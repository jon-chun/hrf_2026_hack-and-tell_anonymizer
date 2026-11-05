import re
import sys
import types
from pathlib import Path

import pytest
import yaml

from anon3pass.types import DocMap, Entity, MapEntry, Span
from anon3pass import verify

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config.yaml").read_text())
KEY = b"k" * 32


def entry(orig, surrogate, entity="PERSON"):
    return MapEntry(surrogate=surrogate, entity=entity, original=orig, fingerprint="fp_" + str(abs(hash(orig)) % 9999))


def docmap(*entries):
    return DocMap(doc_id="d", sha256_original="a", sha256_anon="b", entries=list(entries))


@pytest.fixture(autouse=True)
def fake_modules(monkeypatch):
    p1 = types.ModuleType("anon3pass.pass1_patterns")

    def detect1(text, cfg, terms, extra_terms=()):
        assert terms == {"deny": [], "allow": []}
        return [Span(m.start(), m.end(), m.group(), Entity.EMAIL, "pass1.regex.email")
                for m in re.finditer(r"[\w.-]+@[\w.-]+\.\w+", text)]

    p1.detect = detect1
    p2 = types.ModuleType("anon3pass.pass2_libs")
    p2.detect_secrets_only = lambda text, cfg: [
        Span(m.start(), m.end(), m.group(), Entity.API_KEY, "pass2.secrets") for m in re.finditer(r"AKIA[A-Z0-9]{16}", text)]
    vault = types.ModuleType("anon3pass.vault")
    vault.fingerprint = lambda key, value: "fp:" + str(len(value))
    for name, mod in (("pass1_patterns", p1), ("pass2_libs", p2), ("vault", vault)):
        monkeypatch.setitem(sys.modules, "anon3pass." + name, mod)


def test_exact_original_is_high_and_carries_no_original():
    dm = docmap(entry("Henrik Valdane", "Mark Davis"))
    found = verify.verify_text("Report by Henrik Valdane today.", dm, CFG, KEY)
    assert [f.category for f in found] == ["exact_original"]
    assert found[0].severity == "high" and (found[0].anon_start, found[0].anon_end) == (10, 24)
    assert "Valdane" not in repr(found) and found[0].quote == ""


def test_case_and_spacing_variants():
    dm = docmap(entry("Henrik Valdane", "Mark Davis"))
    found = verify.verify_text("HENRIK  VALDANE spoke.", dm, CFG, KEY)
    assert found[0].category == "normalized_original"


def test_digit_separators_normalized():
    dm = docmap(entry("4111 1111 1111 1111", "4539 0000 0000 0001", "CREDIT_CARD"))
    found = verify.verify_text("Card 4111-1111-1111-1111 on file", dm, CFG, KEY)
    assert found and found[0].category == "normalized_original"


def test_fuzzy_name_variant():
    dm = docmap(entry("Henrik Valdane", "Mark Davis"))
    found = verify.verify_text("Contact Henrick Valdane soon.", dm, CFG, KEY)
    assert [f.category for f in found] == ["fuzzy_original"]


def test_surrogates_and_placeholders_do_not_self_flag():
    dm = docmap(entry("a@real.com", "jo.smith@example.org", "EMAIL"), entry("Henrik Valdane", "Mark Davis"))
    text = "Mail jo.smith@example.org, Mark Davis, key [API_KEY_1] done."
    assert verify.verify_text(text, dm, CFG, KEY) == []


def test_surrogate_equal_to_reused_original_is_not_a_finding():
    # "Dana" is the original of one entry and the surrogate of another: not a leak
    dm = docmap(entry("Carol", "Dana"), entry("Dana", "Erin"))
    assert verify.verify_text("Dana met Erin.", dm, CFG, KEY) == []


def test_short_original_only_whole_word():
    dm = docmap(entry("Al", "Bo"))
    assert verify.verify_text("Alabama and Allen", dm, CFG, KEY) == []
    found = verify.verify_text("Then Al left.", dm, CFG, KEY)
    assert found and found[0].category == "exact_original"


def test_irreversible_entries_are_skipped():
    dm = docmap(MapEntry("[API_KEY_1]", "API_KEY", None, "fp", reversible=False))
    assert verify.verify_text("nothing here", dm, CFG, KEY) == []


def test_pattern_and_secret_rerun_on_unmasked_text():
    dm = docmap(entry("x", "y"))
    found = verify.verify_text("Write to leak@real-corp.com with AKIAABCDEFGHIJKLMNOP", dm, CFG, KEY)
    cats = sorted((f.category, f.entity) for f in found)
    assert ("pattern", "EMAIL") in cats and ("secret", "API_KEY") in cats
    assert all(f.quote == "" and f.fingerprint.startswith("fp:") for f in found)


def test_entropy_scan():
    dm = docmap(entry("x", "y"))
    tok = "q8Zx7LmP2vB9nR4tYw6KdJ3hF5gS1aCe"
    found = verify.verify_text(f"blob {tok} end", dm, CFG, KEY)
    assert [f.category for f in found] == ["entropy"] and found[0].severity == "medium"


def test_entity_policy_keep_is_not_flagged():
    cfg = {**CFG, "entity_policy": {**CFG["entity_policy"], "EMAIL": "keep"}}
    dm = docmap(entry("x", "y"))
    assert verify.verify_text("see a@b-corp.com", dm, cfg, KEY) == []
