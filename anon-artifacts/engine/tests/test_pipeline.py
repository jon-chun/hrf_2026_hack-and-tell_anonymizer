import json
import re
import stat
import sys
import types
from pathlib import Path

import pytest
import yaml

from anon3pass import pipeline, vault
from anon3pass.types import Entity, Span

CFG = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text())
MASTER = b"\x07" * 32

NAMES = re.compile(r"John Smith|Jon Smith|SMITH|Smith|John|Anna Lee|Anna|Ann Lee|Ann")
EMAIL = re.compile(r"[\w.]+@[\w.-]+\.\w+")
PHONE = re.compile(r"\(\d{3}\) \d{3}-\d{4}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SECRET = re.compile(r"sk-[A-Za-z0-9]{20,}")


def fake_pass1(text, cfg, terms, extra_terms=()):
    spans = []
    for rx, ent in ((EMAIL, Entity.EMAIL), (PHONE, Entity.PHONE), (DATE, Entity.DATE)):
        spans += [Span(m.start(), m.end(), m.group(), ent, "pass1.regex") for m in rx.finditer(text)]
    for t in extra_terms:
        spans += [Span(m.start(), m.end(), t, Entity.CUSTOM, "pass1.denylist")
                  for m in re.finditer(re.escape(t), text)]
    for m in NAMES.finditer(text):
        canon = "John Smith" if m.group() == "Jon Smith" else None
        spans.append(Span(m.start(), m.end(), m.group(), Entity.PERSON,
                          "pass1.fuzzy" if canon else "pass1.denylist", canonical=canon))
    return spans


def fake_pass2(text, cfg):
    return [Span(m.start(), m.end(), m.group(), Entity.API_KEY, "pass2.secrets")
            for m in SECRET.finditer(text)]


def install_fakes(monkeypatch, key_file=None, pass1=fake_pass1, pass2=fake_pass2):
    for name, attrs in (("pass1_patterns", {"detect": pass1}), ("pass2_libs", {"detect": pass2}),
                        ("config", {"load_terms": lambda cfg: {"deny": [], "allow": []},
                                    "load_config": lambda path: make_cfg(key_file)})):
        mod = types.ModuleType(f"anon3pass.{name}")
        mod.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, f"anon3pass.{name}", mod)


def make_cfg(key_file=None, **over):
    cfg = json.loads(json.dumps(CFG))
    cfg["pipeline"]["passes"] = ["patterns", "libraries"]
    if key_file:
        cfg["paths"]["key_file"] = str(key_file)
    cfg.update(over)
    return cfg


TEXT = ("Dr. Smith met John Smith on 2024-03-05. John said Jon Smith emailed john.smith@acme-corp.org "
        "from (415) 222-3344.\r\nSMITH's key is sk-abcdefghijklmnopqrstuvwxyz123456. Smith agreed; "
        "see you 2024-03-15.\n")
TERMS = {"deny": [], "allow": []}


def run(text=TEXT, cfg=None, master=MASTER, registry=None, extra=()):
    return pipeline.anonymize_text(text, "doc", cfg or make_cfg(), master,
                                   {} if registry is None else registry, TERMS, extra)


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    install_fakes(monkeypatch)


def test_output_replaces_everything_and_keeps_surroundings():
    anon, dm, stats = run()
    for orig in ("John", "Smith", "Jon", "acme-corp", "222-3344", "sk-abcdef", "2024-03-05"):
        assert orig not in anon
    assert anon.startswith("Dr. ") and "\r\n" in anon and anon.endswith("\n")
    assert "[API_KEY_1]" in anon
    assert stats["by_pass"]["pass1"] == 10 and stats["by_pass"]["pass2"] == 1
    assert stats["by_entity"]["PERSON"] == 6 and stats["by_entity"]["API_KEY"] == 1
    assert "John" not in json.dumps(stats)


def test_occurrences_point_at_anonymized_text():
    anon, dm, _ = run()
    for occ in dm.occurrences:
        assert anon[occ.anon_start:occ.anon_end]
    secret = [o for o in dm.occurrences if anon[o.anon_start:o.anon_end] == "[API_KEY_1]"]
    assert secret and secret[0].original is None
    assert [o.anon_start for o in dm.occurrences] == sorted(o.anon_start for o in dm.occurrences)


def test_surrogates_never_in_source():
    anon, dm, _ = run()
    for e in dm.entries:
        if e.reversible:
            assert e.surrogate.casefold() not in TEXT.casefold()


def test_idempotent_with_same_key_and_different_with_other_key():
    a1, _, _ = run()
    a2, _, _ = run()
    b, _, _ = run(master=b"\x08" * 32)
    assert a1 == a2 and a1 != b


