from app.core import config_win, state
from app.workflows import enroll_flow


def test_enroll_flow_against_local(monkeypatch):
    # garante que vamos bater no teu endpoint real
    monkeypatch.setenv("APP_BASE_URL", "http://127.0.0.1:8000")

    cfg = config_win.load()
    st = state.read_safe(cfg)

    ok, msg = enroll_flow.run()
    assert ok, f"Enroll falhou: {msg}"

    st2 = state.read_safe(cfg)
    assert st2.device_id is not None
    assert st2.access_token is not None
