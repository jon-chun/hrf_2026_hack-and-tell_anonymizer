import re
import sys
from pathlib import Path

import pytest

from anon3pass import pipeline, restore, vault
from anon3pass.types import Entity, Span

sys.path.insert(0, str(Path(__file__).parent))
from test_pipeline import MASTER, TERMS, TEXT, fake_pass1, install_fakes, make_cfg, run  # noqa: E402


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    install_fakes(monkeypatch)


def placeholder_text(text):
    return re.sub(r"sk-[A-Za-z0-9]{20,}", "[API_KEY_1]", text)


def test_exact_round_trip_is_byte_exact_with_secret_placeholder():
    anon, dm, _ = run()
    restored, stats = restore.restore_text(anon, dm)
    assert stats["mode"] == "exact"
    assert restored == placeholder_text(TEXT)
    assert "Jon Smith" in restored  # fuzzy variant keeps its own spelling in exact mode
    assert "\r\n" in restored


def test_reverse_mode_after_edits():
    anon, dm, _ = run()
    edited = "NOTE ADDED.\n" + anon.replace("agreed", "disagreed") + "Postscript."
    restored, stats = restore.restore_text(edited, dm)
    assert stats["mode"] == "reverse"
    expected = "NOTE ADDED.\n" + placeholder_text(TEXT).replace("Jon Smith", "John Smith") \
        .replace("agreed", "disagreed") + "Postscript."
    assert restored == expected
    assert stats["ambiguous_surrogates"] == 0


def test_surrogate_that_is_substring_of_another_restores_correctly():
    text = "Anna Lee met Anna. Ann Lee waved to Ann.\n"
    anon, dm, _ = run(text)
    restored, _ = restore.restore_text(anon, dm)
    assert restored == text
    edited = anon + "More."
    restored, stats = restore.restore_text(edited, dm)
    assert stats["mode"] == "reverse" and restored == text + "More."


def test_overlapping_surrogates_prefer_longest():
    text = "Ann Lee and Ann\n"
    anon, dm, _ = run(text)
    sur = sorted(e.surrogate for e in dm.entries)
    assert len(sur) == 2 and sur[1].startswith(sur[0] + " ")  # one surrogate is a prefix of the other
    restored, _ = restore.restore_text(anon + " ", dm)
    assert restored == text + " "


def test_secret_never_recoverable():
    anon, dm, _ = run()
    assert all("sk-abc" not in (e.original or "") for e in dm.entries)
    assert all("sk-abc" not in (o.original or "") for o in dm.occurrences)


def test_ambiguous_surrogate_is_left_alone():
    from anon3pass.types import DocMap, MapEntry
    dm = DocMap("d", "x", "y", [MapEntry("in their 30s", "AGE", "31 years old", "f"),
                                MapEntry("in their 30s", "AGE", "38 years old", "f")])
    out, stats = restore.restore_text("he is in their 30s", dm)
    assert out == "he is in their 30s" and stats["ambiguous_surrogates"] == 1


def test_restore_file(tmp_path):
    key = tmp_path / "master.key"
    vault.load_or_create_key(key)
    src = tmp_path / "a.txt"
    src.write_bytes(TEXT.encode())
    cfg = make_cfg(key)
    res = pipeline.anonymize_file(src, tmp_path / "out", cfg)
    stats = restore.restore_file(res["anon_path"], res["map_path"], tmp_path / "r" / "a.txt", cfg)
    assert stats["mode"] == "exact"
    assert (tmp_path / "r" / "a.txt").read_bytes() == placeholder_text(TEXT).encode()
