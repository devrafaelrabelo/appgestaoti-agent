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

        log.war
