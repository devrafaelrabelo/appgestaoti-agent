from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import tomllib  # Python 3.11+

@dataclass
class Config:
    base_url: str
    enroll_path: str = "/api/agent/enroll"
    metrics_path: str = "/api/agent/metrics"
    inventory_path: str = "/api/agent/inventory"
    enrollment_token: str = ""
    interval_seconds: int = 30
    timeout_seconds: float = 10.0
    http2: bool | None = None
    data_path: str = str(Path.home() / ".appgestaoti")

    @property
    def norm_base_url(self) -> str:
        return self.base_url.rstrip("/")

    @staticmethod
    def from_file(path: str | Path) -> "Config":
        d = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        return Config(
            base_url=d["base_url"],
            enroll_path=d.get("enroll_path", "/api/agent/enroll"),
            metrics_path=d.get("metrics_path", "/api/agent/metrics"),
            inventory_path=d.get("inventory_path", "/api/agent/inventory"),
            enrollment_token=d.get("enrollment_token", ""),
            interval_seconds=int(d.get("interval_seconds", 30)),
            timeout_seconds=float(d.get("timeout_seconds", 10.0)),
            http2=d.get("http2", None),
            data_path=d.get("data_dir") or d.get("data_path") or str(Path.home() / ".appgestaoti"),
        )
