# app/core/http.py
from __future__ import annotations

import httpx
from typing import Optional


def _make_headers(
    cfg,
    include_enrollment_token: bool = True,
    access_token: Optional[str] = None,
) -> dict[str, str]:
    """
    Monta os headers padrão para chamadas ao backend.

    - Sempre inclui User-Agent + X-Agent-Name/Version
    - Pode incluir X-Enrollment-Token (fase de inscrição)
    - Pode incluir Authorization: Bearer (quando já registrado)
    """
    headers = {
        "User-Agent": f"{cfg.agent_name}/{cfg.agent_version}",
        "X-Agent-Name": cfg.agent_name,
        "X-Agent-Version": cfg.agent_version,
    }
    if include_enrollment_token and getattr(cfg, "enrollment_token", None):
        headers["X-Enrollment-Token"] = cfg.enrollment_token
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def sync_client(
    cfg,
    *,
    include_enrollment_token: bool = True,
    access_token: Optional[str] = None,
) -> httpx.Client:
    """
    Cria um cliente httpx síncrono com base_url e headers configurados.
    """
    base_url = (cfg.norm_base_url or "").rstrip("/")
    if not base_url:
        raise ValueError("Configuração inválida: base_url vazio")

    return httpx.Client(
        base_url=base_url,
        timeout=cfg.timeout_sec,
        headers=_make_headers(cfg, include_enrollment_token, access_token),
        transport=httpx.HTTPTransport(retries=3),
        follow_redirects=True,
    )


def async_client(
    cfg,
    *,
    include_enrollment_token: bool = True,
    access_token: Optional[str] = None,
) -> httpx.AsyncClient:
    """
    Cria um cliente httpx assíncrono (usado no service_loop).
    """
    base_url = (cfg.norm_base_url or "").rstrip("/")
    if not base_url:
        raise ValueError("Configuração inválida: base_url vazio")

    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=cfg.timeout_sec,
        headers=_make_headers(cfg, include_enrollment_token, access_token),
        transport=httpx.AsyncHTTPTransport(retries=3, limits=limits),
        follow_redirects=True,
    )
