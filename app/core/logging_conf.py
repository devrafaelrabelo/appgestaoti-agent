# app/core/logging_conf.py
import logging
import logging.handlers
from pathlib import Path

from app.core.config_win import load


class _RedactingFilter(logging.Filter):
    """
    Filtro que remove tokens sensíveis antes de gravar no log.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # tokens comuns
            record.msg = record.msg.replace("Authorization: Bearer", "Authorization: Bearer ***")
            record.msg = record.msg.replace("X-Enrollment-Token", "X-Enrollment-Token: ***")
            record.msg = record.msg.replace("access_token", "access_token=***")
            record.msg = record.msg.replace("enrollment_token", "enrollment_token=***")
        return True


def setup(level: int = logging.INFO) -> None:
    """
    Configura logging global com rotação de arquivo + console.
    - Usa RotatingFileHandler em %ProgramData%/.../logs/agent.log
    - Faz fallback para console-only se não conseguir gravar arquivo
    - Idempotente (não recria handlers se já existir)
    """
    cfg = load()

    # diretório de logs sempre em %ProgramData%
    log_dir: Path = cfg.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent.log"

    root = logging.getLogger()
    if root.handlers:
        # já configurado (idempotente)
        return

    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    # arquivo rotativo
    try:
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        fh.addFilter(_RedactingFilter())
        root.addHandler(fh)
    except Exception as e:
        # se não conseguir gravar, loga só no console
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
        logging.warning("logging_conf: fallback para console-only (%s)", e)

    # console handler (sempre presente, mas não duplica se já tiver)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.addFilter(_RedactingFilter())
    root.addHandler(ch)


def set_level(level: int) -> None:
    """
    Permite mudar nível de log em runtime (ex: DEBUG para diagnóstico).
    """
    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers:
        h.setLevel(level)
