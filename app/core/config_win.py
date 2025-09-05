# app/core/config_win.py
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Cfg:
    base_url: str
    metrics_path: str
    enroll_path: str
    inventory_path: str
    data_dir: Path
    enrollment_token: str

    agent_name: str = "appgestaoti-agent"
    agent_version: str = "0.1.0"
    timeout_sec: int = 30
    schema_version: str = "1.0"

    metrics_interval: int = 60       # padrão: 1 min
    inventory_interval: int = 86400  # padrão: 24h

    @property
    def norm_base_url(self) -> str:
        return self.base_url.rstrip("/")

    @property
    def state_file(self) -> Path:
        """Arquivo de state (device_id, access_token)."""
        return self.data_dir / "state.json"

    @property
    def queue_dir(self) -> Path:
        """Fila offline para métricas/inventário."""
        d = self.data_dir / "queue"
        d.mkdir(parents=True, exist_ok=True)
        return d


def _default_data_dir() -> Path:
    """
    Resolve sempre para ProgramData (independente de x86/x64).
    Em Windows 64-bit, {pf32} é usado para app, mas os dados ficam em %ProgramData%.
    """
    programdata = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    base = programdata / "RabeloTech" / "AppGestaoTI" / "agent"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _load_local_override(cfg: Cfg) -> Cfg:
    """
    Permite sobrescrever configurações em agent.json
    (útil para debug, override de intervalos etc.)
    """
    cfg_file = cfg.data_dir / "agent.json"
    if cfg_file.exists():
        try:
            overrides = json.loads(cfg_file.read_text(encoding="utf-8"))
            for k, v in overrides.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
        except Exception as e:
            # não quebra se o JSON estiver ruim
            import logging
            logging.warning("falha ao carregar override %s: %s", cfg_file, e)
    return cfg


def load() -> Cfg:
    base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000")

    cfg = Cfg(
        base_url=base_url,
        metrics_path=os.environ.get("APP_METRICS_PATH", "/api/telemetry/metrics"),
        enroll_path=os.environ.get("APP_ENROLL_PATH", "/api/telemetry/enroll"),
        inventory_path=os.environ.get("APP_INVENTORY_PATH", "/api/telemetry/inventory"),
        data_dir=_default_data_dir(),
        enrollment_token=os.environ.get("APP_ENROLLMENT_TOKEN", "TESTE_LOCAL"),
        metrics_interval=int(os.environ.get("APP_METRICS_INTERVAL", "60")),
        inventory_interval=int(os.environ.get("APP_INVENTORY_INTERVAL", "86400")),
    )
    return _load_local_override(cfg)
