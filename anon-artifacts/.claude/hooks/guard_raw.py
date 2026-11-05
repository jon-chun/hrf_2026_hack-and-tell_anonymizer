#!/usr/bin/env python3
"""PreToolUse hook: keep raw inputs, vault files and keys away from the model.

Reads the hook JSON on stdin. Exit 0 allows the call; exit 2 blocks it and sends the
stderr message to the model. This is best-effort defence, NOT a sandbox: it matches
path strings and a narrow Bash allowlist, and cannot see what a permitted program does.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

BLOCKED_SUFFIXES = (".map.enc", ".registry.enc", ".key")
BLOCKED_NAMES = ("terms.local.yaml",)
BLOCKED_FRAGMENTS = ("workspace/raw", ".config/anon3pass")
SHELL_META = re.compile(r"[;|&<>`$\n\r\\]")
PATH_FIELDS = ("file_path", "path", "pattern", "glob", "notebook_path")


BASH_MARKS = ("workspace/raw", "raw/", ".map.enc", ".registry.enc", ".key", "terms.local", ".config/anon3pass", "master.key")


def _forms(value: str, cwd: str) -> list[str]:
    """The raw string plus its expanded, absolute and real-path forms (slash-normalized)."""
    expanded = os.path.expanduser(value)
    absolute = expanded if os.path.isabs(expanded) else os.path.join(cwd, expanded)
    forms = {value, expanded, os.path.normpath(absolute)}
    try:
        forms.add(os.path.realpath(absolute))
    except OSError:
        pass
    return [f.replace("\\", "/") for f in forms]


def blocked_path(value: str, cwd: str) -> str | None:
    for form in _forms(value, cwd):
        low = form.lower()
        base = os.path.basename(low.rstrip("/"))
        if any(frag in low for frag in BLOCKED_FRAGMENTS):
            return "workspace/raw or ~/.config/anon3pass"
        if base in BLOCKED_NAMES or any(base.endswith(s) for s in BLOCKED_SUFFIXES):
            return "a key, vault or local terms file"
    return None


def check_bash(command: str) -> str | None:
    """Block shell access to protected paths. bin/anon may touch them, but only as a plain command."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "command could not be parsed"
    if not tokens:
        return "empty command"
    first = tokens[0]
    is_anon = first in ("bin/anon", "./bin/anon") or (os.path.isabs(first) and first.endswith("/bin/anon"))
    if is_anon:
        return "shell metacharacters are not allowed with bin/anon" if SHELL_META.search(command) else None
    lowered = command.lower()
    if any(mark in lowered for mark in BASH_MARKS):
        return "this command names a protected path; only a plain bin/anon command may do that"
    return None


def decide(payload: dict) -> str | None:
    """Return a reason to block, or None to allow."""
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool == "Bash":
        return check_bash(str(tin.get("command", "")))
    for field in PATH_FIELDS:
        value = tin.get(field)
        if isinstance(value, str) and value:
            hit = blocked_path(value, cwd)
            if hit:
                return f"{tool} on {hit} ({field})"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("not an object")
    except ValueError:
        print("guard_raw: unreadable hook input; blocking (fail closed).", file=sys.stderr)
        return 2
    reason = decide(payload)
    if reason:
        print(f"guard_raw: blocked. {reason}. Raw inputs, vault files and keys are for the "
              "bin/anon CLI only; never read them yourself. (Best-effort guard, not a sandbox.)",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
