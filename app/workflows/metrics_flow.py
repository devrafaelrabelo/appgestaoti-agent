# app/workflows/metrics_flow.py
import logging
from app.core import config_win, logging_conf, http, state
from app.core.envelope import make_envelope
from app.system.metrics_win import collect_metrics_sample

def run(batch: int = 1) -> tuple[bool, str]:
    """
    Envia 'batch' amostras (por padrão 1). Faz fallback para enrollment token
    (header + body) se não houver access_token no state.
    """
    logging_conf.setup()
    log = logging.getLogger(__name__)
    cfg = config_win.load()
    st = state.read_safe(cfg)

    samples = [collect_metrics_sample() for _ in range(max(1, int(batch)))]

    envelope = make_envelope(cfg, st, kind="metrics", full=False)
    data = {"samples": samples}

    # Preferimos access_token; se não existir, habilitamos envio do enrollment token
    token = st.access_token or None
    include_enrollment = token is None
    if include_enrollment:
        # alguns backends de teste aceitam o token também no corpo
        data["auth"] = {"enrollment_token": cfg.ENROLLMENT_TOKEN}

    payload = {"envelope": envelope, "data": data}

    client = http.client(cfg, bearer_token=token, include_enrollment_header=include_enrollment)

    headers = {}
    if include_enrollment:
        # redundante, mas ajuda em backends que validam por header custom
        headers["X-Enrollment-Token"] = cfg.ENROLLMENT_TOKEN

    r = client.post(cfg.METRICS_PATH, json=payload, headers=headers)

    # Tratamento explícito (sem levantar exceção)
    if r.status_code in (200, 201, 202):
        log.info("Metrics enviado: %d amostra(s).", len(samples))
        return True, f"Metrics enviado: {len(samples)} amostra(s)."

    if r.status_code == 401:
        return False, f"401 Unauthorized: {r.text}"

    try:
        r.raise_for_status()
    except Exception as e:
        return False, f"Falha ao enviar metrics: {e}"

    return True, "Metrics concluído."
