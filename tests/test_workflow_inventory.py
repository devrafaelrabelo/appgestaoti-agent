from app.core import config_win, state
from app.workflows import inventory_flow


def test_inventory_flow_against_local(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "http://127.0.0.1:8000")

    cfg = config_win.load()
    # garante token no state antes de enviar
    st = state.AgentState(device_id="local-test", access_token="TESTE_LOCAL")
    state.write_safe(cfg, st)

    ok, msg = inventory_flow.run()
    assert ok, f"Inventory falhou: {msg}"
