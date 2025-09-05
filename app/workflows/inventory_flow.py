# app/workflows/inventory_flow.py
from __future__ import annotations

import logging
import time
from typing import Tuple

from app.core import config_win, logging_conf, http, state
from app.core.envelope import make_envelope
from app.core.hashutil import sha256_of
from app.system.inventory_win import collect_full_inventory
from app.workflows.enroll_flow import run as run_enroll
from app.core.guard_win import is_allowed_by_policy


def _ensure_token(cfg) -> str | None:
    st = state.read_safe(cfg)
    if getattr(st, "access_token", None):
        return st.access_token
    ok, _ = run_enroll()
    st = state.read_safe(cfg)
    return st.access_token if ok and getattr(st, "access_token", None) else None


def run() -> Tuple[bool, str]:
    """
    Envia inventário completo:
      - Garante access_token (faz enroll se necessário).
      - Calcula hash do inventário e deduplica via If-None-Match.
      - Atualiza state.last_inventory_hash quando aceito.
    """
    logging_conf.setup()
    log = logging.getLogger("agent.inventory")
    cfg = config_win.load()

    allowed, reason = is_allowed_by_policy(cfg)
    if not allowed:
        log.warning("Inventory bloqueado pela política local: %s", reason)
        return False, f"Envio bloqueado pela política local: {reason}"

    token = _ensure_token(cfg)
    if not token:
        return False, "Sem access_token após tentativa de enroll."

    st = state.read_safe(cfg)

    t0 = time.time()
    inv = collect_full_inventory()
    inv_hash = sha256_of(inv)
    t1 = time.time()

    envelope = make_envelope(cfg, st, kind="inventory", full=True)
    data = {
        "snapshot_version": envelope["sent_at"][:10].replace("-", ""),
        "inventory_hash": inv_hash,
        "prev_inventory_hash": st.last_inventory_hash,
        **inv,
    }
    payload = {"envelope": envelope, "data": data}

    headers = {
        "If-None-Match": inv_hash,
        "Authorization": f"Bearer {token}",
    }

    full_url = f"{cfg.norm_base_url}{cfg.inventory_path}"
    log.info("POST %s (hash=%s)", full_url, inv_hash)

    try:
        with http.sync_client(cfg, include_enrollment_token=False, access_token=token) as client:
            r = client.post(cfg.inventory_path, json=payload, headers=headers)
    except Exception as e:
        log.warning("Erro de conexão ao enviar inventory: %s", e)
        return False, f"Erro de conexão ao enviar inventory: {e}"

    log.info("Resposta inventory: HTTP %s (coleta %.2fs)", r.status_code, t1 - t0)

    if r.status_code in (200, 201):
        st.last_inventory_hash = inv_hash
        state.write_safe(cfg, st)
        log.info("Inventory aceito. Hash=%s", inv_hash)
        return True, "Inventory enviado com sucesso."

    if r.status_code in (204, 304):
        st.last_inventory_hash = inv_hash
        state.write_safe(cfg, st)
        log.info("Inventory sem mudanças (If-None-Match).")
        return True, "Inventory sem mudanças."

    if r.status_code == 401:
        return False, f"401 Unauthorized: {r.text}"

    try:
        r.raise_for_status()
    except Exception as e:
        return False, f"Falha ao enviar inventory: {e}"

    return True, "Inventory concluído."
