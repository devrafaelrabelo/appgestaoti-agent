import pytest
from app.system import inventory_win


def test_collect_minimal_inventory_returns_expected_keys(monkeypatch):
    inv = inventory_win.collect_minimal_inventory()
    assert "hostname" in inv
    assert "os" in inv
    assert "cpu" in inv
    assert "memory" in inv
    assert "user" in inv
    assert "hardware" in inv
    # deve conter pelo menos essas chaves
    assert "count" in inv["cpu"]
    assert "total_bytes" in inv["memory"]


def test_collect_full_inventory_extends_minimal(monkeypatch):
    inv = inventory_win.collect_full_inventory()
    # herdado do minimal
    assert "hostname" in inv
    # extras
    assert "collected_at" in inv
    assert "network" in inv
    assert "storage" in inv
    assert "cpu" in inv
    assert "memory" in inv


def test_collect_full_inventory_network_has_interfaces(monkeypatch):
    inv = inventory_win.collect_full_inventory()
    net = inv.get("network", {})
    assert "interfaces" in net
    assert isinstance(net["interfaces"], list)


def test_collect_handles_ps_errors(monkeypatch):
    # força _ps a sempre retornar None
    monkeypatch.setattr(inventory_win, "_ps", lambda *a, **k: None)

    inv = inventory_win.collect_full_inventory()
    # mesmo com falha, deve retornar estrutura básica
    assert "os" in inv
    assert "cpu" in inv
    assert "memory" in inv
    assert "network" in inv
    assert "storage" in inv
