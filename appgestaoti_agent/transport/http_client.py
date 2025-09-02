from __future__ import annotations
import httpx

def build_client(
    base_url: str | None = None,
    timeout: float | httpx.Timeout | None = None,
    http2: bool | None = None,
    verify: bool = True,
    **client_kwargs,
) -> httpx.AsyncClient:
    # evitar duplicidade se vier em client_kwargs
    client_kwargs.pop("timeout", None)

    # fallback automático de HTTP/2
    if http2 is None:
        try:
            import h2  # noqa: F401
            http2 = True
        except Exception:
            http2 = False

    if timeout is None:
        timeout = 10.0

    return httpx.AsyncClient(
        base_url=base_url or "",
        timeout=timeout,
        http2=http2,
        verify=verify,
        **client_kwargs,
    )
