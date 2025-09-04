# app/core/crypto.py
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from app.core.config_win import load as load_cfg
from app.core.secure_fs import harden_path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass
class Keypair:
    private_path: Path
    public_path: Path
    public_b64: str
    type: str = "ed25519"


def _read_public_b64(pub_path: Path) -> str:
    """Lê a chave pública do disco (PEM ou RAW) e retorna em base64 (raw)."""
    public_bytes = pub_path.read_bytes()
    try:
        pubkey = serialization.load_pem_public_key(public_bytes)
        raw = pubkey.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    except ValueError:
        raw = public_bytes  # pode já estar em formato RAW
    return base64.b64encode(raw).decode("ascii")


def ensure_keypair(cfg=None) -> Keypair:
    # Local padrão das chaves:
    # %PROGRAMDATA%\RabeloTech\AppGestaoTI\agent\keys\id_ed25519 (.pub)
    cfg = cfg or load_cfg()
    key_dir = cfg.DATA_DIR / "keys"
    prv = key_dir / "id_ed25519"
    pub = key_dir / "id_ed25519.pub"

    key_dir.mkdir(parents=True, exist_ok=True)
    try:
        harden_path(key_dir, include_current_user=True)
    except Exception:
        pass

    # Tenta reforçar ACLs mesmo se a leitura de atributos estiver negada
    try:
        prv_exists = prv.exists()
        pub_exists = pub.exists()
    except PermissionError:
        # Tenta “abrir” ACL dos arquivos diretamente
        try:
            harden_path(prv, include_current_user=True)
            harden_path(pub, include_current_user=True)
        except Exception:
            pass
        # Reavalia
        prv_exists = prv.exists() if prv.parent.exists() else False
        pub_exists = pub.exists() if pub.parent.exists() else False

    if prv_exists and pub_exists:
        try:
            harden_path(prv, include_current_user=True)
            harden_path(pub, include_current_user=True)
        except Exception:
            pass
        return Keypair(prv, pub, _read_public_b64(pub), "ed25519")

    # Gerar novas chaves
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    prv.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    try:
        harden_path(prv, include_current_user=True)
        harden_path(pub, include_current_user=True)
    except Exception:
        pass

    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_b64 = base64.b64encode(raw).decode("ascii")
    return Keypair(prv, pub, public_b64, "ed25519")
