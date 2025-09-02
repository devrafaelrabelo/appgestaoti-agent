import os, tempfile, textwrap, pytest
from pathlib import Path

@pytest.fixture
def tmp_config_path():
    """Gera config.toml temporário válido."""
    data = textwrap.dedent("""
        base_url = "http://127.0.0.1:8000"
        enroll_path = "/api/agent/enroll"
        metrics_path = "/api/agent/metrics"
        inventory_path = "/api/agent/inventory"
        enrollment_token = "TESTE_LOCAL"
        interval_seconds = 5
        timeout_seconds = 5
        log_level = "INFO"
        data_dir = "C:\\\\Temp\\\\appgestaoti_data"
        send_inventory_on_start = true
    """).strip()
    fd, path = tempfile.mkstemp(prefix="config_", suffix=".toml")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    yield Path(path)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
