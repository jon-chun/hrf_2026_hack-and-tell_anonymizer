import re
from pathlib import Path

import yaml

from anon3pass.surrogates import SurrogateEngine
from anon3pass.types import Entity, Span

CFG = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text())
KEY = b"\x01" * 32


def span(text, entity, source_text, nth=0, **kw):
    start = -1
    for _ in range(nth + 1):
        start = source_text.index(text, start + 1)
    return Span(start, start + len(text), text, entity, "pass1.test", **kw)


def assign(spans, src, key=KEY, registry=None):
    eng = SurrogateEngine(key, CFG, registry)
    return eng, eng.assign(spans, src)


def test_person_parts_coherent_and_case_variants():
    src = "John Smith, John, Smith, SMITH, Dr. Smith, J. Smith, Smith's"
    sp = [span("John Smith", Entity.PERSON, src), span("John", Entity.PERSON, src, 1),
          span("Smith", Entity.PERSON, src, 1), span("SMITH", Entity.PERSON, src),
          span("Smith", Entity.PERSON, src, 2), span("J. Smith", Entity.PERSON, src),
          span("Smith's", Entity.PERSON, src)]
    _, e = assign(sp, src)
    first, last = e[0].surrogate.split()
    assert e[1].surrogate == first
    assert e[2].surrogate == last
    assert e[3].surrogate == last.upper()
    assert e[4].surrogate == last
    assert e[5].surrogate == f"{first[0]}. {last}"
    assert e[6].surrogate == f"{last}'s"
    assert e[0].original == "John Smith" and e[3].original == "SMITH"


def test_fuzzy_variant_shares_canonical_surrogate():
    src = "John Smith and Jon Smith"
    sp = [span("John Smith", Entity.PERSON, src),
          span("Jon Smith", Entity.PERSON, src, canonical="John Smith")]
    _, e = assign(sp, src)
    assert e[0].surrogate == e[1].surrogate
    assert e[1].original == "John Smith"


def test_longer_name_processed_first_even_if_listed_later():
    src = "Smith then John Smith"
    sp = [span("Smith", Entity.PERSON, src), span("John Smith", Entity.PERSON, src)]
    _, e = assign(sp, src)
    assert e[0].surrogate == e[1].surrogate.split()[1]


def test_determinism_same_key_and_different_key():
    src = "John Smith wrote to Acme Corp from Paris."
    sp = [span("John Smith", Entity.PERSON, src), span("Acme Corp", Entity.ORGANIZATION, src),
          span("Paris", Entity.LOCATION, src)]
    a = [x.surrogate for x in assign(sp, src)[1]]
    b = [x.surrogate for x in assign(sp, src)[1]]
    c = [x.surrogate for x in assign(sp, src, key=b"\x02" * 32)[1]]
    assert a == b
    assert a != c


def test_registry_gives_same_surrogate_in_next_document():
    reg = {}
    src1 = "John Smith"
    _, e1 = assign([span("John Smith", Entity.PERSON, src1)], src1, registry=reg)
    assert reg["PERSON|john smith"] == e1[0].surrogate
    src2 = "Mail John Smith today"
    _, e2 = assign([span("John Smith", Entity.PERSON, src2)], src2, registry=dict(reg))
    assert e2[0].surrogate == e1[0].surrogate


def test_surrogate_never_in_source_or_originals():
    names = ["Alice", "Bob", "Carol", "Dave", "Erin", "Frank", "Grace", "Heidi"]
    src = " ".join(names)
    sp = [span(n, Entity.PERSON, src) for n in names]
    _, e = assign(sp, src)
    sur = [x.surrogate for x in e]
    assert len(set(sur)) == len(sur)
    for s in sur:
        assert s.casefold() not in src.casefold()
        assert s not in names


def test_collision_is_rehashed():
    # Seed the source with whatever the first attempt would produce.
    src0 = "Zed"
    _, e0 = assign([span("Zed", Entity.PERSON, src0)], src0)
    first = e0[0].surrogate
    src1 = f"Zed {first}"
    _, e1 = assign([span("Zed", Entity.PERSON, src1)], src1)
    assert e1[0].surrogate != first


