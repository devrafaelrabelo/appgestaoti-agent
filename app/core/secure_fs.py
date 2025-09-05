# app/core/secure_fs.py
from pathlib import Path
import platform
import logging


def harden_path(p: Path, include_current_user: bool = True) -> None:
    """
    Ajusta permissões do arquivo/pasta para reduzir risco de exposição.
    - No Windows, a ideia seria aplicar ACLs restritivas (SYSTEM, Administrators e,
      opcionalmente, o usuário atual).
    - No Linux/macOS, poderia aplicar chmod 600/700.

    Atualmente é apenas um stub (no-op), mantido por compatibilidade.
    """
    try:
        # Por enquanto, não faz nada real.
        # Futuro: usar pywin32 / icacls no Windows, chmod no POSIX.
        logging.debug("secure_fs.harden_path noop for %s (platform=%s)", p, platform.system())
    except Exception as e:
        logging.warning("secure_fs.harden_path falhou para %s: %s", p, e)
    return
