# app/core/envelope.py
from datetime import datetime, timezone
import uuid

def make_envelope(cfg, state, kind: str, *, full: bool, seq: int | None = None) -> dict:
    """
    Envelope padronizado para todos os envios.
    """
    if hasattr(state, "next_seq"):
        seq = state.next_seq(kind) if seq is None else seq
    else:
        seq = 1 if seq is None else seq

    return {
        "schema_version": getattr(cfg, "SCHEMA_VERSION", "1.0"),
        "message_id": str(uuid.uuid4()),
        "sent_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "device_id": getattr(state, "device_id", None),
        "agent": {"name": cfg.AGENT_NAME, "version": cfg.AGENT_VERSION},
        "collect": {"kind": kind, "full": bool(full), "seq": int(seq)},
    }
