import time

import pytest

from anon3pass.config import load_config
from anon3pass.pass1_patterns import detect
from anon3pass.types import Entity

CFG = load_config(None)
NOTERMS = {"deny": [], "allow": []}


def found(text, terms=NOTERMS, extra=(), cfg=CFG):
    spans = detect(text, cfg, terms, extra)
    for s in spans:
        assert text[s.start:s.end] == s.text
    return spans


def texts(text, entity, **kw):
    return [s.text for s in found(text, **kw) if s.entity == entity]


def test_email_and_handle_not_confused():
    t = "Mail bob@example.com or ping @bob_99 today."
    assert texts(t, Entity.EMAIL) == ["bob@example.com"]
    assert texts(t, Entity.USERNAME) == ["@bob_99"]


def test_url_strips_trailing_punct():
    assert texts("See https://example.com/a/b?x=1.", Entity.URL) == ["https://example.com/a/b?x=1"]


def test_ipv4_ipv6():
    assert texts("host 192.0.2.44 up", Entity.IP_ADDRESS) == ["192.0.2.44"]
    assert texts("v 1.2.3.4.5 and 999.1.1.1", Entity.IP_ADDRESS) == []
    assert texts("addr 2001:db8::1 ok", Entity.IP_ADDRESS) == ["2001:db8::1"]
    assert texts("at 12:30:45 sharp", Entity.IP_ADDRESS) == []


@pytest.mark.parametrize("phone", ["(555) 010-1234", "555-010-1234", "+1 555 010 1234", "+44 20 7946 0958",
                                   "555.010.1234"])
def test_phone_positive(phone):
    assert texts(f"Call {phone} now", Entity.PHONE) == [phone]


@pytest.mark.parametrize("junk", ["in 2024 we", "number 1234 here", "pi is 3.14159", "ratio 12.5 and 100.25",
                                  "ssn 123-45-6789 only", "date 2024-03-05"])
def test_phone_negative(junk):
    assert texts(junk, Entity.PHONE) == []


def test_ssn():
    assert texts("SSN 123-45-6789.", Entity.SSN) == ["123-45-6789"]
    assert texts("SSN 000-45-6789.", Entity.SSN) == []


def test_credit_card_luhn():
    assert texts("card 4111 1111 1111 1111 end", Entity.CREDIT_CARD) == ["4111 1111 1111 1111"]
    assert texts("card 4111 1111 1111 1112 end", Entity.CREDIT_CARD) == []


def test_iban_mod97():
    assert texts("pay GB82 WEST 1234 5698 7654 32 today", Entity.IBAN) == ["GB82 WEST 1234 5698 7654 32"]
    assert texts("pay GB82WEST12345698765432.", Entity.IBAN) == ["GB82WEST12345698765432"]
    assert texts("pay GB82 WEST 1234 5698 7654 33 today", Entity.IBAN) == []
    # a trailing upper-case word must not be swallowed
    assert texts("GB82 WEST 1234 5698 7654 32 AND more", Entity.IBAN) == ["GB82 WEST 1234 5698 7654 32"]


@pytest.mark.parametrize("d", ["2024-03-05", "03/05/2024", "March 5, 2024", "5 March 2024", "Mar 5",
                               "5th of March 2024", "Mar. 5"])
def test_date_positive(d):
    assert texts(f"On {d} we met", Entity.DATE) == [d]


@pytest.mark.parametrize("junk", ["yesterday", "next week", "in 2024", "version 1.2.3", "2024-13-45", "may I help"])
def test_date_negative(junk):
    assert texts(f"We said {junk}.", Entity.DATE) == []


@pytest.mark.parametrize("phrase", ["34 years old", "aged 34", "age 34", "34-year-old"])
def test_age(phrase):
    assert texts(f"The witness, {phrase}, said", Entity.AGE) == [phrase]


def test_age_negative():
    assert texts("over 200 years old and age 2024", Entity.AGE) == []


def test_custom_rule():
    cfg = load_config(None)
    cfg["pass1_patterns"]["custom_rules"] = [{"name": "case_no", "regex": r"HRF-\d{4}", "entity": "ID_NUMBER"}]
    spans = found("See HRF-1234.", cfg=cfg)
    assert [(s.text, s.entity, s.source) for s in spans] == [("HRF-1234", Entity.ID_NUMBER, "pass1.regex.case_no")]


