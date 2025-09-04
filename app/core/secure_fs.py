# app/core/secure_fs.py
import subprocess, os
from pathlib import Path

def _current_account() -> str:
    dom = os.environ.get("USERDOMAIN") or os.environ.get("COMPUTERNAME") or ""
    usr = os.environ.get("USERNAME") or ""
    return f"{dom}\\{usr}" if dom and usr else (usr or "Users")

def harden_path(p: Path, include_current_user: bool = True):
    """
    Endurece ACL no Windows. Por padrão, além de Administrators e SYSTEM,
    também inclui o usuário atual (útil em DEV/execução não-elevada).
    """
    try:
        if not p.exists():
            return

        # remove herança
        subprocess.run(["icacls", str(p), "/inheritance:r"], capture_output=True, text=True)

        grants = ["Administrators:(F)", "SYSTEM:(F)"]
        if include_current_user:
            grants.append(f"{_current_account()}:(F)")

        # aplica no alvo
        subprocess.run(["icacls", str(p), "/grant:r", *grants], capture_output=True, text=True)

        # se diretório, aplica também nos filhos
        if p.is_dir():
            # usar shell=True para expandir wildcard no Windows
            subprocess.run(f'icacls "{p}\\*" /inheritance:r', capture_output=True, text=True, shell=True)
            subprocess.run(f'icacls "{p}\\*" /grant:r ' + " ".join(grants), capture_output=True, text=True, shell=True)
    except Exception:
        # não quebra o fluxo se icacls falhar
        pass
