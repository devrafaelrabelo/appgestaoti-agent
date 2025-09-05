# app/system/metrics_win.py
from __future__ import annotations

import getpass
import logging
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import psutil

log = logging.getLogger("agent.metrics")


def collect_metrics_sample() -> Dict[str, Any]:
    """
    Coleta uma amostra de métricas do sistema (Windows):
      - CPU (%)
      - Memória (usado/total/%)
      - Disco raiz (SystemDrive)
      - Contagem de processos
      - Uptime
      - Sessões de usuário ativas
    """
    now = time.time()
    ts_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Boot time / uptime
    uptime_seconds = 0
    try:
        boot = psutil.boot_time()
        uptime_seconds = int(now - boot)
    except Exception as e:
        log.debug("Falha ao coletar uptime: %s", e)

    # CPU
    cpu_percent = 0.0
    try:
        cpu_percent = psutil.cpu_percent(interval=0.3)
    except Exception as e:
        log.debug("Falha ao coletar CPU: %s", e)

    # Memória
    mem_used = mem_total = 0
    mem_percent = 0.0
    try:
        mem = psutil.virtual_memory()
        mem_used, mem_total, mem_percent = mem.used, mem.total, mem.percent
    except Exception as e:
        log.debug("Falha ao coletar memória: %s", e)

    # Disco raiz
    disk_total = disk_used = 0
    disk_percent = 0.0
    try:
        root = os.getenv("SystemDrive", "C:") + "\\"
        disk = psutil.disk_usage(root)
        disk_total, disk_used, disk_percent = disk.total, disk.used, disk.percent
    except Exception as e:
        log.debug("Falha ao coletar disco: %s", e)

    # Sessões de usuário
    active_user = "unknown"
    users: List[str] = []
    try:
        # usuário atual
        domain = os.environ.get("USERDOMAIN") or ""
        user = getpass.getuser()
        active_user = f"{domain}\\{user}" if domain else user

        # todos os usuários logados
        users = sorted({u.name for u in psutil.users() if getattr(u, "name", None)})
        if active_user not in users:
            users.append(active_user)
    except Exception as e:
        log.debug("Falha ao coletar sessões de usuário: %s", e)
        users = [active_user]

    # Process count
    process_count = 0
    try:
        process_count = len(psutil.pids())
    except Exception as e:
        log.debug("Falha ao coletar contagem de processos: %s", e)

    return {
        "timestamp": int(now),
        "collected_at": ts_iso,
        "cpu_percent": float(cpu_percent),
        "memory": {
            "used_bytes": int(mem_used),
            "total_bytes": int(mem_total),
            "percent": float(mem_percent),
        },
        "process_count": int(process_count),
        "uptime_seconds": int(uptime_seconds),
        "disk_root": {
            "total_bytes": int(disk_total),
            "used_bytes": int(disk_used),
            "percent": float(disk_percent),
        },
        "sessions": {
            "active_user": active_user,
            "users": users,
            "hostname": socket.gethostname(),
        },
    }
