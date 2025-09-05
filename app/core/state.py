# app/core/state.py
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from app.core.secure_fs import harden_path


class AgentState(BaseModel):
    device_id: Optional[str] = None
    access_token: Optional[str] = None
    registered_at: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    seq: Dict[str, int] = Field(default_factory=dict)
    last_inventory_hash: Optional[str] = None

    def next_seq(self, kind: str) -> int:
        self.seq[kind] = int(self.seq.get(kind, 0)) + 1
        return self.seq[kind]


# ---------- helpers de caminho / compatibilidade ----------

def _resolve_state_path(cfg) -> Path:
    """
    Compatível com o Cfg novo (cfg.state_file) e com o legado (cfg.DATA_DIR/state.json).
    """
    # Preferência: novo atributo
    p = getattr(cfg, "state_file", None)
    if isinstance(p, Path):
        return p

    # Compat: DATA_DIR legado
    data_dir = getattr(cfg, "data_dir", None) or getattr(cfg, "DATA_DIR", None)
    if data_dir is None:
        # fallback absoluto seguro em ProgramData
        base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "RabeloTech" / "AppGestaoTI" / "agent"
        base.mkdir(parents=True, exist_ok=True)
        return base / "state.json"

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "state.json"


def _legacy_path(cfg) -> Path:
    """
    Caminho antigo (%ProgramData%.../agent/state.json) caso precise migrar.
    """
    data_dir = getattr(cfg, "DATA_DIR", None)
    if data_dir:
        return Path(data_dir) / "state.json"
    # Se não houver DATA_DIR legado, retorna o atual para no-op.
    return _resolve_state_path(cfg)


# ---------- API pública ----------

def path(cfg) -> Path:
    """Retorna o caminho do arquivo de estado atual."""
    return _resolve_state_path(cfg)


def exists(cfg) -> bool:
    return path(cfg).exists()


def read_safe(cfg) -> AgentState:
    """
    Lê o state de forma resiliente:
    - tenta o caminho atual;
    - se inválido/corrompido, tenta o .bak;
    - se falhar, retorna AgentState() vazio.
    """
    p = path(cfg)
    bak = p.with_suffix(".json.bak")

    # 1) state.json
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return AgentState(**data) if isinstance(data, dict) else AgentState()
    except (OSError, json.JSONDecodeError, ValidationError):
        pass

    # 2) state.json.bak
    try:
        if bak.exists():
            data = json.loads(bak.read_text(encoding="utf-8"))
            return AgentState(**data) if isinstance(data, dict) else AgentState()
    except (OSError, json.JSONDecodeError, ValidationError):
        pass

    return AgentState()


def write_safe(cfg, st: AgentState) -> None:
    """
    Escrita atômica com backup:
    - serializa para temp file;
    - move state.json atual para .bak;
    - replace atômico do temp -> state.json;
    - aplica endurecimento de ACLs (best-effort).
    """
    p = path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_name = tempfile.mkstemp(prefix="state_", suffix=".json", dir=str(p.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(_to_json(st))

        # backup do estado anterior
        if p.exists():
            try:
                shutil.copy2(p, p.with_suffix(".json.bak"))
            except OSError:
                # backup é best-effort; segue mesmo se falhar
                pass

        # replace atômico
        os.replace(tmp_name, p)

        # harden ACLs (best-effort)
        try:
            harden_path(p)
        except Exception:
            pass
    finally:
        # se sobrou tmp, remove
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except OSError:
            pass


def from_backend_response(data: dict, existing: AgentState | None = None) -> AgentState:
    st = existing or AgentState()
    st.device_id = data.get("device_id", st.device_id)
    st.access_token = data.get("access_token", st.access_token)
    st.registered_at = data.get("registered_at", st.registered_at)
    if isinstance(data.get("policy"), dict):
        st.policy = data["policy"]
    return st


# ---------- utilidades ----------

def migrate_legacy_if_needed(cfg) -> None:
    """
    Se o state existir no caminho legado e não existir no caminho novo, migra (move).
    """
    old = _legacy_path(cfg)
    new = path(cfg)
    if old == new:
        return
    try:
        if old.exists() and not new.exists():
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
    except OSError:
        # migração é best-effort; se falhar, segue com o estado novo vazio
        pass


def _to_json(model: AgentState) -> str:
    # Compatível com Pydantic v2 (model_dump) e v1 (json())
    if hasattr(model, "model_dump"):
        data = model.model_dump(mode="json")
        return json.dumps(data, ensure_ascii=False, indent=2)
    return model.json(ensure_ascii=False, indent=2)
