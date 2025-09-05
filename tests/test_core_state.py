import json
import pytest
from app.core import state
from app.core.config_win import Cfg


@pytest.fixture
def cfg(tmp_path):
    """Config fake usando tmp_path para isolar state.json."""
    return Cfg(
        BASE_URL="http://localhost:8000",
        METRICS_PATH="/api/metrics",
        ENROLL_PATH="/api/enroll",
        INVENTORY_PATH="/api/inventory",
        DATA_DIR=tmp_path,
        ENROLLMENT_TOKEN="TEST_TOKEN",
    )


def test_state_write_and_read(cfg):
    st1 = state.AgentState(device_id="dev123", access_token="tok123")
    state.write_safe(cfg, st1)

    assert state.exists(cfg)
    st2 = state.read_safe(cfg)

    assert st2.device_id == "dev123"
    assert st2.access_token == "tok123"


def test_state_handles_invalid_json(cfg):
    # cria um state.json inválido
    p = state.path(cfg)
    p.write_text("{invalid json}", encoding="utf-8")

    st = state.read_safe(cfg)
    assert isinstance(st, state.AgentState)
    # fallback → device_id vazio
    assert st.device_id is None


def test_next_seq_increments(cfg):
    st = state.AgentState()
    assert st.next_seq("metrics") == 1
    assert st.next_seq("metrics") == 2
    assert st.seq["metrics"] == 2


def test_from_backend_response_updates_existing(cfg):
    st = state.AgentState(device_id="old", access_token="oldtok")

    resp = {
        "device_id": "newid",
        "access_token": "newtok",
        "registered_at": "2025-01-01T00:00:00Z",
        "policy": {"metrics_interval_sec": 10},
    }

    st2 = state.from_backend_response(resp, existing=st)
    assert st2.device_id == "newid"
    assert st2.access_token == "newtok"
    assert st2.registered_at == "2025-01-01T00:00:00Z"
    assert isinstance(st2.policy, dict)
