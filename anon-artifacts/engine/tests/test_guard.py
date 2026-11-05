import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "guard_raw.py"
CWD = "/proj/anon-artifacts"


def run(tool, tool_input, raw=None):
    payload = raw if raw is not None else json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": CWD})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


@pytest.mark.parametrize("tool,tin", [
    ("Read", {"file_path": "workspace/raw/notes.md"}),
    ("Read", {"file_path": "/proj/anon-artifacts/workspace/raw/notes.md"}),
    ("Read", {"file_path": "workspace/out/doc.map.enc"}),
    ("Read", {"file_path": "workspace/out/_registry.registry.enc"}),
    ("Read", {"file_path": "/home/u/.config/anon3pass/master.key"}),
    ("Read", {"file_path": "~/.config/anon3pass/anything.txt"}),
    ("Read", {"file_path": "terms.local.yaml"}),
    ("Edit", {"file_path": "workspace/raw/a.md", "old_string": "a", "new_string": "b"}),
    ("Write", {"file_path": "workspace/raw/a.md", "content": "x"}),
    ("Write", {"file_path": "../x/../workspace/raw/../raw/a.md", "content": "x"}),
    ("Grep", {"pattern": "name", "path": "workspace/raw"}),
    ("Grep", {"pattern": "x", "path": "workspace/out", "glob": "*.map.enc"}),
    ("Glob", {"pattern": "workspace/raw/**"}),
    ("Glob", {"pattern": "**/*.key"}),
])
def test_blocks_sensitive_paths(tool, tin):
    r = run(tool, tin)
    assert r.returncode == 2 and "guard_raw: blocked" in r.stderr


@pytest.mark.parametrize("tool,tin", [
    ("Read", {"file_path": "workspace/out/doc.anon.md"}),
    ("Read", {"file_path": "/proj/anon-artifacts/spec/tech-spec.md"}),
    ("Write", {"file_path": "workspace/out/doc.findings.json", "content": "{}"}),
    ("Grep", {"pattern": "x", "path": "engine/src"}),
    ("Glob", {"pattern": "workspace/out/*.anon.md"}),
])
def test_allows_ordinary_paths(tool, tin):
    r = run(tool, tin)
    assert r.returncode == 0 and r.stderr == ""


@pytest.mark.parametrize("cmd", [
    "bin/anon run workspace/raw/a.md -o workspace/out",
    "./bin/anon verify workspace/out/a.anon.md --map workspace/out/a.map.enc",
    "/proj/anon-artifacts/bin/anon init-key",
])
def test_bash_allows_bin_anon(cmd):
    assert run("Bash", {"command": cmd}).returncode == 0


@pytest.mark.parametrize("cmd", [
    "cat workspace/raw/a.md",
    "bin/anon run a.md; cat ~/.config/anon3pass/master.key",
    "bin/anon run a.md | head",
    "bin/anon run a.md && cat x",
    "bin/anon run a.md > out.txt",
    "bin/anon run $(cat k)",
    "bin/anon run `cat k`",
    "bin/anon run $HOME/x",
    "bin/anon run a.md\ncat k",
    "cat workspace/raw/a.md",
    "python3 -c 'print(open(\"x.map.enc\").read())'",
    "cp terms.local.yaml /tmp/x",
    "",
])
def test_bash_blocks_everything_else(cmd):
    r = run("Bash", {"command": cmd})
    assert r.returncode == 2 and "guard_raw: blocked" in r.stderr


@pytest.mark.parametrize("cmd", ["ls", "bin/anonymous run", "uv run pytest"])
def test_bash_allows_commands_away_from_protected_paths(cmd):
    assert run("Bash", {"command": cmd}).returncode == 0


def test_malformed_input_fails_closed():
    assert run("", {}, raw="not json").returncode == 2
    assert run("", {}, raw="[]").returncode == 2


def test_settings_json_wires_the_hook():
    s = json.loads((HOOK.parents[1] / "settings.json").read_text())
    entry = s["hooks"]["PreToolUse"][0]
    assert set(entry["matcher"].split("|")) == {"Read", "Grep", "Glob", "Edit", "Write", "Bash"}
    assert "guard_raw.py" in entry["hooks"][0]["command"]
