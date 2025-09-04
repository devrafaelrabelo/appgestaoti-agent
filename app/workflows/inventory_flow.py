import logging
from app.core import config_win, logging_conf, http, state
from app.core.envelope import make_envelope
from app.core.hashutil import sha256_of
from app.system.inventory_win import collect_full_inventory
from app.core.guard_win import is_allowed_by_policy

def run() -> tuple[bool, str]:
    logging_conf.setup()
    log = logging.getLogger(__name__)
    cfg = config_win.load()
    st = state.read_safe(cfg)

    allowed, reason = is_allowed_by_policy(cfg)
    if not allowed:
        return False, f"Envio bloqueado pela política local: {reason}"

    st = state.read_safe(cfg)
    inv = collect_full_inventory()
    inv_hash = sha256_of(inv)

    envelope = make_envelope(cfg, st, kind="inventory", full=True)
    data = {
        "snapshot_version": envelope["sent_at"][:10].replace("-", ""),
        "inventory_hash": inv_hash,
        "prev_inventory_hash": st.last_inventory_hash,
        **inv,
    }

    # Preferimos access_token; se não existir, habilitamos envio do enrollment token
    token = st.access_token or None
    include_enrollment = token is None
    if include_enrollment:
        # alguns backends exigem o token também no body
        data["auth"] = {"enrollment_token": cfg.ENROLLMENT_TOKEN}

    payload = {"envelope": envelope, "data": data}

    client = http.client(cfg, bearer_token=token, include_enrollment_header=include_enrollment)

    # If-None-Match para deduplicar inventory
    headers = {"If-None-Match": inv_hash}
    if include_enrollment:
        # redundante, mas ajuda em backends que validam por header custom
        headers["X-Enrollment-Token"] = cfg.ENROLLMENT_TOKEN

    r = client.post(cfg.INVENTORY_PATH, json=payload, headers=headers)

    # Tratamento explícito
    if r.status_code in (200, 201):
        st.last_inventory_hash = inv_hash
        state.write_safe(cfg, st)
        log.info("Inventory aceito. Hash=%s", inv_hash)
        return True, "Inventory enviado com sucesso."
    if r.status_code in (204, 304):
        st.last_inventory_hash = inv_hash
        state.write_safe(cfg, st)
        log.info("Inventory sem mudanças (ETag/If-None-Match).")
        return True, "Inventory sem mudanças."

    if r.status_code == 401:
        # Mostra motivo do backend para depurar
        return False, f"401 Unauthorized: {r.text}"

    try:
        r.raise_for_status()
    except Exception as e:
        return False, f"Falha ao enviar inventory: {e}"

    return True, "Inventory concluído."
