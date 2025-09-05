from app.core import config_win, http


def test_client_builds_headers():
    cfg = config_win.load()
    with http.sync_client(cfg, include_enrollment_token=True) as c:
        headers = {k.lower(): v for k, v in c.headers.items()}
        assert "user-agent" in headers
        assert "x-agent-name" in headers
        assert "x-agent-version" in headers
        assert "x-enrollment-token" in headers


def test_client_without_enrollment_token():
    cfg = config_win.load()
    with http.sync_client(cfg, include_enrollment_token=False) as c:
        headers = {k.lower(): v for k, v in c.headers.items()}
        assert "user-agent" in headers
        assert "x-agent-name" in headers
        assert "x-agent-version" in headers
        assert "x-enrollment-token" not in headers