# app/daemon/preflight.py
from __future__ import annotations

import logging
import os
from pathlib import Path

# Raiz em %ProgramData%\RabeloTech\AppGestaoTI
BASE = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "RabeloTech" / "AppGestaoTI"

CONFIG_DIR = BASE / "config"
DATA_DIR = BASE / "data"
LOG_DIR = BASE / "logs"
QUEUE_DIR = DATA_DIR / "queue"


def ensure_environment() -> None:
    """
    Cria a árvore de diretórios necessária para rodar o agente.

    Estrutura:
      %ProgramData%\RabeloTech\AppGestaoTI\
        ├─ config\      → arquivos de configuração local (state.json, agent.json, etc.)
        ├─ data\        → dados temporários, fila offline
        │   └─ queue\
        └─ logs\        → arquivos de log do agente

    Se qualquer diretório não puder ser criado, levanta exceção (OSError).
    """
    for d in (CONFIG_DIR, DATA_DIR, LOG_DIR, QUEUE_DIR):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error("Falha ao criar diretório %s: %s", d, e)
            raise
        else:
            logging.debug("Diretório OK: %s", d)
