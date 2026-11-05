"""Encrypted vault: key handling, HKDF key derivation, AES-256-GCM files, keyed fingerprints."""
from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import secrets
import stat
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from anon3pass.types import DocMap, MapEntry, Occurrence

FORMAT_VERSION = 1
KIND_DOCMAP = "docmap"
KIND_REGISTRY = "registry"
INFO_ENC = b"anon3pass/v1/aes-256-gcm-encryption-key"
INFO_HMAC = b"anon3pass/v1/hmac-sha256-surrogate-key"


class VaultError(Exception):
    """A vault file is corrupt, tampered with, or of an unknown version."""


class KeyFileError(VaultError):
    """The master key file is missing, malformed or has unsafe permissions."""


def write_atomic(path: str | os.PathLike, data: bytes, mode: int = 0o600) -> None:
    """Write via a temp file in the same directory, then os.replace."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_key(path: str | os.PathLike) -> bytes:
    """Read an existing master key; refuse group/other permissions."""
    path = Path(path).expanduser()
    if not path.exists():
        raise KeyFileError("key file not found; run `anon init-key`")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise KeyFileError("key file has group or other permissions; run chmod 600 on it")
    key = path.read_bytes()
    if len(key) != 32:
        raise KeyFileError("key file is not 32 bytes")
    return key


def load_or_create_key(path: str | os.PathLike) -> bytes:
    path = Path(path).expanduser()
    if path.exists():
        return load_key(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    key = secrets.token_bytes(32)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key)
    os.chmod(path, 0o600)
    return key


def derive_keys(master: bytes) -> tuple[bytes, bytes]:
    """Return (encryption key, HMAC key), derived with distinct HKDF info labels."""
    def one(info: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)
    return one(INFO_ENC), one(INFO_HMAC)


def fingerprint(hmac_key: bytes, value: str) -> str:
    """Keyed fingerprint, safe to print."""
    return hmac.new(hmac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def _aad(kind: str, version: int) -> bytes:
    return f"{kind}:{version}".encode()


def _seal(kind: str, payload: dict, enc_key: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    plain = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ct = AESGCM(enc_key).encrypt(nonce, plain, _aad(kind, FORMAT_VERSION))
    return bytes([FORMAT_VERSION]) + nonce + ct


def _open(kind: str, blob: bytes, enc_key: bytes) -> dict:
    if len(blob) < 1 + 12 + 16:
        raise VaultError(f"{kind} file is truncated")
    version = blob[0]
    if version != FORMAT_VERSION:
        raise VaultError(f"{kind} file has unsupported version {version}")
    try:
        plain = AESGCM(enc_key).decrypt(blob[1:13], blob[13:], _aad(kind, version))
    except InvalidTag as exc:
        raise VaultError(f"{kind} file failed authentication: tampered, corrupt or wrong key") from exc
    return json.loads(plain.decode("utf-8"))


def save_docmap(path: str | os.PathLike, docmap: DocMap, enc_key: bytes) -> None:
    write_atomic(path, _seal(KIND_DOCMAP, dataclasses.asdict(docmap), enc_key))


def load_docmap(path: str | os.PathLike, enc_key: bytes) -> DocMap:
    d = _open(KIND_DOCMAP, Path(path).read_bytes(), enc_key)
    return DocMap(
        doc_id=d["doc_id"],
        sha256_original=d["sha256_original"],
        sha256_anon=d["sha256_anon"],
        entries=[MapEntry(**e) for e in d["entries"]],
        occurrences=[Occurrence(**o) for o in d["occurrences"]],
        version=d.get("version", 1),
    )


def save_registry(path: str | os.PathLike, registry: dict, enc_key: bytes) -> None:
    write_atomic(path, _seal(KIND_REGISTRY, {"registry": registry}, enc_key))


def load_registry(path: str | os.PathLike, enc_key: bytes) -> dict:
    return _open(KIND_REGISTRY, Path(path).read_bytes(), enc_key)["registry"]
