from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Cfg:
    BASE_URL: str
    METRICS_PATH: str
    ENROLL_PATH: str
    INVENTORY_PATH: str
    DATA_DIR: Path
    ENROLLMENT_TOKEN: str
    AGENT_NAME: str = "appgestaoti-agent"
    AGENT_VERSION: str = "0.1.0"
    TIMEOUT_SEC: int = 30
    SCHEMA_VERSION: str = "1.0"

    @property
    def timeout_sec(self) -> int:
        """Alias para compatibilidade com cfg.timeout_sec"""
        return self.TIMEOUT_SEC

    @property
    def data_dir(self) -> Path:
        """Alias para compatibilidade com cfg.data_dir"""
        return self.DATA_DIR

    @property
    def norm_base_url(self) -> str:
        return self.BASE_URL.rstrip("/")

    @property
    def metrics_path(self) -> str: return self.METRICS_PATH
    @property
    def enroll_path(self) -> str: return self.ENROLL_PATH
    @property
    def inventory_path(self) -> str: return self.INVENTORY_PATH
    @property
    def enrollment_token(self) -> str: return self.ENROLLMENT_TOKEN
    @property
    def agent_name(self) -> str: return self.AGENT_NAME
    @property
    def agent_version(self) -> str: return self.AGENT_VERSION

def load() -> Cfg:
    programdata = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    data_dir = programdata / "RabeloTech" / "AppGestaoTI" / "agent"
    data_dir.mkdir(parents=True, exist_ok=True)
    base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000")
    return Cfg(
        BASE_URL=base_url,
        METRICS_PATH=os.environ.get("APP_METRICS_PATH", "/api/telemetry/metrics"),
        ENROLL_PATH=os.environ.get("APP_ENROLL_PATH", "/api/telemetry/enroll"),
        INVENTORY_PATH=os.environ.get("APP_INVENTORY_PATH", "/api/telemetry/inventory"),
        DATA_DIR=data_dir,
        ENROLLMENT_TOKEN=os.environ.get("APP_ENROLLMENT_TOKEN", "TESTE_LOCAL"),
    )
