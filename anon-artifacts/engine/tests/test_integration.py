"""Real modules wired together, no fakes and no NER model. These cover the seams between modules."""
import json
import yaml
import pytest
from anon3pass import cli
from anon3pass.config import load_config
from anon3pass.pipeline import anonymize_text
from anon3pass.restore import restore_text

TEXT = """Attendees: Ana Costa
Passport K4471982, office at 27 Harbour Street. Contact ana@realorg.test.
Ana said the key AKIAIOSFODNN7EXAMPLEX must rotate. ANA agreed.
"""


@pytest.fixture
def cfg(tmp_path):
    c = load_config(None)
    c["pipeline"]["passes"] = ["patterns"]
    c["paths"]["key_file"] = str(tmp_path / "k.key")
    c["paths"]["terms_file"] = str(tmp_path / "none.yaml")
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(c))
    return c, str(p), tmp_path


def test_address_id_and_full_secret_token_are_replaced(cfg):
    c, _, _ = cfg
    c["pipeline"]["passes"] = ["patterns", "libraries"]
    c["pass2_libraries"]["ner"]["engine"] = "none"
    anon, dm, _ = anonymize_text(TEXT, "d", c, b"k" * 32, {}, {"deny": [{"term": "Ana Costa", "entity": "PERSON"}], "allow": []})
    for leak in ("K4471982", "27 Harbour Street", "AKIAIOSFODNN7EXAMPLE", "Costa"):
        assert leak not in anon
    assert "EXAMPLEX" not in anon, "a secret must be replaced to the end of its token"
    assert "Ana" not in anon and "ANA" not in anon, "name parts must propagate to every mention"
    assert restore_text(anon, dm)[0].count("Ana") == 2


def test_public_entities_stay(cfg):
    c, _, _ = cfg
    c["pipeline"]["keep_public_entities"] = ["United Nations"]
    terms = {"deny": [], "allow": []}
    anon, _, _ = anonymize_text("Ana wrote to the United Nations.", "d", c, b"k" * 32, {"PERSON|ana": "Bea"}, terms)
    assert "United Nations" in anon


def test_verify_then_packet_then_feedback_loop_through_cli(cfg, capsys):
    _, cpath, tmp = cfg
    src = tmp / "n.txt"
    src.write_text("Ana visited Ostermark on 2024-03-05.\n")
    out = tmp / "out"
    base = ["--config", cpath]
    assert cli.main([*base, "init-key"]) == 0
    assert cli.main([*base, "run", str(src), "-o", str(out)]) == 0
    anon = out / "n.anon.txt"
    packet = tmp / "p.json"
    # No recorded verify yet: refuse to prepare text for a model.
    assert cli.main([*base, "qa-packet", str(anon), "-o", str(packet)]) == 3
    assert cli.main([*base, "verify", str(anon), "--map", str(out / "n.map.enc")]) == 0
    assert cli.main([*base, "qa-packet", str(anon), "-o", str(packet)]) == 0
    assert json.loads(packet.read_text())["verified"] is True

    findings = tmp / "f.json"
    findings.write_text(json.dumps({"doc_id": "n", "findings": [{"quote": "Ostermark", "category": "location", "severity": "high", "reason": "real-looking place", "suggested_action": "replace"}], "reidentification_risk": {"level": "low", "rationale": "x"}}))
    terms = tmp / "x.yaml"
    assert cli.main([*base, "qa-apply", str(findings), "--map", str(out / "n.map.enc"), "-o", str(terms)]) == 0
    assert cli.main([*base, "run", str(src), "-o", str(out), "--extra-terms", str(terms)]) == 0
    assert "Ostermark" not in anon.read_text(), "QA findings must reach the next run"
    assert "Ostermark" not in capsys.readouterr().out.replace(str(terms), "")


def test_redacted_password_is_not_a_leak_but_a_real_one_is(cfg):
    from anon3pass import vault
    from anon3pass.verify import verify_text
    c, _, _ = cfg
    c["pipeline"]["passes"] = ["patterns", "libraries"]
    c["pass2_libraries"]["ner"]["engine"] = "none"
    text = 'Login: password: Blue-Harbor-4471 and then password = "Orchard-9921". Done.\n'
    anon, dm, _ = anonymize_text(text, "d", c, b"k" * 32, {}, {"deny": [], "allow": []})
    _, h = vault.derive_keys(b"k" * 32)
    assert verify_text(anon, dm, c, h) == []
    assert "high" in {f.severity for f in verify_text(anon + 'password = "Other-Real-7734"\n', dm, c, h)}
