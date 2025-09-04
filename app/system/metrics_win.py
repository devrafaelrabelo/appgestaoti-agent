# app/system/metrics_win.py
import psutil, time, os, getpass

def collect_metrics_sample() -> dict:
    boot = psutil.boot_time()
    now = time.time()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(os.getenv("SystemDrive", "C:\\"))
    # psutil.cpu_percent com interval pequeno para sample “real”
    cpu_p = psutil.cpu_percent(interval=0.5)

    domain = os.environ.get("USERDOMAIN") or ""
    user = getpass.getuser()
    active_user = f"{domain}\\{user}" if domain else user

    return {
        "timestamp": int(now),
        "cpu_percent": float(cpu_p),
        "memory": {
            "used_bytes": int(mem.used),
            "total_bytes": int(mem.total),
            "percent": float(mem.percent),
        },
        "process_count": len(psutil.pids()),
        "uptime_seconds": int(now - boot),
        "disk_root": {
            "total_bytes": int(disk.total),
            "used_bytes": int(disk.used),
            "percent": float(disk.percent),
        },
        "sessions": {
            "active_user": active_user,
            "users": [active_user],
        },
    }
