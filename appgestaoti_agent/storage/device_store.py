from __future__ import annotations
from pathlib import Path
import json

class DeviceStore:
    def __init__(self, data_path: str):
        self.base = Path(data_path)
        self.base.mkdir(parents=True, exist_ok=True)
        self.file = self.base / "device.json"

    def read(self) -> dict | None:
        if not self.file.exists():
            return None
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def write(self, device: dict) -> None:
        self.file.write_text(json.dumps(device, ensure_ascii=False, indent=2), encoding="utf-8")
