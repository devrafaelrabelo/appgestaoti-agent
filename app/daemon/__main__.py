# app/daemon/__main__.py
import logging
import sys

from app.daemon.preflight import ensure_environment
from app.daemon.service_loop import run_service
from app.core import logging_conf
from app.core import guard_win


def main() -> None:
    # Configura logging global
    logging_conf.setup(logging.INFO)

    # Garante ambiente em %ProgramData%
    ensure_environment()

    # Evita múltiplas instâncias
    if not guard_win.ensure_single_instance("appgestaoti-agent-service"):
        logging.error("Encerrando: já existe outra instância do serviço em execução.")
        sys.exit(1)

    logging.info("=== AppGestaoTI Agent Service iniciado ===")

    try:
        run_service()  # entra no loop (metrics/inventory + fila + enroll)
    except KeyboardInterrupt:
        logging.info("Serviço interrompido manualmente (CTRL+C / stop).")
    except Exception:
        logging.exception("Erro fatal no serviço")
        sys.exit(1)
    finally:
        logging.info("=== AppGestaoTI Agent Service finalizado ===")


if __name__ == "__main__":
    main()
