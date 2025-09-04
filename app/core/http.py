# app/core/http.py
import httpx

def client(cfg, bearer_token: str | None = None, include_enrollment_header: bool = True):
    """
    Cria um httpx.Client com headers padrão.
    - Usa access_token (se passado), senão ENROLLMENT_TOKEN.
    - include_enrollment_header=False evita enviar X-Enrollment-Token (ex.: inventory/metrics).
    """
    transport = httpx.HTTPTransport(retries=3)
    token = bearer_token or cfg.ENROLLMENT_TOKEN

    headers = {
        "User-Agent": f"{cfg.AGENT_NAME}/{cfg.AGENT_VERSION}",
        "Authorization": f"Bearer {token}",
        "X-Agent-Name": cfg.AGENT_NAME,
        "X-Agent-Version": cfg.AGENT_VERSION,
    }
    if include_enrollment_header:
        headers["X-Enrollment-Token"] = cfg.ENROLLMENT_TOKEN

    return httpx.Client(
        base_url=cfg.Backend_URL if hasattr(cfg, "Backend_URL") else cfg.BACKEND_URL,  # tolera digitação diferente
        timeout=cfg.TIMEOUT_SEC,
        headers=headers,
        transport=transport,
        follow_redirects=True,
    )
