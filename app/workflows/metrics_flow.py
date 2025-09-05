# app/workflows/metrics_flow.py
from __future__ import annotations

import logging
import time
from typing import Tuple

from app.core import config_win, logging_conf, http, state
from app.core.envelope import make_envelope
from app.workflows.enroll_flow import run as run_enroll
from app.system.metrics_win import collect_metrics_sample


def _ensure_token(cfg) -> str | None:
    st = state.read_safe(cfg)
    if getattr(st, "access_token", None):
        return st.access_token
    ok, _ = run_enroll()
    st = state.read_safe(cfg)
    return st.access_token if ok and getattr(st, "access_token", None) else None


def run(batch: int = 1) -> Tuple[bool, str]:
    """
    Envia 'batch' amostras de métricas.
    Se não houver token, tenta fazer enroll automaticamente.
    """
    logging_conf.setup()
    log = logging.getLogger("agent.metrics")
    cfg = config_win.load()

    token = _ensure_token(cfg)
    if not token:
        return False, "Sem access_token após tentativa de enroll."

    st = state.read_safe(cfg)

    t0 = time.time()
    samples = [collect_metrics_sample() for _ in range(max(1, int(batch)))]
    t1 = time.time()

    envelope = make_envelope(cfg, st, kind="metrics", full=False)
    payload = {"envelope": envelope, "data": {"samples": samples}}

    headers = {"Authorization": f"Bearer {token}"}
    full_url = f"{cfg.norm_base_url}{cfg.metrics_path}"
    log.info("POST %s (%d sample[s])", full_url, len(samples))

    try:
        with http.sync_client(cfg, include_enrollment_token=False, access_token=token) as client:
            r = client.post(cfg.metrics_path, json=payload, headers=headers)
    except Exception as e:
        log.warning("Erro de conexão ao enviar metrics: %s", e)
        return False, f"Erro de conexão ao enviar metrics: {e}"

    log.info("Resposta metrics: HTTP %s (coleta %.2fs)", r.status_code, t1 - t0)

    if r.status_code in (200, 201, 202):
        log.info("Metrics enviado: %d amostra(s).", len(samples))
        return True, f"Metrics enviado: {len(samples)} amostra(s)."

    if r.status_code == 401:
        return False, f"401 Unauthorized: {r.text}"

    try:
        r.raise_for_status()
    except Exception as e:
        return False, f"Falha ao enviar metrics: {e}"

    return True, "Metrics concluído."
