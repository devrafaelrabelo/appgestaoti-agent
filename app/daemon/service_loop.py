# app/daemon/service_loop.py
from __future__ import annotations

import logging
import random
import time
from typing import Optional

from app.core import config_win, logging_conf, state
from app.workflows.enroll_flow import run as do_enroll
from app.workflows.inventory_flow import run as do_inventory
from app.workflows.metrics_flow import run as do_metrics


def _sleep(sec: float) -> None:
    try:
        time.sleep(max(0.0, sec))
    except KeyboardInterrupt:
        raise


def _now() -> float:
    return time.monotonic()


def _apply_policy(st, cfg) -> tuple[int, int]:
    """
    Calcula intervalos de metrics/inventory considerando defaults de cfg
    e overrides de policy vinda do backend.
    """
    m = getattr(cfg, "metrics_interval", 60)
    i = getattr(cfg, "inventory_interval", 86400)

    if getattr(st, "policy", None):
        try:
            m = int(st.policy.get("metrics_interval_sec") or m)
        except Exception:
            pass
        try:
            i = int(st.policy.get("inventory_interval_sec") or i)
        except Exception:
            pass

    return max(5, m), max(60, i)


def _jittered_delay(base_sec: int, pct: float = 0.1) -> float:
    j = base_sec * pct
    return base_sec + random.uniform(-j, j)


def _ensure_enrolled(log: logging.Logger, cfg, stop_after: Optional[int]) -> bool:
    """
    Pré-voo: garante que temos device_id e access_token antes de iniciar o loop.
    Retenta com backoff exponencial até sucesso ou timeout.
    """
    t_start = _now()
    backoff = 5.0
    max_backoff = 300.0

    while True:
        st = state.read_safe(cfg)
        if getattr(st, "device_id", None) and getattr(st, "access_token", None):
            log.info("Pré-voo: agente já está registrado (device_id=%s).", st.device_id)
            return True

        ok, msg = do_enroll()
        if ok:
            st = state.read_safe(cfg)
            log.info("Pré-voo: enroll OK (device_id=%s).", getattr(st, "device_id", None))
            return True

        log.warning("Pré-voo: enroll falhou: %s. Retentando em %.0fs", msg, backoff)
        _sleep(backoff)
        backoff = min(backoff * 2.0, max_backoff)
        if stop_after is not None and (_now() - t_start) >= float(stop_after):
            log.error("Pré-voo: timeout aguardando enroll.")
            return False


def run_forever(stop_after: Optional[int] = None) -> int:
    """
    Loop principal do agente:
      - Pré-voo exige device_id + access_token (faz enroll se necessário).
      - Executa metrics (default 60s) e inventory (default 86400s) com jitter.
      - Se perder token/state, tenta re-enroll com backoff.
    """
    logging_conf.setup()
    log = logging.getLogger("agent.service")
    cfg = config_win.load()
    random.seed()

    if not _ensure_enrolled(log, cfg, stop_after):
        return 1

    st = state.read_safe(cfg)
    METRICS_EVERY, INVENTORY_EVERY = _apply_policy(st, cfg)
    log.info("Agente em loop. metrics=%ss inventory=%ss", METRICS_EVERY, INVENTORY_EVERY)

    now = _now()
    next_metrics = now + _jittered_delay(METRICS_EVERY, 0.05)
    next_inventory = now + _jittered_delay(INVENTORY_EVERY, 0.05)

    re_backoff = 5.0
    re_backoff_max = 300.0
    t0 = _now()

    while True:
        now = _now()

        # Re-enroll se perdermos credenciais
        st = state.read_safe(cfg)
        if not (getattr(st, "device_id", None) and getattr(st, "access_token", None)):
            ok, msg = do_enroll()
            if ok:
                log.info("Re-enroll OK: %s", msg)
                re_backoff = 5.0
                st = state.read_safe(cfg)
                METRICS_EVERY, INVENTORY_EVERY = _apply_policy(st, cfg)
                next_metrics = now + _jittered_delay(METRICS_EVERY, 0.05)
                next_inventory = now + _jittered_delay(INVENTORY_EVERY, 0.05)
            else:
                log.warning("Re-enroll falhou: %s. Nova tentativa em %.0fs", msg, re_backoff)
                _sleep(re_backoff)
                re_backoff = min(re_backoff * 2.0, re_backoff_max)
                if stop_after is not None and (_now() - t0) >= float(stop_after):
                    log.info("Encerrando por stop_after=%s", stop_after)
                    return 0
                continue

        # Metrics
        if now >= next_metrics:
            ok_m, msg_m = do_metrics(batch=1)
            log.info("Metrics %s: %s", "OK" if ok_m else "erro", msg_m)
            next_metrics = _now() + _jittered_delay(METRICS_EVERY, 0.1)

        # Inventory
        if now >= next_inventory:
            ok_i, msg_i = do_inventory()
            log.info("Inventory %s: %s", "OK" if ok_i else "erro", msg_i)
            next_inventory = _now() + _jittered_delay(INVENTORY_EVERY, 0.1)

        # Espera até o próximo evento
        sleep_for = min(next_metrics, next_inventory) - _now()
        _sleep(min(max(sleep_for, 0.5), 10.0))

        if stop_after is not None and (_now() - t0) >= float(stop_after):
            log.info("Encerrando por stop_after=%s", stop_after)
            return 0
