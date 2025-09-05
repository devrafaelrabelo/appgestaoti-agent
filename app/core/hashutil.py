from __future__ import annotations
import hashlib
import json
from typing import Any


def sha256_of(obj: Any) -> str:
    """
    Calcula o SHA256 de um objeto Python (dict/list/str/etc).
    Usa JSON canônico (chaves ordenadas, sem espaços extras).
    """
    if obj is None:
        return ""
    try:
        if isinstance(obj, (str, bytes)):
            data = obj if isinstance(obj, bytes) else obj.encode("utf-8")
        else:
            data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(data).hexdigest()
    except Exception as e:
        # fallback simples: converte para string e hashea
        return hashlib.sha256(str(obj).encode("utf-8")).hexdigest()
