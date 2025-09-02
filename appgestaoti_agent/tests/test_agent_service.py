import pytest, respx
from httpx import Response
from appgestaoti_agent.config import Config
from appgestaoti_agent.services.agent_service import AgentService
import appgestaoti_agent.services.scheduler as scheduler_mod
import appgestaoti_agent.transport.enrollment as enrollment_mod

@pytest.mark.asyncio
@respx.mock
async def test_agent_service_start_once(tmp_config_path, monkeypatch):
    # mocks HTTP usados no scheduler
    respx.post("http://127.0.0.1:8000/api/agent/metrics").mock(
        return_value=Response(200, json={"status": "ok"})
    )
    respx.post("http://127.0.0.1:8000/api/agent/inventory").mock(
        return_value=Response(200, json={"status": "ok"})
    )

    # mock do enrollment -> devolve device_id
    async def fake_enroll(base_url, path, token, client, cfg):
        return {"device_id": "DEV-TEST"}
    monkeypatch.setattr(enrollment_mod, "enroll", fake_enroll)

    # rodar apenas 1 iteração no scheduler
    async def fake_run_scheduler(cfg, client, device_store, device, stop_event, iterations=None):
        assert device["device_id"] == "DEV-TEST"
        return
    monkeypatch.setattr(scheduler_mod, "run_scheduler", fake_run_scheduler)

    cfg = Config.from_file(tmp_config_path)
    svc = AgentService(cfg)
    await svc.start(iterations=1)
