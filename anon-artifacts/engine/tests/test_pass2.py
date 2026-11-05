import pytest

from anon3pass import pass2_libs
from anon3pass.config import load_config
from anon3pass.pass2_libs import detect, detect_secrets_only
from anon3pass.types import Entity

CFG = load_config(None)

# Synthetic secrets, assembled from fragments so no scanner sees a literal key in this file.
AWS = "AKIA" + "IOSFODNN7EXAMPLE"
GH = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
SLACK = "xoxb-" + "123456789012-abcdefABCDEF"
ANTH = "sk-ant-" + "api03-AbCdEfGhIjKlMnOpQrStUvWx"
OPENAI = "sk-" + "proj1234567890abcdefghijklmn"
GOOG = "AIza" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q"
STRIPE = "sk_live_" + "4eC39HqLyjWDarjtT1zdp7dc"
JWT = "eyJhbGciOiJIUzI1NiJ9" + ".eyJzdWIiOiJ0ZXN0MTIzIn0" + ".c2lnbmF0dXJlMTIzNDU"
PEM = ("-----BEGIN RSA " + "PRIVATE KEY-----\nMIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu\n"
       "KUpRKfFLfRYC9AIKjbJTWit+CqvjWYzvQwECAwEAAQ==\n-----END RSA " + "PRIVATE KEY-----")


def secrets(text, cfg=CFG):
    spans = detect_secrets_only(text, cfg)
    for s in spans:
        assert text[s.start:s.end] == s.text
    return spans


def kinds(text):
    return {(s.text, s.entity) for s in secrets(text)}


def test_ner_returns_person_org_location():
    text = "Maria Gonzalez works at Amnesty International in Geneva."
    spans = detect(text, CFG)
    got = {(s.text, s.entity) for s in spans}
    assert ("Maria Gonzalez", Entity.PERSON) in got
    assert ("Amnesty International", Entity.ORGANIZATION) in got
    assert ("Geneva", Entity.LOCATION) in got
    assert all(text[s.start:s.end] == s.text and s.source.startswith("pass2.") for s in spans)


def test_ner_never_emits_dates():
    spans = detect("The hearing was on March 5, 2024 at noon.", CFG)
    assert not [s for s in spans if s.entity == Entity.DATE]


def test_entities_and_threshold_respected():
    cfg = load_config(None)
    cfg["pass2_libraries"]["ner"]["entities"] = ["PERSON"]
    spans = detect("Maria Gonzalez works at Amnesty International in Geneva.", cfg)
    assert {s.entity for s in spans} == {Entity.PERSON}
    cfg["pass2_libraries"]["ner"]["score_threshold"] = 0.99
    assert detect("Maria Gonzalez works in Geneva.", cfg) == []


def test_pattern_recognizers_toggle():
    text = "Write to maria@example.com please."
    assert any(s.entity == Entity.EMAIL for s in detect(text, CFG))
    cfg = load_config(None)
    cfg["pass2_libraries"]["presidio_pattern_recognizers"] = False
    assert not any(s.entity == Entity.EMAIL for s in detect(text, cfg))


def test_engine_none_only_secrets():
    cfg = load_config(None)
    cfg["pass2_libraries"]["ner"]["engine"] = "none"
    spans = detect(f"Maria Gonzalez key {AWS}", cfg)
    assert [s.text for s in spans] == [AWS]


def test_chunking_keeps_offsets_and_seam_entities(monkeypatch):
    monkeypatch.setattr(pass2_libs, "_max_length", lambda a: 2200)
    filler = "The committee reviewed the budget and the schedule. " * 40
    text = filler + "Maria Gonzalez met Amnesty International staff in Geneva. " + filler * 2
    assert len(text) > 2200
    spans = [s for s in detect(text, CFG) if s.source == "pass2.presidio"]
    for s in spans:
        assert text[s.start:s.end] == s.text
    assert [s.text for s in spans].count("Maria Gonzalez") == 1
    assert [s.text for s in spans].count("Geneva") == 1


def test_chunk_bounds_partition_text():
    b = pass2_libs._chunk_bounds(10_000, 2200)
    assert b[0][0] == 0 and b[-1][1] == 10_000
    assert all(b[i][1] == b[i + 1][0] for i in range(len(b) - 1))


