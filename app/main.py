# app/main.py
from __future__ import annotations

import sys
from typing import Callable, Tuple

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def _print(msg: str) -> None:
    print(msg, flush=True)


def _safe_int(s: str, default: int = 1) -> int:
    try:
        v = int(s)
        return v if v > 0 else default
    except Exception:
        return default


def _run_step(name: str, fn: Callable[[], Tuple[bool, str]]) -> tuple[bool, str]:
    try:
        ok, msg = fn()
    except Exception as e:
        return False, f"{name} falhou com exceção: {e}"
    return ok, msg


def run_all() -> tuple[bool, str]:
    """
    Pipeline completo:
      - Enroll (se não houver device_id OU access_token)
      - Inventory (sempre)
      - Metrics (sempre, batch=1)
    """
    from app.core import config_win, state
    from app.workflows.enroll_flow import run as run_enroll
    from app.workflows.inventory_flow import run as run_inventory
    from app.workflows.metrics_flow import run as run_metrics

    cfg = config_win.load()
    st = state.read_safe(cfg)

    steps: list[tuple[str, bool, str]] = []

    need_enroll = not getattr(st, "device_id", None) or not getattr(st, "access_token", None)
    if need_enroll:
        ok, msg = _run_step("enroll", run_enroll)
        steps.append(("enroll", ok, msg))
        # recarrega state para etapas seguintes
        st = state.read_safe(cfg)
    else:
        steps.append(("enroll", True, "Pulado: já possui device_id e access_token"))

    ok_i, msg_i = _run_step("inventory", run_inventory)
    steps.append(("inventory", ok_i, msg_i))

    ok_m, msg_m = _run_step("metrics", lambda: run_metrics(batch=1))
    steps.append(("metrics", ok_m, msg_m))

    ok_global = all(s[1] for s in steps)
    resumo = " | ".join(f"{name}:{'OK' if ok else 'FAIL'}" for name, ok, _ in steps)
    detalhes = "\n".join(f"- {name}: {msg}" for name, _, msg in steps)
    return ok_global, f"{resumo}\n{detalhes}"


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv

    # Sem argumentos → faz tudo
    if not argv or argv[0] in {"all", "*"}:
        ok, msg = run_all()
        _print(msg)
        sys.exit(EXIT_OK if ok else EXIT_FAIL)

    # Específicos
    cmd = argv[0].lower()

    if cmd == "enroll":
        from app.workflows.enroll_flow import run as run_enroll
        ok, msg = _run_step("enroll", run_enroll)
        _print(msg)
        sys.exit(EXIT_OK if ok else EXIT_FAIL)

    if cmd in {"inventory", "inv"}:
        from app.workflows.inventory_flow import run as run_inventory
        ok, msg = _run_step("inventory", run_inventory)
        _print(msg)
        sys.exit(EXIT_OK if ok else EXIT_FAIL)

    if cmd in {"metrics", "met"}:
        from app.workflows.metrics_flow import run as run_metrics
        batch = _safe_int(argv[1], 1) if len(argv) > 1 else 1
        ok, msg = _run_step("metrics", lambda: run_metrics(batch=batch))
        _print(msg)
        sys.exit(EXIT_OK if ok else EXIT_FAIL)

    if cmd in {"--help", "-h", "help"}:
        _print(
            "Usage:\n"
            "  python -m app.main                 # faz tudo (enroll* + inventory + metrics)\n"
            "  python -m app.main enroll          # apenas enroll\n"
            "  python -m app.main inventory       # apenas inventory\n"
            "  python -m app.main metrics [N]     # apenas metrics (opcional batch N)\n"
            "\n* Enroll roda no 'faz tudo' se faltar device_id OU access_token."
        )
        sys.exit(EXIT_OK)

    if cmd in {"--version", "-V"}:
        try:
            from app.core.config_win import load as _load
            cfg = _load()
            _print(f"{cfg.AGENT_NAME} {cfg.AGENT_VERSION}")
        except Exception:
            _print("appgestaoti-agent")
        sys.exit(EXIT_OK)

    _print(f"Unknown command: {argv[0]}\nUse --help para ver os comandos.")
    sys.exit(EXIT_USAGE)


if __name__ == "__main__":
    main()
