from pydantic import BaseModel
from pathlib import Path
import os, shutil

class Cfg(BaseModel):
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    ENROLL_PATH: str = os.getenv("ENROLL_PATH", "/api/agent/enroll")
    METRICS_PATH: str = os.getenv("METRICS_PATH", "/api/agent/metrics")
    INVENTORY_PATH: str = os.getenv("INVENTORY_PATH", "/api/agent/inventory")
    ENROLLMENT_TOKEN: str = os.getenv("ENROLLMENT_TOKEN", "TESTE_LOCAL")

    SCHEMA_VERSION: str = os.getenv("SCHEMA_VERSION", "1.0")
    AGENT_NAME: str = os.getenv("AGENT_NAME", "appgestaoti-agent")
    AGENT_VERSION: str = os.getenv("AGENT_VERSION", "0.1.0")

    DATA_DIR: Path = Path(os.getenv("DATA_DIR", r"%PROGRAMDATA%\RabeloTech\AppGestaoTI\agent"))

    DEV_MODE: bool = os.getenv("DEV_MODE", "1") == "1"
    ENFORCE_HTTPS: bool = os.getenv("ENFORCE_HTTPS", "0") == "1"
    REQUIRE_DOMAIN: bool = os.getenv("REQUIRE_DOMAIN", "0") == "1"
    ALLOWED_DOMAINS: str = os.getenv("ALLOWED_DOMAINS", "")
    ALLOWED_BACKEND_HOSTS: str = os.getenv("ALLOWED_BACKEND_HOSTS", "")

    TIMEOUT_SEC: int = int(os.getenv("TIMEOUT_SEC", "15"))
    KEY_TYPE: str = os.getenv("KEY_TYPE", "ed25519")

def _expand_programdata(p: Path) -> Path:
    s = str(p)
    if s.startswith("%PROGRAMDATA%"):
        base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return Path(s.replace("%PROGRAMDATA%", base))
    return p

def _ensure_dirs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "keys").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)

def _is_writable_dir(dirpath: Path) -> bool:
    try:
        dirpath.mkdir(parents=True, exist_ok=True)
        test = dirpath / ".writetest"
        test.write_text("x", encoding="utf-8")
        test.unlink(missing_ok=True)
        return True
    except Exception:
        return False

def _migrate_old_dirs(target: Path) -> None:
    base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    candidates = [
        Path(base) / "AppGestaoTI" / "agent",
        Path(base) / "AppGestaoTI" / "agent_win",
        Path(base) / "AppGestaoTI-agent",
    ]
    for old in candidates:
        if old.exists() and old.resolve() != target.resolve():
            src_state = old / "state.json"
            if src_state.exists() and not (target / "state.json").exists():
                shutil.move(str(src_state), str(target / "state.json"))
            for name in ("keys", "logs"):
                src = old / name
                dst = target / name
                if src.exists() and not dst.exists():
                    shutil.move(str(src), str(dst))

def resolve_data_dir(p: Path) -> Path:
    # 1) Tenta ProgramData
    pd = _expand_programdata(p)
    if _is_writable_dir(pd):
        _ensure_dirs(pd)
        _migrate_old_dirs(pd)
        return pd
    # 2) Fallback: LOCALAPPDATA (user)
    lad = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "RabeloTech" / "AppGestaoTI" / "agent"
    _ensure_dirs(lad)
    return lad

def load() -> Cfg:
    cfg = Cfg()
    cfg.DATA_DIR = resolve_data_dir(cfg.DATA_DIR)
    return cfg
