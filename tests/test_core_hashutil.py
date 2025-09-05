import hashlib
from app.core import hashutil


def test_sha256_of_string():
    s = "hello"
    expected = hashlib.sha256(s.encode("utf-8")).hexdigest()
    assert hashutil.sha256_of(s) == expected


def test_sha256_of_bytes():
    b = b"hello"
    expected = hashlib.sha256(b).hexdigest()
    assert hashutil.sha256_of(b) == expected


def test_sha256_of_dict_is_deterministic():
    obj1 = {"b": 2, "a": 1}
    obj2 = {"a": 1, "b": 2}  # ordem diferente
    h1 = hashutil.sha256_of(obj1)
    h2 = hashutil.sha256_of(obj2)
    assert h1 == h2, "Hashes de dicts equivalentes devem ser iguais"


def test_sha256_of_list_is_deterministic():
    obj1 = [1, 2, 3]
    obj2 = [1, 2, 3]
    assert hashutil.sha256_of(obj1) == hashutil.sha256_of(obj2)


def test_sha256_of_none_returns_empty_string():
    assert hashutil.sha256_of(None) == ""


def test_sha256_of_unserializable_object(monkeypatch):
    class Bad:
        def __str__(self): return "bad"

    # força json.dumps a falhar
    monkeypatch.setattr("json.dumps", lambda *a, **k: (_ for _ in ()).throw(TypeError("fail")))
    result = hashutil.sha256_of(Bad())
    assert isinstance(result, str)
    assert len(result) == 64  # tamanho do hash sha256 em hex
