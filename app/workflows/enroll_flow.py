import logging
from app.core import config_win, logging_conf, state, crypto, http
from app.core.envelope import make_envelope
from app.system.inventory_win import collect_minimal_inventory
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
    keypair = crypto.ensure_keypair(cfg)
    inv_min = collect_minimal_inventory()

    envelope = make_envelope(cfg, st, kind="enroll", full=True)
    data = {
        "keys": {"public": keypair.public_b64, "type": keypair.type},
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
        "enrollment_token": cfg.ENROLLMENT_TOKEN,
    }

    payload = {"envelope": envelope, "data": data}

    client = http.client(cfg, include_enrollment_header=True)
    r = client.post(cfg.ENROLL_PATH, json=payload)
    r.raise_for_status()
    resp = r.json()

    st = state.from_backend_response(resp, existing=st)
    state.write_safe(cfg, st)
    log.info("Enroll OK: device_id=%s", st.device_id)
    return True, f"Enroll concluído. device_id={st.device_id}"
