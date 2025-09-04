from pydantic import BaseModel, Field
from pathlib import Path
from typing import Any, Dict, Optional
import json
from app.core.secure_fs import harden_path

class AgentState(BaseModel):
    device_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    registered_at: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    seq: Dict[str, int] = Field(default_factory=dict)  # contador por kind: enroll/inventory/metrics
    last_inventory_hash: Optional[str] = None

    def next_seq(self, kind: str) -> int:
        self.seq[kind] = int(self.seq.get(kind, 0)) + 1
        return self.seq[kind]

def path(cfg) -> Path:
    return cfg.DATA_DIR / "state.json"

def exists(cfg) -> bool:
    return path(cfg).exists()

def read_safe(cfg) -> AgentState:
    p = path(cfg)
    if not p.exists():
        return AgentState()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return AgentState(**data)
    except Exception:
        pass
    return AgentState()

def _to_json(model: AgentState) -> str:
    # Pydantic v2
    if hasattr(model, "model_dump"):
        data = model.model_dump(mode="json")
        return json.dumps(data, ensure_ascii=False, indent=2)
    # v1 fallback
    return model.json(ensure_ascii=False, indent=2)

def write_safe(cfg, st: AgentState) -> None:
    p = path(cfg)
    p.write_text(_to_json(st), encoding="utf-8")
    try:
        harden_path(p)
    except Exception:
        pass


def from_backend_response(data: dict, existing: AgentState | None = None) -> AgentState:
    st = existing or AgentState()
    st.device_id = data.get("device_id", st.device_id)
    st.access_token = data.get("access_token", st.access_token)
    st.refresh_token = data.get("refresh_token", st.refresh_token)
    st.registered_at = data.get("registered_at", st.registered_at)
    if "policy" in data and isinstance(data["policy"], dict):
        st.policy = data["policy"]
    return st
