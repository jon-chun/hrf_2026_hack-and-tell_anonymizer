import os
import stat

import pytest

from anon3pass import vault
from anon3pass.types import DocMap, MapEntry, Occurrence


def test_key_created_with_safe_modes(tmp_path):
    path = tmp_path / "sub" / "master.key"
    key = vault.load_or_create_key(path)
    assert len(key) == 32
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert vault.load_or_create_key(path) == key


def test_key_with_group_or_other_permissions_refused(tmp_path):
    path = tmp_path / "master.key"
    vault.load_or_create_key(path)
    os.chmod(path, 0o640)
    with pytest.raises(vault.KeyFileError, match="permissions"):
        vault.load_or_create_key(path)
    with pytest.raises(vault.KeyFileError):
        vault.load_key(path)


def test_derived_keys_are_distinct_and_stable():
    enc, mac = vault.derive_keys(b"k" * 32)
    assert enc != mac and len(enc) == len(mac) == 32
    assert vault.derive_keys(b"k" * 32) == (enc, mac)
    assert vault.derive_keys(b"j" * 32) != (enc, mac)


def test_fingerprint_is_keyed():
    assert vault.fingerprint(b"a" * 32, "x") == vault.fingerprint(b"a" * 32, "x")
    assert vault.fingerprint(b"a" * 32, "x") != vault.fingerprint(b"b" * 32, "x")


def _docmap():
    return DocMap("d", "aa", "bb",
                  [MapEntry("Mark", "PERSON", "John", "fp"), MapEntry("[API_KEY_1]", "API_KEY", None, "fp2", False)],
                  [Occurrence(0, 4, "John"), Occurrence(5, 16, None)])


def test_docmap_and_registry_round_trip(tmp_path):
    enc, _ = vault.derive_keys(b"k" * 32)
    vault.save_docmap(tmp_path / "d.map.enc", _docmap(), enc)
    assert vault.load_docmap(tmp_path / "d.map.enc", enc) == _docmap()
    assert stat.S_IMODE((tmp_path / "d.map.enc").stat().st_mode) == 0o600
    vault.save_registry(tmp_path / "r.enc", {"PERSON|john": "Mark"}, enc)
    assert vault.load_registry(tmp_path / "r.enc", enc) == {"PERSON|john": "Mark"}
    assert b"John" not in (tmp_path / "d.map.enc").read_bytes()
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


def test_tampered_vault_rejected(tmp_path):
    enc, _ = vault.derive_keys(b"k" * 32)
    path = tmp_path / "d.map.enc"
    vault.save_docmap(path, _docmap(), enc)
    blob = bytearray(path.read_bytes())
    blob[-1] ^= 1
    path.write_bytes(bytes(blob))
    with pytest.raises(vault.VaultError, match="tampered"):
        vault.load_docmap(path, enc)


def test_wrong_kind_and_wrong_key_rejected(tmp_path):
    enc, _ = vault.derive_keys(b"k" * 32)
    vault.save_docmap(tmp_path / "d", _docmap(), enc)
    with pytest.raises(vault.VaultError):
        vault.load_registry(tmp_path / "d", enc)  # AAD binds the file kind
    with pytest.raises(vault.VaultError):
        vault.load_docmap(tmp_path / "d", vault.derive_keys(b"z" * 32)[0])