def test_structured_formats():
    src = ("a.b@corp.io (415) 222-3344 https://corp.io/x 10.1.2.3 078-05-1120 "
           "4539578763621486 GB82 WEST 1234 5698 7654 32 AB-12345 2024-03-05 March 5, 2024 @jdoe xyz")
    items = [("a.b@corp.io", Entity.EMAIL), ("(415) 222-3344", Entity.PHONE),
             ("https://corp.io/x", Entity.URL), ("10.1.2.3", Entity.IP_ADDRESS),
             ("078-05-1120", Entity.SSN), ("4539578763621486", Entity.CREDIT_CARD),
             ("GB82 WEST 1234 5698 7654 32", Entity.IBAN), ("AB-12345", Entity.ID_NUMBER),
             ("2024-03-05", Entity.DATE), ("March 5, 2024", Entity.DATE), ("@jdoe", Entity.USERNAME)]
    _, e = assign([span(t, k, src) for t, k in items], src)
    em, ph, url, ip, ssn, cc, iban, idn, d1, d2, user = [x.surrogate for x in e]
    assert re.fullmatch(r"[\w.]+@example\.(org|com|net)", em)
    assert re.fullmatch(r"\(\d{3}\) 555-01\d\d", ph)
    assert url.startswith("https://example.org/")
    assert ip.startswith("192.0.2.")
    assert re.fullmatch(r"9\d\d-\d\d-\d{4}", ssn)
    assert cc.startswith("400000") and len(cc) == 16 and _luhn(cc)
    assert iban.startswith("GB") and iban[4] == " " and len(iban) == len(items[6][0])
    assert _iban_ok(iban)
    assert re.fullmatch(r"[A-Z]{2}-\d{5}", idn)
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", d1)
    assert re.fullmatch(r"[A-Z][a-z]+ \d{1,2}, \d{4}", d2)
    assert user.startswith("@")


def _luhn(num):
    total = 0
    for i, ch in enumerate(reversed(num)):
        d = int(ch) * (2 if i % 2 else 1)
        total += d - 9 if d > 9 else d
    return total % 10 == 0


def _iban_ok(iban):
    s = iban.replace(" ", "")
    s = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in s)) % 97 == 1


def test_dates_keep_intervals_and_unparseable_become_placeholders():
    from datetime import date
    src = "2024-03-05 then 2024-03-25 then sometime in spring 2024-13-45"
    sp = [span("2024-03-05", Entity.DATE, src), span("2024-03-25", Entity.DATE, src),
          span("2024-13-45", Entity.DATE, src)]
    _, e = assign(sp, src)
    a, b = (date.fromisoformat(e[i].surrogate) for i in (0, 1))
    assert (b - a).days == 20
    assert e[2].surrogate == "[DATE_1]" and e[2].original == "2024-13-45"


def test_age_generalize_and_other_entities_fall_back_to_redact():
    src = "34 years old and 123 Main Street"
    cfg = dict(CFG, entity_policy={**CFG["entity_policy"], "ADDRESS": "generalize"})
    eng = SurrogateEngine(KEY, cfg)
    e = eng.assign([span("34 years old", Entity.AGE, src), span("123 Main Street", Entity.ADDRESS, src)], src)
    assert e[0].surrogate == "in their 30s" and e[0].reversible
    assert e[1].surrogate == "[ADDRESS_1]" and e[1].original == "123 Main Street"


def test_keep_and_redact_policies():
    src = "Paris and Acme"
    cfg = dict(CFG, entity_policy={**CFG["entity_policy"], "LOCATION": "keep", "ORGANIZATION": "redact"})
    e = SurrogateEngine(KEY, cfg).assign(
        [span("Paris", Entity.LOCATION, src), span("Acme", Entity.ORGANIZATION, src)], src)
    assert e[0].surrogate == "Paris"
    assert e[1].surrogate == "[ORGANIZATION_1]" and e[1].original == "Acme" and e[1].reversible


def test_secrets_are_irreversible_by_default_and_vaulted_when_configured():
    src = "key sk-abc123 and sk-abc123 and sk-zzz"
    sp = [span("sk-abc123", Entity.API_KEY, src), span("sk-abc123", Entity.API_KEY, src, 1),
          span("sk-zzz", Entity.API_KEY, src)]
    eng, e = assign(sp, src)
    assert [x.surrogate for x in e] == ["[API_KEY_1]", "[API_KEY_1]", "[API_KEY_2]"]
    assert all(x.original is None and not x.reversible for x in e)
    assert e[0].fingerprint and "sk-abc123" not in str(eng.registry)
    cfg = dict(CFG, secrets_policy={"store_in_vault": True})
    e2 = SurrogateEngine(KEY, cfg).assign(sp, src)
    assert e2[0].original == "sk-abc123" and e2[0].reversible
