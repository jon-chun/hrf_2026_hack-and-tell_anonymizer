"""anon command line. Output is counts and paths only (invariant I1)."""
from __future__ import annotations

import argparse
import hashlib
import dataclasses
import importlib
import json
import os
import sys
from pathlib import Path

import yaml

from anon3pass import vault

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_LEAK, EXIT_ENV = 0, 1, 2, 3, 4
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
TEXT_SUFFIXES = {".txt", ".md"}


class CliError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


def _mod(name: str):
    try:
        return importlib.import_module(f"anon3pass.{name}")
    except ImportError as exc:
        raise CliError(f"missing dependency: anon3pass.{name} ({type(exc).__name__})", EXIT_ENV)


def _load_cfg(args) -> dict:
    return _mod("config").load_config(args.config)


def _key_path(cfg: dict) -> str:
    return os.path.expanduser(cfg["paths"]["key_file"])


def _keys(cfg: dict) -> tuple[bytes, bytes]:
    try:
        return vault.derive_keys(vault.load_key(_key_path(cfg)))
    except vault.KeyFileError as exc:
        raise CliError(f"{exc}", EXIT_ENV)


def _emit(args, data: dict, text: str) -> None:
    print(json.dumps(data, sort_keys=True) if args.json else text)


def _write_json(path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    vault.write_atomic(path, json.dumps(data, indent=2).encode("utf-8"), 0o600)


def _jsonable(obj):
    return dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else obj


# ---- handlers --------------------------------------------------------------------------
def cmd_init_key(args) -> int:
    cfg = _load_cfg(args)
    path = _key_path(cfg)
    existed = os.path.exists(path)
    try:
        vault.load_or_create_key(path)
    except vault.KeyFileError as exc:
        raise CliError(str(exc), EXIT_ENV)
    _emit(args, {"key_file": path, "created": not existed},
          f"key {'already exists' if existed else 'created'}: {path}")
    return EXIT_OK


def _collect_inputs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.is_file() and f.suffix in TEXT_SUFFIXES)
        elif p.is_file():
            files.append(p)
        else:
            raise CliError(f"input not found: {p}", EXIT_USAGE)
    if not files:
        raise CliError("no .txt or .md inputs found", EXIT_USAGE)
    return files


def _load_extra_terms(path: str | None) -> list[str]:
    if not path:
        return []
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except OSError:
        raise CliError(f"cannot read extra terms file: {path}", EXIT_USAGE)
    return [t if isinstance(t, dict) else str(t) for t in data.get("extra_terms", data.get("terms", []))]


def cmd_run(args) -> int:
    cfg = _load_cfg(args)
    if not os.path.exists(_key_path(cfg)):
        raise CliError(f"key file missing: {_key_path(cfg)}; run `anon init-key` first", EXIT_ENV)
    _keys(cfg)
    pipeline = _mod("pipeline")
    inputs = _collect_inputs(args.inputs)
    extra = _load_extra_terms(args.extra_terms)
    results = []
    for f in inputs:
        try:
            res = pipeline.anonymize_file(f, args.output, cfg, extra)
        except (RuntimeError, ImportError) as exc:
            raise CliError(f"detector unavailable: {type(exc).__name__}", EXIT_ENV)
        results.append(res)
        _emit_run_line(args, res)
    if args.json:
        _emit(args, {"documents": results}, "")
    return EXIT_OK


def _emit_run_line(args, res: dict) -> None:
    if args.json:
        return
    counts = ", ".join(f"{k}={v}" for k, v in sorted(res["stats"]["by_entity"].items())) or "none"
    print(f"{res['doc_id']}: {res['stats']['spans_replaced']} replaced ({counts}) -> {res['anon_path']}")


def cmd_restore(args) -> int:
    cfg = _load_cfg(args)
    _keys(cfg)
    stats = _mod("restore").restore_file(args.anon, args.map, args.output, cfg)
    _emit(args, stats, f"restored ({stats['mode']}): {stats['replaced']} replaced, "
                       f"{stats['unmatched_surrogates']} unmatched -> {stats['out_path']}")
    return EXIT_OK


def cmd_verify(args) -> int:
    cfg = _load_cfg(args)
    enc_key, hmac_key = _keys(cfg)
    docmap = vault.load_docmap(args.map, enc_key)
    anon = Path(args.anon).read_text(encoding="utf-8")
    findings = _mod("verify").verify_text(anon, docmap, cfg, hmac_key)
    if args.output:
        _write_json(args.output, [_jsonable(f) for f in findings])
    threshold = SEVERITY_RANK[cfg["pipeline"].get("fail_on", "high")]
    blocking = [f for f in findings if SEVERITY_RANK.get(f.severity, 3) >= threshold]
    by_sev = {s: sum(f.severity == s for f in findings) for s in SEVERITY_RANK}
    _record_verify(args.anon, anon, by_sev)
    _emit(args, {"findings": len(findings), "blocking": len(blocking), "by_severity": by_sev},
          f"verify: {len(findings)} findings ({by_sev['high']} high, {by_sev['medium']} medium, "
          f"{by_sev['low']} low)")
    return EXIT_LEAK if blocking else EXIT_OK


