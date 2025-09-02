from __future__ import annotations
import asyncio, logging
from appgestaoti_agent.storage.device_store import DeviceStore
from appgestaoti_agent.transport.http_client import build_client
from appgestaoti_agent.transport.enrollment import enroll
from appgestaoti_agent.services.scheduler import run_scheduler

log = logging.getLogger(__name__)

class AgentService:
    def __init__(self, cfg):
        self.cfg = cfg
        self.stop_event = asyncio.Event()

    async def start(self, *, iterations: int | None = None):
        device_store = DeviceStore(self.cfg.data_path)
        async with build_client(timeout=float(self.cfg.timeout_seconds), http2=self.cfg.http2, base_url=None) as client:
            device = device_store.read()
            if not device:
                log.info("Realizando enrollment")
                device = await enroll(self.cfg.norm_base_url, self.cfg.enroll_path, self.cfg.enrollment_token, client, self.cfg)
                device_store.write(device)
                log.info("Enrollment concluído: %s", device.get("device_id"))
            await run_scheduler(self.cfg, client, device_store, device, self.stop_event, iterations=iterations)

    def stop(self):
        self.stop_event.set()
