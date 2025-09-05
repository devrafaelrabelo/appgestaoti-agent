import pytest
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# --- servidor fake ---
app = FastAPI()

@app.post("/api/telemetry/enroll")
async def enroll(request: Request):
    body = await request.json()
    return {
        "device_id": "test-device-123",
        "access_token": "token-xyz",
        "registered_at": "2025-01-01T00:00:00Z",
        "policy": {"metrics_interval_sec": 30, "inventory_interval_sec": 3600},
    }

@app.post("/api/telemetry/inventory")
async def inventory(request: Request):
    body = await request.json()
    if body.get("data", {}).get("inventory_hash") == "duplicate":
        return JSONResponse(status_code=304, content={})
    return {"status": "ok"}

@app.post("/api/telemetry/metrics")
async def metrics(request: Request):
    body = await request.json()
    return {"received": len(body.get("data", {}).get("samples", []))}

# --- pytest fixture ---
@pytest.fixture(scope="session", autouse=True)
def test_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    yield "http://127.0.0.1:8000"
    server.should_exit = True
    thread.join()