def _record_verify(anon_path: str, anon: str, by_sev: dict) -> None:
    """Store counts and the text hash in the sibling report. qa-packet and gate read this block."""
    report_path = _mod("qa")._sibling_report(Path(anon_path))
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["verify"] = {**by_sev, "sha256_anon": hashlib.sha256(anon.encode("utf-8")).hexdigest()}
    _write_json(str(report_path), report)


def _known_surrogates(anon_path: str, cfg: dict) -> list[str]:
    """Strings already in the anonymized text, so giving them to the auditor reveals nothing."""
    stem = Path(anon_path).name.split(".anon", 1)[0]
    map_path = Path(anon_path).with_name(f"{stem}.map.enc")
    if not map_path.exists():
        return []
    enc_key, _ = _keys(cfg)
    return sorted({e.surrogate for e in vault.load_docmap(str(map_path), enc_key).entries if e.surrogate})


def cmd_qa_packet(args) -> int:
    cfg = _load_cfg(args)
    packet = _mod("qa").build_packet(args.anon, cfg)
    if not packet.get("verified"):
        raise CliError("no passing `anon verify` is recorded for this exact text; run it first", EXIT_LEAK)
    packet["known_surrogates"] = _known_surrogates(args.anon, cfg)
    _write_json(args.output, packet)
    n = len(packet.get("chunks", []))
    _emit(args, {"chunks": n, "packet": args.output}, f"qa packet: {n} chunks -> {args.output}")
    return EXIT_OK


def cmd_qa_run(args) -> int:
    cfg = _load_cfg(args)
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    result = _mod("qa").run_backend(packet, cfg, args.packet)
    _write_json(args.output, result)
    status = result.get("status", "done")
    _emit(args, {"status": status, "findings_file": args.output}, f"qa run: {status} -> {args.output}")
    return EXIT_OK


def cmd_qa_apply(args) -> int:
    cfg = _load_cfg(args)
    enc_key, _ = _keys(cfg)
    docmap = vault.load_docmap(args.map, enc_key)
    result = _mod("qa").apply_findings(args.findings, docmap, args.output, cfg)
    safe = {k: v for k, v in result.items() if isinstance(v, (int, str, bool, float))}
    _emit(args, {**safe, "terms_file": args.output},
          f"qa apply: {safe.get('added', safe.get('applied', '?'))} terms -> {args.output}")
    return EXIT_OK


def cmd_gate(args) -> int:
    cfg = _load_cfg(args)
    ok, message = _mod("qa").gate(args.report, args.findings, cfg, args.human_reviewed)
    _emit(args, {"passed": ok, "message": message}, message)
    return EXIT_OK if ok else EXIT_LEAK


# ---- parser ----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=argparse.SUPPRESS, help="config YAML (default: packaged config)")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="machine-readable output")
    p = argparse.ArgumentParser(prog="anon", description="anon3pass reversible text anonymizer")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--config", default=None, help="config YAML (default: packaged config)")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, help_):
        sp = sub.add_parser(name, parents=[common], help=help_)
        sp.set_defaults(func=fn)
        return sp

    add("init-key", cmd_init_key, "create the master key")
    sp = add("run", cmd_run, "anonymize files or directories")
    sp.add_argument("inputs", nargs="+")
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--extra-terms", default=None, help="YAML with `terms: [str]`")
    sp = add("restore", cmd_restore, "restore originals")
    sp.add_argument("anon")
    sp.add_argument("--map", required=True)
    sp.add_argument("-o", "--output", required=True)
    sp = add("verify", cmd_verify, "local leak check of an anonymized document")
    sp.add_argument("anon")
    sp.add_argument("--map", required=True)
    sp.add_argument("-o", "--output", default=None, help="write findings JSON")
    sp = add("qa-packet", cmd_qa_packet, "build the Pass 3 packet")
    sp.add_argument("anon")
    sp.add_argument("-o", "--output", required=True)
    sp = add("qa-run", cmd_qa_run, "run the Pass 3 backend")
    sp.add_argument("packet")
    sp.add_argument("-o", "--output", required=True)
    sp = add("qa-apply", cmd_qa_apply, "turn findings into extra terms")
    sp.add_argument("findings")
    sp.add_argument("--map", required=True)
    sp.add_argument("-o", "--output", required=True)
    sp = add("gate", cmd_gate, "pass or fail the document")
    sp.add_argument("report")
    sp.add_argument("--findings", required=True)
    sp.add_argument("--human-reviewed", action="store_true",
                    help="a person has read the flagged passages and accepts them")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    try:
        return args.func(args)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code
    except vault.VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:  # never echo exception text: it could carry document content
        print(f"error: {type(exc).__name__}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