def test_missing_optional_engines_raise_runtimeerror(monkeypatch):
    cfg = load_config(None)
    cfg["pass2_libraries"]["ner"]["engine"] = "opf"
    monkeypatch.setattr(pass2_libs.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        detect("x", cfg)
    cfg["pass2_libraries"]["ner"]["engine"] = "gliner2"
    with pytest.raises(RuntimeError):
        detect("x", cfg)


@pytest.mark.parametrize("secret,entity", [
    (AWS, Entity.API_KEY), (GH, Entity.TOKEN), (SLACK, Entity.TOKEN), (ANTH, Entity.API_KEY),
    (OPENAI, Entity.API_KEY), (GOOG, Entity.API_KEY), (STRIPE, Entity.API_KEY), (JWT, Entity.TOKEN),
])
def test_provider_formats(secret, entity):
    got = kinds(f"deploy notes: {secret} (rotate soon)")
    assert (secret, entity) in got


def test_password_value_only():
    text = "login password=hunter2xyz and pwd: 'open sesame' then passphrase = correcthorse"
    got = {s.text for s in secrets(text) if s.entity == Entity.PASSWORD}
    assert got == {"hunter2xyz", "open sesame", "correcthorse"}


def test_bearer_value_only():
    tok = "abcDEF123456ghiJKL789"
    spans = secrets(f"Authorization: Bearer {tok}")
    assert tok in {s.text for s in spans}
    assert not any("Authorization" in s.text for s in spans)


def test_pem_block_spans_lines():
    text = f"before\n{PEM}\nafter"
    spans = [s for s in secrets(text) if s.entity == Entity.PRIVATE_KEY]
    assert len(spans) == 1 and spans[0].text == PEM and "\n" in spans[0].text


def test_entropy_token():
    tok = "q8Zx3KpL0vB7nR2mT5yW9cD4"  # 24 chars, mixed
    spans = secrets(f"blob {tok} end")
    assert any(s.text == tok and s.entity == Entity.SECRET for s in spans)
    assert secrets("internationalization is a very long ordinary word indeed") == []


def test_no_false_positives_on_plain_prose():
    assert secrets("The password policy was reviewed on Tuesday. Tokens of appreciation were given.") == []


def test_placeholders_not_redetected():
    assert secrets("password=[PASSWORD_1] key [API_KEY_2]") == []


def test_gitleaks_toggle_and_missing_binary(monkeypatch):
    cfg = load_config(None)
    cfg["pass2_libraries"]["secrets"]["gitleaks"] = True
    monkeypatch.setattr(pass2_libs.shutil, "which", lambda name: None)
    monkeypatch.setattr(pass2_libs.os.path, "exists", lambda p: False)
    with pytest.raises(RuntimeError):
        detect_secrets_only("x", cfg)
    cfg["pass2_libraries"]["secrets"]["gitleaks"] = "auto"
    detect_secrets_only("x", cfg)  # auto without the binary is silent


def _only(engine):
    cfg = load_config(None)
    sec = cfg["pass2_libraries"]["secrets"]
    sec.update(detect_secrets=False, credential_rules=False, entropy_min=0, gitleaks=False)
    sec[engine] = True
    return cfg


def test_detect_secrets_library_alone_covers_basic_auth_value():
    text = "fetch http://svcuser:S3cretPassw0rd@example.com/x now"
    spans = detect_secrets_only(text, _only("detect_secrets"))
    assert [s.text for s in spans] == ["S3cretPassw0rd"]


def test_detect_secrets_library_full_token_not_prefix():
    spans = detect_secrets_only(f"t={GH}", _only("detect_secrets"))
    assert [s.text for s in spans] == [GH]


@pytest.mark.skipif(not pass2_libs.shutil.which("gitleaks") and not pass2_libs.os.path.exists("/opt/homebrew/bin/gitleaks"),
                    reason="gitleaks binary not installed")
def test_gitleaks_alone_offsets():
    text = f"x\nGITHUB_TOKEN={GH}\nend"
    spans = detect_secrets_only(text, _only("gitleaks"))
    assert any(s.text == GH for s in spans)


def test_secrets_fast_on_200kb():
    import time
    text = "The quick brown fox, meeting notes and budget lines. user=alice\n" * 3300
    assert len(text) > 200_000
    t0 = time.time()
    detect_secrets_only(text, load_config(None))
    assert time.time() - t0 < 20