def test_registry_shared_across_documents():
    reg = {}
    a, _, _ = run("John Smith here.", registry=reg)
    b, _, _ = run("Later, John Smith left.", registry=reg)
    assert a.removesuffix(" here.") in b


def test_passes_respected(monkeypatch):
    anon, _, stats = run(cfg=make_cfg(pipeline={**CFG["pipeline"], "passes": ["libraries"]}))
    assert "John Smith" in anon and "[API_KEY_1]" in anon and stats["passes"] == ["libraries"]
    anon, _, _ = run(cfg=make_cfg(pipeline={**CFG["pipeline"], "passes": ["patterns"]}))
    assert "sk-abcdef" in anon and "John" not in anon


def test_extra_terms_reach_pass1():
    anon, _, _ = run("Project Falcon is here", extra=["Project Falcon"])
    assert "Falcon" not in anon


def S(start, end, ent, src, score=1.0):
    return Span(start, end, "x" * (end - start), ent, src, score)


def test_merge_rule_order():
    secret = S(5, 12, Entity.API_KEY, "pass2.secrets")
    longer = S(0, 10, Entity.PERSON, "pass1.denylist")
    assert pipeline.merge_spans([longer, secret]) == [secret]            # secret beats longer
    short = S(8, 12, Entity.EMAIL, "pass1.regex")
    assert pipeline.merge_spans([short, longer]) == [longer]             # longer wins
    hi = S(0, 10, Entity.LOCATION, "pass2.presidio", 0.9)
    lo = S(0, 10, Entity.PERSON, "pass1.denylist", 0.5)
    assert pipeline.merge_spans([lo, hi]) == [hi]                        # higher score wins
    p1 = S(0, 10, Entity.PERSON, "pass1.denylist")
    p2 = S(0, 10, Entity.LOCATION, "pass2.presidio")
    assert pipeline.merge_spans([p2, p1]) == [p1]                        # lower pass wins
    left, right = S(0, 5, Entity.PERSON, "pass1.x"), S(5, 9, Entity.EMAIL, "pass1.x")
    assert pipeline.merge_spans([right, left]) == [left, right]          # adjacent is not overlap


def test_overlap_replaced_once():
    class Dup:
        @staticmethod
        def detect(text, cfg, terms, extra=()):
            return [Span(0, 10, "John Smith", Entity.PERSON, "pass1.denylist"),
                    Span(5, 10, "Smith", Entity.PERSON, "pass2.presidio")]
    sys.modules["anon3pass.pass1_patterns"].detect = Dup.detect
    anon, dm, _ = run("John Smith")
    assert len(dm.occurrences) == 1 and anon == dm.entries[0].surrogate


def test_allow_terms_not_replaced_unless_denied():
    terms = {"deny": [], "allow": ["Smith"]}
    anon, _, _ = pipeline.anonymize_text("Smith and John", "d", make_cfg(), MASTER, {}, terms)
    assert anon.startswith("Smith and ") and "John" not in anon


def test_anonymize_file_writes_four_files_with_safe_modes(tmp_path):
    key = tmp_path / "k" / "master.key"
    vault.load_or_create_key(key)
    src = tmp_path / "note.md"
    src.write_bytes(TEXT.encode())
    out = tmp_path / "out"
    res = pipeline.anonymize_file(src, out, make_cfg(key), now=None)
    names = sorted(p.name for p in out.iterdir())
    assert names == ["_registry.registry.enc", "note.anon.md", "note.map.enc", "note.report.json"]
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
    for n in ("note.map.enc", "_registry.registry.enc"):
        assert stat.S_IMODE((out / n).stat().st_mode) == 0o600
    report = json.loads((out / "note.report.json").read_text())
    assert set(report) == {"doc_id", "sha256_original", "sha256_anon", "counts", "passes", "timestamp", "status"}
    blob = (out / "note.report.json").read_text()
    assert "Smith" not in blob and "sk-abc" not in blob
    assert res["report_path"].endswith("note.report.json")
    again = pipeline.anonymize_file(src, out, make_cfg(key))
    assert (out / "note.anon.md").read_text() == Path(again["anon_path"]).read_text()


def test_ner_span_across_a_newline_does_not_swallow_the_next_line():
    from anon3pass.pipeline import _clean
    from anon3pass.types import Entity, Span
    text = "Venue: Port Halvren\nAttendees: Ana"
    span = Span(7, 29, text[7:29], Entity.LOCATION, "pass2.presidio")
    cleaned = _clean(span, text)
    assert cleaned.text == "Port Halvren" and text[cleaned.start:cleaned.end] == "Port Halvren"
