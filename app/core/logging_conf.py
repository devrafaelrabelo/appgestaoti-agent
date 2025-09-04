import logging, logging.handlers
from pathlib import Path
from app.core.config_win import load

class _RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # remove tokens do texto se por acaso alguém logar
        if isinstance(record.msg, str):
            record.msg = (record.msg
                          .replace("Authorization: Bearer", "Authorization: Bearer ***")
                          .replace("X-Enrollment-Token", "X-Enrollment-Token: ***"))
        return True

def setup():
    cfg = load()
    log_dir: Path = cfg.DATA_DIR / "logs"
    log_file = log_dir / "agent.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
        )
        ch = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        fh.setFormatter(fmt); ch.setFormatter(fmt)
        fh.addFilter(_RedactingFilter()); ch.addFilter(_RedactingFilter())
        logger.addHandler(fh); logger.addHandler(ch)
