from app.core import config_win, state
from app.workflows import metrics_flow


def test_metrics_flow_against_local(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "http://127.0.0.1:8000")

    cfg = config_win.load()
    st = state.AgentState(device_id="local-test", access_token="local-token")
    state.write_safe(cfg, st)

    ok, msg = metrics_flow.run(batch=2)
    assert ok, f"Metrics falhou: {msg}"
    assert "2 amostra" in msg
