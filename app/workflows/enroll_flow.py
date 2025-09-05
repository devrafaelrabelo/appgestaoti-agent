# app/workflows/enroll_flow.py
from __future__ import annotations

import logging
from typing import Tuple

from app.core import config_win, logging_conf, state, http
from app.core.envelope import make_envelope
from app.system.inventory_win import collect_minimal_inventory
from app.core.guard_win import is_allowed_by_policy


def run() -> Tuple[bool, str]:
    """
    Fluxo de enroll:
      - monta envelope + fingerprint mínima
      - envia POST para backend com enrollment_token
      - persiste device_id e access_token retornados
    """
    logging_conf.setup()
    log = logging.getLogger("agent.enroll")
    cfg = config_win.load()
    st = state.read_safe(cfg)

    allowed, reason = is_allowed_by_policy(cfg)
    if not allowed:
        log.warning("Enroll bloqueado pela política local: %s", reason)
        return False, f"Envio bloqueado pela política local: {reason}"

    inv_min = collect_minimal_inventory()
    envelope = make_envelope(cfg, st, kind="enroll", full=True)
    data = {
        "fingerprint": {
            "hostname": inv_min.get("hostname"),
            "hardware_uuid": inv_min.get("hardware", {}).get("uuid"),
            "bios_serial": inv_min.get("hardware", {}).get("serial"),
        },
        "device_min": {
            "os": inv_min.get("os"),
            "cpu_count": inv_min.get("cpu", {}).get("count"),
            "memory_total_bytes": inv_min.get("memory", {}).get("total_bytes"),
        },
        "enrollment_token": cfg.enrollment_token,
    }
    payload = {"envelope": envelope, "data": data}

    full_url = f"{cfg.norm_base_url}{cfg.enroll_path}"
    log.info("POST %s", full_url)

    try:
        with http.sync_client(cfg, include_enrollment_token=True) as client:
            r = client.post(cfg.enroll_path, json=payload)
    except Exception as e:
        log.warning("Erro de conexão no enroll: %s", e)
        return False, f"Erro de conexão no enroll: {e}"

    log.info("Resposta enroll: HTTP %s", r.status_code)

    if r.status_code in (200, 201, 202):
        try:
            resp = r.json() if r.content else {}
        except Exception:
            resp = {}
        st = state.from_backend_response(resp, existing=st)
        state.write_safe(cfg, st)
        log.info("Enroll OK: device_id=%s", st.device_id)
        return True, f"Enroll concluído. device_id={st.device_id}"

    if r.status_code == 401:
        return False, f"401 Unauthorized durante enroll: {r.text}"

    try:
        r.raise_for_status()
    except Exception as e:
        return False, f"Falha no enroll: {e}"

    # fallback: sucesso inesperado mas com body
    try:
        resp = r.json() if r.content else {}
    except Exception:
        resp = {}
    st = state.from_backend_response(resp, existing=st)
    state.write_safe(cfg, st)
    return True, "Enroll concluído."
