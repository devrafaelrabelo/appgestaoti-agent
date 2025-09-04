# app/core/guard_win.py
import os, subprocess
from urllib.parse import urlparse

def _ps(cmd: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out or None
    except Exception:
        return None

def current_domain() -> str | None:
    return os.environ.get("USERDOMAIN") or _ps("(Get-CimInstance Win32_ComputerSystem).Domain")

def is_domain_joined() -> bool:
    val = _ps("(Get-CimInstance Win32_ComputerSystem).PartOfDomain")
    if val is None:
        return False
    return str(val).strip().lower() in ("true", "1")

def host_from_url(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""

def is_allowed_by_policy(cfg) -> tuple[bool, str]:
    """
    Verifica (1) HTTPS se exigido, (2) domínio permitido (se exigido), (3) host em allowlist (se configurado).
    Retorna (allowed, motivo_ou_vazio).
    """
    # HTTPS
    if cfg.ENFORCE_HTTPS and not str(cfg.BACKEND_URL).lower().startswith("https://"):
        return False, "Política exige HTTPS e a URL atual não é HTTPS."

    # Domínio
    if cfg.REQUIRE_DOMAIN:
        if not is_domain_joined():
            return False, "Máquina não é membro de domínio e a política exige domínio."
        allowed = [d.strip().upper() for d in cfg.ALLOWED_DOMAINS.split(";") if d.strip()]
        if allowed:
            dom = (current_domain() or "").upper()
            if dom not in allowed:
                return False, f"Domínio '{dom}' não está na allowlist."

    # Host allowlist
    hosts = [h.strip().lower() for h in cfg.ALLOWED_BACKEND_HOSTS.split(";") if h.strip()]
    if hosts:
        host = (host_from_url(cfg.BACKEND_URL) or "").lower()
        if host not in hosts:
            return False, f"Host '{host}' não está na allowlist."

    return True, ""
