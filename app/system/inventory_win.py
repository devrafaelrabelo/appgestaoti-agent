# app/system/inventory_win.py
from __future__ import annotations

import logging
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil

log = logging.getLogger("agent.inventory")


# -----------------------------
# PowerShell helpers (Windows)
# -----------------------------
def _ps(cmd: str, timeout: float = 5.0) -> Optional[str]:
    """
    Executa um comando PowerShell e retorna stdout (strip) ou None em erro/timeout.
    """
    if not _is_windows():
        return None
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
        return (out or "").strip() or None
    except Exception as e:
        log.debug("PowerShell comando falhou (%s): %s", cmd, e)
        return None


def _is_windows() -> bool:
    return platform.system().lower().startswith("win")


# -----------------------------
# FAST getters (env/psutil)
# -----------------------------
def _domain() -> Optional[str]:
    return os.environ.get("USERDOMAIN") or _ps("(Get-CimInstance Win32_ComputerSystem).Domain")


def _uuid() -> Optional[str]:
    return _ps("(Get-CimInstance Win32_ComputerSystemProduct).UUID")


def _serial() -> Optional[str]:
    return _ps("(Get-CimInstance Win32_BIOS).SerialNumber")


def _cpu_name() -> Optional[str]:
    return platform.processor() or _ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")


def _os_build() -> Optional[str]:
    return _ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').CurrentBuildNumber")


def _product_name() -> Optional[str]:
    return _ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').ProductName")


# -----------------------------
# Inventory collectors
# -----------------------------
def collect_minimal_inventory() -> Dict[str, Any]:
    """
    Coleta rápida: hostname, OS básico, CPU logical count, memória total,
    usuário+domínio, uuid/serial quando disponíveis.
    """
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = platform.node() or "unknown"

    return {
        "hostname": hostname,
        "os": {
            "name": platform.system() or "Windows",
            "version": platform.version() or "",
            "release": platform.release() or "",
            "arch": platform.machine() or "",
        },
        "cpu": {"count": psutil.cpu_count(logical=True) or 0},
        "memory": {"total_bytes": int(psutil.virtual_memory().total or 0)},
        "user": {
            "primary": os.environ.get("USERNAME") or "",
            "domain": _domain(),
        },
        "hardware": {"uuid": _uuid(), "serial": _serial()},
    }


def collect_full_inventory() -> Dict[str, Any]:
    """
    Coleta completa com detalhes de OS, CPU, memória, discos e rede.
    Sempre retorna um dict coerente, mesmo com falhas parciais.
    """
    inv = collect_minimal_inventory()

    # OS extras
    inv["os"].update({"build": _os_build(), "product": _product_name()})

    # CPU extras
    inv["cpu"]["name"] = _cpu_name()
    inv["cpu"]["physical_cores"] = psutil.cpu_count(logical=False)

    # Memória extras
    try:
        mem = psutil.virtual_memory()
        inv["memory"].update(
            {
                "available_bytes": int(mem.available),
                "percent": float(mem.percent),
            }
        )
    except Exception as e:
        log.debug("Falha ao coletar memória: %s", e)

    # Discos
    disks: List[Dict[str, Any]] = []
    try:
        for part in psutil.disk_partitions(all=False):
            if ("cdrom" in (part.opts or "").lower()) or not part.fstype:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except Exception as e:
                log.debug("Falha ao coletar disco %s: %s", part.device, e)
                continue
            disks.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_bytes": int(usage.total or 0),
                    "used_bytes": int(usage.used or 0),
                    "free_bytes": int(usage.free or 0),
                    "percent": float(usage.percent or 0.0),
                }
            )
    except Exception as e:
        log.debug("Falha em disk_partitions: %s", e)
    inv["storage"] = {"disks": sorted(disks, key=lambda d: d.get("mountpoint") or "")}

    # Rede
    interfaces: List[Dict[str, Any]] = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        AF_LINK = getattr(psutil, "AF_LINK", None)
        for name, addr_list in addrs.items():
            mac = None
            ipv4: List[str] = []
            ipv6: List[str] = []
            for a in addr_list:
                fam, addr = getattr(a, "family", None), getattr(a, "address", None)
                if not addr:
                    continue
                if AF_LINK is not None and fam == AF_LINK:
                    mac = addr
                elif fam == socket.AF_INET:
                    ipv4.append(addr)
                elif fam == socket.AF_INET6:
                    ipv6.append(addr.split("%", 1)[0])
            st = stats.get(name)
            interfaces.append(
                {
                    "name": name,
                    "mac": mac,
                    "ipv4": ipv4,
                    "ipv6": ipv6,
                    "is_up": bool(st.isup) if st else None,
                    "mtu": int(st.mtu) if st and st.mtu else None,
                    "speed_mbps": int(st.speed) if st and st.speed else None,
                }
            )
    except Exception as e:
        log.debug("Falha ao coletar rede: %s", e)

    interfaces.sort(key=lambda x: (x.get("name") or "").lower())
    inv["network"] = {
        "hostname": inv.get("hostname"),
        "domain": inv.get("user", {}).get("domain"),
        "interfaces": interfaces,
    }

    inv["collected_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return inv
