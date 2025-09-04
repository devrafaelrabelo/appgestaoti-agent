import platform, psutil, getpass, socket, os, subprocess
from datetime import datetime

def _ps(cmd: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out or None
    except Exception:
        return None

def _uuid() -> str | None:
    return _ps("(Get-CimInstance Win32_ComputerSystemProduct).UUID")

def _serial() -> str | None:
    return _ps("(Get-CimInstance Win32_BIOS).SerialNumber")

def _domain() -> str | None:
    return os.environ.get("USERDOMAIN") or _ps("(Get-CimInstance Win32_ComputerSystem).Domain")

def _cpu_name() -> str | None:
    return _ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")

def _os_build() -> str | None:
    return _ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').CurrentBuildNumber")

def _product_name() -> str | None:
    return _ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').ProductName")

def collect_minimal_inventory() -> dict:
    return {
        "hostname": socket.gethostname(),
        "os": {
            "name": "Windows",
            "version": platform.version(),
            "release": platform.release(),
            "arch": platform.machine(),
        },
        "cpu": {"count": psutil.cpu_count(logical=True)},
        "memory": {"total_bytes": psutil.virtual_memory().total},
        "user": {"primary": getpass.getuser(), "domain": _domain()},
        "hardware": {"uuid": _uuid(), "serial": _serial()},
    }

def collect_full_inventory() -> dict:
    inv = collect_minimal_inventory()
    inv["os"]["build"] = _os_build()
    inv["os"]["product"] = _product_name()
    inv["cpu"]["name"] = _cpu_name()
    inv["cpu"]["physical_cores"] = psutil.cpu_count(logical=False)

    mem = psutil.virtual_memory()
    inv["memory"].update({
        "available_bytes": mem.available,
        "percent": mem.percent,
    })

    disks = []
    for part in psutil.disk_partitions(all=False):
        if ("cdrom" in (part.opts or "").lower()) or not part.fstype:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "percent": usage.percent,
        })
    inv["storage"] = {"disks": disks}

    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    AF_LINK = getattr(psutil, "AF_LINK", None)
    interfaces = []
    for name, addr_list in addrs.items():
        mac = None; ipv4 = []; ipv6 = []
        for a in addr_list:
            fam = getattr(a, "family", None)
            try:
                import socket as _s
                if AF_LINK is not None and fam == AF_LINK:
                    mac = a.address
                elif fam == _s.AF_INET:
                    ipv4.append(a.address)
                elif fam == _s.AF_INET6:
                    ipv6.append(a.address.split("%")[0])
            except Exception:
                pass
        st = stats.get(name)
        interfaces.append({
            "name": name,
            "mac": mac,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "is_up": bool(st.isup) if st else None,
            "mtu": st.mtu if st else None,
            "speed_mbps": st.speed if st else None,
        })
    inv["network"] = {
        "hostname": inv.get("hostname"),
        "domain": inv["user"].get("domain"),
        "interfaces": interfaces,
    }

    inv["collected_at"] = datetime.utcnow().isoformat() + "Z"
    return inv
