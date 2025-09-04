# app/core/hashutil.py
import hashlib, json

def canonical_dumps(obj) -> str:
    """
    JSON canônico: chaves ordenadas, sem espaços extras.
    Útil p/ hash/ETag.
    """
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def sha256_of(obj) -> str:
    data = canonical_dumps(obj).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