def test_disabled_rule_not_run():
    cfg = load_config(None)
    cfg["pass1_patterns"]["enabled_rules"] = ["email"]
    spans = found("a@example.com 192.0.2.1", cfg=cfg)
    assert [s.entity for s in spans] == [Entity.EMAIL]


def test_denylist_exact_case_insensitive_whole_word():
    terms = {"deny": [{"term": "Jane Roe", "entity": "PERSON"}], "allow": []}
    t = "jane  roe met JANE ROE; Jane Roesler stayed."
    spans = [s for s in found(t, terms) if s.source == "pass1.denylist"]
    assert [s.text for s in spans] == ["jane  roe", "JANE ROE"]
    assert all(s.entity == Entity.PERSON for s in spans)


def test_fuzzy_variant_resolves_to_canonical():
    terms = {"deny": [{"term": "John Smith", "entity": "PERSON"}], "allow": []}
    spans = [s for s in found("Then Jon Smith left. Later John Smith came.", terms) if s.source == "pass1.fuzzy"]
    assert [(s.text, s.canonical, s.entity) for s in spans] == [("Jon Smith", "John Smith", Entity.PERSON)]


def test_fuzzy_respects_min_length_and_toggle():
    terms = {"deny": [{"term": "Bob", "entity": "PERSON"}], "allow": []}
    assert [s for s in found("Rob and Bobb", terms) if s.source == "pass1.fuzzy"] == []
    cfg = load_config(None)
    cfg["pass1_patterns"]["fuzzy"]["enabled"] = False
    terms = {"deny": [{"term": "Rutherford", "entity": "PERSON"}], "allow": []}
    assert [s for s in found("Rutherfard came", terms, cfg=cfg) if s.source == "pass1.fuzzy"] == []
    assert [s.text for s in found("Rutherfard came", terms) if s.source == "pass1.fuzzy"] == ["Rutherfard"]


def test_extra_terms_custom_entity():
    spans = found("The Zebra Fund paid.", extra=["zebra fund"])
    assert [(s.text, s.entity) for s in spans] == [("Zebra Fund", Entity.CUSTOM)]


def test_allow_suppresses_but_deny_wins():
    t = "Contact info@example.com or Geneva office."
    terms = {"deny": [], "allow": ["info@example.com"]}
    assert texts(t, Entity.EMAIL, terms=terms) == []
    terms = {"deny": [{"term": "info@example.com", "entity": "EMAIL"}], "allow": ["info@example.com"]}
    assert texts(t, Entity.EMAIL, terms=terms)  # also in deny: still found


def test_fuzzy_speed_on_200kb():
    words = ["alpha", "bravo", "delta", "report", "meeting", "budget", "Maria", "said", "the", "of"]
    text = " ".join(words[i % len(words)] for i in range(36000))
    assert len(text) > 190_000
    terms = {"deny": [{"term": f"Person Number{i}", "entity": "PERSON"} for i in range(30)], "allow": []}
    t0 = time.time()
    detect(text, CFG, terms)
    assert time.time() - t0 < 20


@pytest.mark.parametrize("text,entity", [
    ("sort code 20-45-17, acct 63820914", "BANK_ACCOUNT"),
    ("A/C 004512367890 at the branch", "BANK_ACCOUNT"),
    ("national number 650102198507123456 on file", "ID_NUMBER"),
    ("plate LK-19 ZZR on the van", "ID_NUMBER"),
    ("call plus four four seven seven double zero nine oh one", "ID_NUMBER"),
    ("write to fola dot b at gmail dot com today", "EMAIL"),
    ("back on the seventeenth of june", "DATE"),
    ("VPN: user lantern-vpn only", "USERNAME"),
    ("14 Rue des Tanneurs, 1000 Bruxelles", "ADDRESS"),
])
def test_civil_society_formats(text, entity):
    from anon3pass.config import load_config
    from anon3pass import pass1_patterns
    found = pass1_patterns.detect(text, load_config(None), {"deny": [], "allow": []})
    assert entity in {s.entity.value for s in found}


@pytest.mark.parametrize("text", ["please send login details", "the user said it was late", "Login: password"])
def test_ordinary_words_after_user_labels_are_not_usernames(text):
    from anon3pass.config import load_config
    from anon3pass import pass1_patterns
    found = pass1_patterns.detect(text, load_config(None), {"deny": [], "allow": []})
    assert "USERNAME" not in {s.entity.value for s in found}
