import json
import os
import stat
import sys
import types
from pathlib import Path

import pytest

from anon3pass import cli
from anon3pass.types import Entity, LeakFinding, Span

sys.path.insert(0, str(Path(__file__).parent))
from test_pipeline import install_fakes, make_cfg  # noqa: E402

CANARY = "Zanzibar Quillfeather"


def canary_pass1(text, cfg, terms, extra_terms=()):
    i = text.find(CANARY)
    spans = [Span(i, i + len(CANARY), CANARY, Entity.PERSON, "pass1.denylist")] if i >= 0 else []
    for t in extra_terms:
        j = text.find(t)
        if j >= 0:
            spans.append(Span(j, j + len(t), t, Entity.CUSTOM, "pass1.denylist"))
    return spans


@pytest.fixture
def env(tmp_path, monkeypatch):
    key = tmp_path / "cfg" / "master.key"
    install_fakes(monkeypatch, key_file=key, pass1=canary_pass1, pass2=lambda t, c: [])
    return types.SimpleNamespace(key=key, tmp=tmp_path)


def doc(env, name="n.txt", text=f"Please call {CANARY} today. Also Project Falcon.\n"):
    p = env.tmp / name
    p.write_text(text)
    return p


def test_run_without_key_gives_exit_4_with_hint(env, capsys):
    rc = cli.main(["run", str(doc(env)), "-o", str(env.tmp / "out")])
    err = capsys.readouterr().err
    assert rc == 4 and "init-key" in err


def test_init_key_run_restore_and_canary_never_printed(env, capsys):
    assert cli.main(["init-key"]) == 0
    assert stat.S_IMODE(env.key.stat().st_mode) == 0o600
    terms = env.tmp / "t.yaml"
    terms.write_text("terms: [Project Falcon]\n")
    src = doc(env)
    out = env.tmp / "out"
    assert cli.main(["run", str(src), "-o", str(out), "--extra-terms", str(terms)]) == 0
    assert cli.main(["--json", "run", str(src), "-o", str(out), "--extra-terms", str(terms)]) == 0
    anon = out / "n.anon.txt"
    assert cli.main(["restore", str(anon), "--map", str(out / "n.map.enc"), "-o", str(env.tmp / "r.txt")]) == 0
    assert cli.main(["restore", str(anon), "--map", str(out / "missing.enc"), "-o", str(env.tmp / "r2.txt")]) == 1
    cap = capsys.readouterr()
    for stream in (cap.out, cap.err, (out / "n.report.json").read_text(), anon.read_text()):
        assert CANARY not in stream and "Zanzibar" not in stream and "Quillfeather" not in stream
    assert "Falcon" not in anon.read_text()
    assert (env.tmp / "r.txt").read_text() == src.read_text()
    assert str(out) in cap.out


def test_run_accepts_directory_non_recursively(env, capsys):
    cli.main(["init-key"])
    d = env.tmp / "in"
    (d / "sub").mkdir(parents=True)
    (d / "a.txt").write_text("hello")
    (d / "b.md").write_text("hello")
    (d / "c.pdf").write_text("x")
    (d / "sub" / "d.txt").write_text("x")
    assert cli.main(["run", str(d), "-o", str(env.tmp / "o")]) == 0
    names = {p.name for p in (env.tmp / "o").iterdir()}
    assert {"a.anon.txt", "b.anon.md"} <= names and "d.anon.txt" not in names


def test_usage_errors_exit_2(env, capsys):
    assert cli.main(["run"]) == 2
    assert cli.main(["bogus"]) == 2
    cli.main(["init-key"])
    assert cli.main(["run", str(env.tmp / "nope.txt"), "-o", str(env.tmp / "o")]) == 2


def test_key_with_open_permissions_exit_4(env, capsys):
    cli.main(["init-key"])
    os.chmod(env.key, 0o644)
    assert cli.main(["run", str(doc(env)), "-o", str(env.tmp / "o")]) == 4


def _install(monkeypatch, name, **attrs):
    mod = types.ModuleType(f"anon3pass.{name}")
    mod.__dict__.update(attrs)
    monkeypatch.setitem(sys.modules, f"anon3pass.{name}", mod)


def test_verify_exit_codes(env, monkeypatch, capsys):
    cli.main(["init-key"])
    out = env.tmp / "out"
    cli.main(["run", str(doc(env)), "-o", str(out)])
    args = ["verify", str(out / "n.anon.txt"), "--map", str(out / "n.map.enc")]
    _install(monkeypatch, "verify", verify_text=lambda a, d, c, k: [])
    assert cli.main(args) == 0
    leak = LeakFinding("exact_original", "PERSON", "high", 0, 3, "fp", "quote")
    _install(monkeypatch, "verify", verify_text=lambda a, d, c, k: [leak])
    assert cli.main(args + ["-o", str(env.tmp / "f.json")]) == 3
    assert json.loads((env.tmp / "f.json").read_text())[0]["fingerprint"] == "fp"
    low = LeakFinding("entropy", "SECRET", "low")
    _install(monkeypatch, "verify", verify_text=lambda a, d, c, k: [low])
    assert cli.main(args) == 0


def test_missing_verify_module_exit_4(env, monkeypatch, capsys):
    cli.main(["init-key"])
    out = env.tmp / "out"
    cli.main(["run", str(doc(env)), "-o", str(out)])
    monkeypatch.setitem(sys.modules, "anon3pass.verify", None)
    rc = cli.main(["verify", str(out / "n.anon.txt"), "--map", str(out / "n.map.enc")])
    assert rc == 4


def test_qa_commands_and_gate(env, monkeypatch, capsys):
    cli.main(["init-key"])
    out = env.tmp / "out"
    cli.main(["run", str(doc(env)), "-o", str(out)])
    seen = {}
    _install(monkeypatch, "qa",
             build_packet=lambda p, cfg: {"chunks": ["a", "b"], "prompt": "p", "verified": True},
             run_backend=lambda packet, cfg, path=None: {"status": "dispatch_agent", "n": len(packet["chunks"])},
             apply_findings=lambda f, dm, o, cfg: seen.setdefault("applied", {"added": 2}),
             gate=lambda r, f, cfg, reviewed=False: (r.endswith("ok.json"), "checked"))
    assert cli.main(["qa-packet", str(out / "n.anon.txt"), "-o", str(env.tmp / "p.json")]) == 0
    assert cli.main(["qa-run", str(env.tmp / "p.json"), "-o", str(env.tmp / "f.json")]) == 0
    assert json.loads((env.tmp / "f.json").read_text())["n"] == 2
    assert cli.main(["qa-apply", str(env.tmp / "f.json"), "--map", str(out / "n.map.enc"),
                     "-o", str(env.tmp / "x.yaml")]) == 0
    assert seen["applied"] == {"added": 2}
    assert cli.main(["gate", "ok.json", "--findings", "f.json"]) == 0
    assert cli.main(["gate", "bad.json", "--findings", "f.json"]) == 3
