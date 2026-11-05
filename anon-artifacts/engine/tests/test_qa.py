import copy
import json
import sys
import types
from pathlib import Path

import pytest
import yaml

from anon3pass import qa
from anon3pass.types import DocMap, LeakFinding, MapEntry

ENGINE = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ENGINE / "config.yaml").read_text())
DOC_TEXT = "Alice Moreau met Bob Chen in Lyon.\n" * 3


def cfg_with(**qa_over):
    c = copy.deepcopy(CFG)
    c["pass3_agent_qa"].update(qa_over)
    return c


def finding(quote="Alice", category="name", severity="high", action="replace"):
    return {"quote": quote, "category": category, "severity": severity, "reason": "r", "suggested_action": action}


def result(findings, level="low"):
    return {"doc_id": "d", "findings": findings, "reidentification_risk": {"level": level, "rationale": "x"}}


def docmap():
    return DocMap("d", "a", "b", entries=[MapEntry("Alice Moreau", "PERSON", "Ann Real", "fp")])


@pytest.fixture
def anon_file(tmp_path):
    p = tmp_path / "d.anon.txt"
    p.write_text(DOC_TEXT, encoding="utf-8")
    return p


def fake_verify(monkeypatch, severities):
    mod = types.ModuleType("anon3pass.verify_fake")
    monkeypatch.setattr("anon3pass.verify.verify_text",
                        lambda a, d, c, k: [LeakFinding("pattern", "EMAIL", s) for s in severities])


# ---- prompt mirror
def test_prompt_mirrored_in_reference_file():
    ref = ENGINE.parent / ".claude" / "skills" / "anon-qa" / "references" / "auditor-prompt.md"
    assert ref.read_text(encoding="utf-8").strip() == qa.AUDITOR_PROMPT.strip()


def test_prompt_content():
    p = qa.AUDITOR_PROMPT
    assert "DOCUMENT-BEGIN" in p and "untrusted" in p and "known_surrogates" in p
    assert "example.org" in p and "re-identification" in p.lower()


# ---- packet
def test_chunking_offsets_and_overlap(anon_file):
    cfg = cfg_with(chunk_chars=40, chunk_overlap_chars=10)
    pk = qa.build_packet(anon_file, cfg)
    ch = pk["chunks"]
    assert len(ch) > 1 and ch[0]["start"] == 0 and ch[-1]["end"] == len(DOC_TEXT)
    assert ch[1]["start"] == ch[0]["end"] - 10
    assert all(DOC_TEXT[c["start"]:c["end"]] == c["text"] for c in ch)


def test_packet_unverified_without_map(anon_file):
    assert qa.build_packet(anon_file, CFG)["verified"] is False


def test_packet_verified_only_when_no_high(anon_file, monkeypatch):
    fake_verify(monkeypatch, ["medium", "low"])
    assert qa.build_packet(anon_file, CFG, docmap(), b"k")["verified"] is True
    fake_verify(monkeypatch, ["high"])
    assert qa.build_packet(anon_file, CFG, docmap(), b"k")["verified"] is False


def test_packet_verified_from_report(anon_file):
    import hashlib
    rep = {"verify": {"high": 0, "sha256_anon": hashlib.sha256(DOC_TEXT.encode()).hexdigest()}}
    (anon_file.parent / "d.report.json").write_text(json.dumps(rep))
    assert qa.build_packet(anon_file, CFG)["verified"] is True
    rep["verify"]["sha256_anon"] = "0" * 64
    (anon_file.parent / "d.report.json").write_text(json.dumps(rep))
    assert qa.build_packet(anon_file, CFG)["verified"] is False


# ---- run_backend
def test_run_backend_refuses_unverified(anon_file):
    pk = qa.build_packet(anon_file, CFG)
    for backend in ("claude_code", "anthropic", "ollama"):
        with pytest.raises(ValueError, match="not verified"):
            qa.run_backend(pk, cfg_with(backend=backend))


def test_backend_none_is_skipped(anon_file):
    out = qa.run_backend(qa.build_packet(anon_file, CFG), cfg_with(backend="none"))
    assert out["status"] == "skipped" and out["findings"] == []
    qa.validate_findings(out)


def test_claude_code_dispatch(anon_file):
    pk = qa.build_packet(anon_file, CFG)
    pk["verified"] = True
    out = qa.run_backend(pk, cfg_with(backend="claude_code"), packet_path="/x/p.json")
    assert out == {"status": "dispatch_agent", "agent": "anon-leak-auditor", "packet": "/x/p.json"}


def test_ollama_backend_merges_chunks(anon_file, monkeypatch):
    pk = qa.build_packet(anon_file, cfg_with(chunk_chars=40, chunk_overlap_chars=10))
    pk["verified"] = True
    seen = []

    def fake_post(url, payload, timeout=0):
        seen.append((url, payload))
        body = result([finding("Bob Chen", severity="medium")], level="medium")
        return {"message": {"content": json.dumps(body)}}

    monkeypatch.setattr(qa, "_post_json", fake_post)
    out = qa.run_backend(pk, cfg_with(backend="ollama", chunk_chars=40, chunk_overlap_chars=10))
    assert seen[0][0] == "http://localhost:11434/api/chat" and seen[0][1]["format"] == "json"
    assert len(seen) == len(pk["chunks"])
    assert len(out["findings"]) == 1 and out["findings"][0]["anon_start"] >= 0
    assert out["reidentification_risk"]["level"] == "medium"
    qa.validate_findings(out)


def install_fake_anthropic(monkeypatch, stop_reason="end_turn", body=None):
    calls = {}

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            text = json.dumps(body or result([]))
            return types.SimpleNamespace(stop_reason=stop_reason,
                                         content=[types.SimpleNamespace(type="text", text=text)])

    class Messages:
        def stream(self, **kw):
            calls.update(kw)
            return Stream()

    class Client:
        def __init__(self, *a, **kw):
            calls["client_args"] = (a, kw)
            self.beta = types.SimpleNamespace(messages=Messages())

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Client))
    return calls


