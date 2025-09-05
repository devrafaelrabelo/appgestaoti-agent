# ui_tray/main.py
from __future__ import annotations

import threading
import sys
import webbrowser
import logging
from pathlib import Path

import typer
import pystray
from pystray import MenuItem as Item
from PIL import Image

from app.core import logging_conf, config_win, state
from app.workflows import enroll_flow, metrics_flow, inventory_flow


app = typer.Typer(add_completion=False)


def _load_icon() -> Image.Image:
    """
    Carrega ícone do tray (usa app.ico no ProgramData ou fallback).
    """
    try:
        cfg = config_win.load()
        ico_path = Path(cfg.data_dir).parent / "app.ico"
        if ico_path.exists():
            return Image.open(ico_path)
    except Exception:
        pass

    # fallback: quadrado cinza
    return Image.new("RGB", (64, 64), color=(128, 128, 128))


def _do_enroll(icon: pystray.Icon, item: Item) -> None:
    ok, msg = enroll_flow.run()
    logging.info("Tray > Enroll: %s", msg)


def _do_metrics(icon: pystray.Icon, item: Item) -> None:
    ok, msg = metrics_flow.run(batch=1)
    logging.info("Tray > Metrics: %s", msg)


def _do_inventory(icon: pystray.Icon, item: Item) -> None:
    ok, msg = inventory_flow.run()
    logging.info("Tray > Inventory: %s", msg)


def _open_logs(icon: pystray.Icon, item: Item) -> None:
    cfg = config_win.load()
    log_dir = cfg.data_dir.parent / "logs"
    webbrowser.open(str(log_dir))


def _quit(icon: pystray.Icon, item: Item) -> None:
    logging.info("Tray > Encerrando agente tray")
    icon.stop()
    sys.exit(0)


def run_tray() -> None:
    """
    Inicia ícone na bandeja do sistema.
    """
    logging_conf.setup()

    menu = (
        Item("Enroll agora", _do_enroll),
        Item("Enviar Metrics", _do_metrics),
        Item("Enviar Inventory", _do_inventory),
        Item("Abrir pasta de logs", _open_logs),
        Item("Sair", _quit),
    )

    icon = pystray.Icon(
        "appgestaoti-tray",
        _load_icon(),
        "AppGestaoTI Agent",
        menu=menu,
    )

    logging.info("Tray iniciado. Ícone na bandeja do sistema.")

    # roda em thread separada pra não travar
    threading.Thread(target=icon.run, daemon=True).start()


@app.command()
def tray():
    """
    Roda o tray do agente (ícone na bandeja).
    """
    run_tray()
    # mantém processo vivo
    try:
        while True:
            pass
    except KeyboardInterrupt:
        _quit(None, None)


if __name__ == "__main__":
    app()
