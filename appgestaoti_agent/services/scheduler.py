from __future__ import annotations
import asyncio, logging, time
from httpx import AsyncClient

log = logging.getLogger(__name__)

async def _send_metrics(cfg, client: AsyncClient, device: dict) -> None:
    url = f"{cfg.norm_base_url}{cfg.metrics_path}"
    payload = {
        "device_id": device["device_id"],
        "timestamp": int(time.time()),
        "cpu_percent": 5.0,
        "process_count": 123,
        "uptime_seconds": 4567,
    }
    r = await client.post(url, json=payload)
    r.raise_for_status()
    log.info("Metrics enviado: %s", r.status_code)

async def _send_inventory(cfg, client: AsyncClient, device: dict) -> None:
    url = f"{cfg.norm_base_url}{cfg.inventory_path}"
    payload = {"device_id": device["device_id"], "payload": {"os": "Windows", "ram_gb": 16}}
    r = await client.post(url, json=payload)
    r.raise_for_status()
    log.info("Inventory enviado: %s", r.status_code)

async def run_scheduler(cfg, client: AsyncClient, device_store, device: dict, stop_event: asyncio.Event, *, iterations: int | None = None):
    count = 0
    while not stop_event.is_set():
        await _send_metrics(cfg, client, device)
        await _send_inventory(cfg, client, device)
        count += 1
        if iterations is not None and count >= iterations:
            break
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=cfg.interval_seconds)
        except asyncio.TimeoutError:
            pass
