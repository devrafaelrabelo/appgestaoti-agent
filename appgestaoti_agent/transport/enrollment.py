from __future__ import annotations
import logging
from httpx import AsyncClient

log = logging.getLogger(__name__)

async def enroll(base_url: str, path: str, token: str, client: AsyncClient, cfg) -> dict:
    url = f"{base_url}{path}"
    payload = {"enrollment_token": token}
    log.info("Enviando enrollment para %s", url)
    r = await client.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    if "device_id" not in data:
        data["device_id"] = data.get("id", "DEV-LOCAL")
    return data
