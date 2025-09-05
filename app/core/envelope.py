from __future__ import annotations
import time
import uuid

def make_envelope(cfg, st, kind: str, full: bool = False) -> dict:
    """
    Cria o envelope padrão para cada payload enviado ao backend.
    Inclui informações do agente, versão, device_id e timestamps.
    """
    return {
        "id": str(uuid.uuid4()),
        "kind": kind,
        "agent": {
            "name": cfg.agent_name,
            "version": cfg.agent_version,
            "schema_version": cfg.SCHEMA_VERSION,
        },
        "device": {
            "id": getattr(st, "device_id", None),
        },
        "seq": st.next_seq(kind) if hasattr(st, "next_seq") else 0,
        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "full": bool(full),
    }
