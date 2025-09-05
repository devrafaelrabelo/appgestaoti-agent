# app/core/guard_win.py
from __future__ import annotations

import ctypes
import logging
import os
import sys
from pathlib import Path


def is_windows() -> bool:
    return os.name == "nt"


def ensure_single_instance(lock_name: str = "appgestaoti-agent") -> bool:
    """
    Garante que só exista uma instância desse processo.
    Retorna True se conseguiu criar o lock, False se já existia outro.
    No Windows usa CreateMutex; em outros sistemas usa um arquivo lock no tempdir.
    """
    if is_windows():
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, lock_name)
        last_err = kernel32.GetLastError()
        if last_err == 183:  # ERROR_ALREADY_EXISTS
            logging.error("Outra instância já está em execução (mutex=%s)", lock_name)
            return False
        return True
    else:
        import tempfile

        lock_file = Path(tempfile.gettempdir()) / f"{lock_name}.lock"
        try:
            if lock_file.exists():
                logging.error("Outra instância já está em execução (lockfile=%s)", lock_file)
                return False
            lock_file.write_text(str(os.getpid()))
            return True
        except Exception as e:
            logging.warning("Falha ao criar lockfile %s: %s", lock_file, e)
            return True  # não bloqueia, apenas loga


def require_admin() -> bool:
    """
    Verifica se o processo está rodando como administrador (elevado).
    No Windows usa IsUserAnAdmin. Em POSIX verifica UID=0.
    """
    try:
        if is_windows():
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def restart_as_admin() -> None:
    """
    Reinicia o processo atual como administrador (Windows).
    Só chama se não tiver privilégios; bloqueante.
    """
    if not is_windows():
        return

    if require_admin():
        return

    try:
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        sys.exit(0)
    except Exception as e:
        logging.error("Não conseguiu reiniciar como admin: %s", e)
        sys.exit(1)