def test_anthropic_backend_request_shape(anon_file, monkeypatch):
    calls = install_fake_anthropic(monkeypatch, body=result([finding("Lyon", "location", "low")]))
    pk = qa.build_packet(anon_file, CFG)
    pk["verified"] = True
    out = qa.run_backend(pk, cfg_with(backend="anthropic"))
    assert calls["client_args"] == ((), {})            # key from SDK default resolution only
    assert calls["model"] == "claude-opus-5-5"
    assert calls["betas"] == ["server-side-fallback-2026-07-01"] and calls["fallbacks"] == "default"
    assert calls["output_config"]["effort"] == "high"
    assert calls["output_config"]["format"]["type"] == "json_schema"
    assert "DOCUMENT-BEGIN" in calls["messages"][0]["content"]
    assert out["findings"][0]["quote"] == "Lyon"


def test_anthropic_refusal_checked_before_content(anon_file, monkeypatch):
    install_fake_anthropic(monkeypatch, stop_reason="refusal")
    pk = qa.build_packet(anon_file, CFG)
    pk["verified"] = True
    with pytest.raises(RuntimeError, match="refused"):
        qa.run_backend(pk, cfg_with(backend="anthropic"))


# ---- validation
def test_validate_accepts_and_rejects():
    ok = result([finding()])
    assert qa.validate_findings(ok)["findings"][0]["quote"] == "Alice"
    bad = [
        [],
        {**ok, "extra": 1},
        {**ok, "findings": [{**finding(), "severity": "critical"}]},
        {**ok, "findings": [{**finding(), "surprise": 1}]},
        {**ok, "findings": [{k: v for k, v in finding().items() if k != "reason"}]},
        {**ok, "reidentification_risk": {"level": "high"}},
        {**ok, "doc_id": 5},
    ]
    for b in bad:
        with pytest.raises(ValueError):
            qa.validate_findings(b)


# ---- apply
def test_apply_findings(tmp_path):
    fp = tmp_path / "f.json"
    fp.write_text(json.dumps(result([
        finding("Zainab Okoye"),
        finding("Alice Moreau, Zawadi"),              # the part that is not a surrogate is kept
        finding("Alice Moreau"),                      # a known surrogate: skipped
        finding("[API_KEY_1]"),                       # placeholder: skipped
        finding("judge in the north", "quasi_identifier", "high", "human_review"),
        finding("minor", severity="low"),
        finding("Zainab Okoye"),                      # duplicate
    ])))
    out = tmp_path / "t.yaml"
    stats = qa.apply_findings(fp, docmap(), out, CFG)
    assert stats["added"] == 2 and stats["skipped_surrogate"] == 2 and stats["skipped_human_review"] == 1
    assert yaml.safe_load(out.read_text())["extra_terms"] == [{"term": "Zainab Okoye", "entity": "PERSON"}, {"term": "Zawadi", "entity": "PERSON"}]
    assert oct(out.stat().st_mode & 0o777) == "0o600"
    assert "Zainab" not in json.dumps(stats)
    qa.apply_findings(fp, docmap(), out, CFG)          # idempotent
    assert len(yaml.safe_load(out.read_text())["extra_terms"]) == 2


# ---- gate
def write(path, obj):
    path.write_text(json.dumps(obj))
    return path


def test_gate_passes_clean(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d", "verify": {"high": 0}})
    fnd = write(tmp_path / "f.json", result([finding(severity="low")]))
    ok, msg = qa.gate(rep, fnd, CFG)
    assert ok and "gate passed" in msg


def test_gate_fails_on_high_finding_and_hides_quotes(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d"})
    fnd = write(tmp_path / "f.json", result([finding("SecretQuote", severity="high")]))
    ok, msg = qa.gate(rep, fnd, CFG)
    assert not ok and "1 high" in msg and "SecretQuote" not in msg


def test_gate_respects_fail_on_medium(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d"})
    fnd = write(tmp_path / "f.json", result([finding(severity="medium")]))
    assert qa.gate(rep, fnd, CFG)[0] is True
    cfg = copy.deepcopy(CFG)
    cfg["pipeline"]["fail_on"] = "medium"
    assert qa.gate(rep, fnd, cfg)[0] is False


def test_gate_missing_findings(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d"})
    ok, msg = qa.gate(rep, tmp_path / "nope.json", CFG)
    assert not ok and "missing" in msg
    cfg = copy.deepcopy(CFG)
    cfg["pipeline"]["passes"] = ["patterns", "libraries"]
    assert qa.gate(rep, tmp_path / "nope.json", cfg)[0] is True


def test_gate_verify_high_in_report_fails(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d", "verify": {"high": 2}})
    fnd = write(tmp_path / "f.json", result([]))
    ok, msg = qa.gate(rep, fnd, CFG)
    assert not ok and "local verify" in msg


def test_gate_human_review_message(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "d"})
    fnd = write(tmp_path / "f.json", result([finding("x", "quasi_identifier", "medium", "human_review")]))
    ok, msg = qa.gate(rep, fnd, CFG)
    assert not ok and "REQUIRED HUMAN REVIEW: 1" in msg
    ok, msg = qa.gate(rep, fnd, CFG, human_reviewed=True)
    assert ok and "human review recorded for 1" in msg


def test_gate_doc_id_mismatch(tmp_path):
    rep = write(tmp_path / "r.json", {"doc_id": "other"})
    fnd = write(tmp_path / "f.json", result([]))
    assert qa.gate(rep, fnd, CFG)[0] is False
