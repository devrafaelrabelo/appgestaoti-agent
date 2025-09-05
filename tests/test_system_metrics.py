import pytest
from app.system import metrics_win


def test_collect_metrics_sample_has_expected_keys():
    m = metrics_win.collect_metrics_sample()
    assert "timestamp" in m
    assert "collected_at" in m
    assert "cpu_percent" in m
    assert "memory" in m
    assert "process_count" in m
    assert "uptime_seconds" in m
    assert "disk_root" in m
    assert "sessions" in m

    # memória deve ter campos coerentes
    mem = m["memory"]
    assert "used_bytes" in mem
    assert "total_bytes" in mem
    assert "percent" in mem

    # disco raiz também
    disk = m["disk_root"]
    assert "total_bytes" in disk
    assert "used_bytes" in disk
    assert "percent" in disk

    # sessões
    sess = m["sessions"]
    assert "active_user" in sess
    assert "users" in sess
    assert isinstance(sess["users"], list)


def test_collect_metrics_sample_with_monkeypatched_errors(monkeypatch):
    # força psutil a lançar exceções → deve cair nos fallbacks e ainda retornar dict válido
    monkeypatch.setattr(metrics_win.psutil, "cpu_percent", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(metrics_win.psutil, "virtual_memory", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(metrics_win.psutil, "disk_usage", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(metrics_win.psutil, "pids", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))

    m = metrics_win.collect_metrics_sample()
    # ainda deve conter todas as chaves, mesmo com erros
    for key in ["cpu_percent", "memory", "disk_root", "process_count", "sessions"]:
        assert key in m
