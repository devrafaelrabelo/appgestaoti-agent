import pytest, respx
from httpx import Response
from appgestaoti_agent.transport.http_client import build_client

@pytest.mark.asyncio
@respx.mock
async def test_build_client_get_ok():
    respx.get("http://testserver/ping").mock(return_value=Response(200, json={"ok": True}))
    async with build_client(base_url="http://testserver", timeout=3.0) as client:
        r = await client.get("/ping")
        assert r.status_code == 200
        assert r.json()["ok"] is True
