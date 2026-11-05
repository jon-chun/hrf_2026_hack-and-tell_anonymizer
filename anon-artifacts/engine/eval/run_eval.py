#!/usr/bin/env python3
"""Ablation harness for anon3pass on 8 small SYNTHETIC fixtures.

Honest label: this is a smoke-level check on invented, small documents. It is not a
benchmark and says nothing about performance on real data. Everything here is fictional,
so printing values is harmless.

Usage (from engine/):  uv run python eval/run_eval.py [--configs pass1,pass2,pass1+2]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z_]*_\d+\]")
SECRET_ENTITIES = {"API_KEY", "PASSWORD", "PRIVATE_KEY", "TOKEN", "SECRET"}

# name -> (pipeline.passes, whether the gold deny_terms are supplied)
CONFIGS = {
    "pass1": (["patterns"], True),
    "pass2": (["libraries"], False),
    "pass1+2": (["patterns", "libraries"], True),
    "pass1+2-noterms": (["patterns", "libraries"], False),
}


def contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def contains_word(haystack: str, needle: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", haystack, re.IGNORECASE) is not None


def mask_secrets(original: str, gold: dict) -> str:
    for item in gold["must_not_appear"]:
        if item["entity"] in SECRET_ENTITIES:
            original = original.replace(item["value"], "\0")
    return original


def run_config(name: str, cfg0: dict, gold: dict, fixtures_dir: Path) -> dict:
    from anon3pass.pipeline import anonymize_text
    from anon3pass.restore import restore_text

    passes, use_terms = CONFIGS[name]
    cfg = copy.deepcopy(cfg0)
    cfg["pipeline"]["passes"] = passes
    key = os.urandom(32)            # temporary key, never written to disk
    registry: dict = {}
    anonymize_text("Warm-up text for model loading.", "warmup", cfg, key, {}, {"deny": [], "allow": []})

    leaked_by_entity: dict[str, list[int]] = defaultdict(lambda: [0, 0])   # [leaked, total]
    keep_total = keep_lost = 0
    exact = modulo = 0
    seconds = 0.0
    per_doc = {}
    for fname, g in gold["fixtures"].items():
        text = (fixtures_dir / fname).read_text(encoding="utf-8")
        terms = {"deny": [{"term": d["term"], "entity": d["entity"]} for d in g["deny_terms"]] if use_terms else [],
                 "allow": []}
        t0 = time.perf_counter()
        anon, docmap, _stats = anonymize_text(text, Path(fname).stem, cfg, key, registry, terms)
        seconds += time.perf_counter() - t0

        leaks = []
        for item in g["must_not_appear"]:
            leaked_by_entity[item["entity"]][1] += 1
            if contains_word(anon, item["value"]):
                leaked_by_entity[item["entity"]][0] += 1
                leaks.append(item["value"])
        lost = [w for w in g["must_keep"] if not contains_word(anon, w)]
        keep_total += len(g["must_keep"])
        keep_lost += len(lost)

        restored, _ = restore_text(anon, docmap)
        is_exact = restored == text
        is_modulo = PLACEHOLDER_RE.sub("\0", restored) == mask_secrets(text, g)
        exact += is_exact
        modulo += is_modulo
        per_doc[fname] = {"leaked": leaks, "over_redacted": lost, "roundtrip_exact": is_exact,
                          "roundtrip_modulo_secrets": is_modulo}

    total = sum(t for _, t in leaked_by_entity.values())
    leaked = sum(l for l, _ in leaked_by_entity.values())
    return {
        "config": name, "passes": passes, "deny_terms": use_terms,
        "leaked": leaked, "gold_values": total,
        "leak_rate": round(leaked / total, 4) if total else 0.0,
        "leaked_by_entity": {e: {"leaked": l, "total": t} for e, (l, t) in sorted(leaked_by_entity.items())},
        "over_redaction_rate": round(keep_lost / keep_total, 4) if keep_total else 0.0,
        "over_redacted_items": keep_lost, "must_keep_items": keep_total,
        "roundtrip_exact": f"{exact}/{len(gold['fixtures'])}",
        "roundtrip_modulo_secrets": f"{modulo}/{len(gold['fixtures'])}",
        "seconds": round(seconds, 2),
        "documents": per_doc,
    }


def table(results: list[dict]) -> str:
    entities = sorted({e for r in results for e in r["leaked_by_entity"]})
    head = ["config", "leaked/gold", "over-redaction", "round-trip exact", "round-trip excl. secrets", "seconds"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in results:
        lines.append(f"| {r['config']} | {r['leaked']}/{r['gold_values']} | {r['over_redaction_rate']:.1%} | "
                     f"{r['roundtrip_exact']} | {r['roundtrip_modulo_secrets']} | {r['seconds']} |")
    lines += ["", "Leaked gold values by entity (leaked/total):", "",
              "| entity | " + " | ".join(r["config"] for r in results) + " |",
              "|---|" + "---|" * len(results)]
    for e in entities:
        cells = []
        for r in results:
            d = r["leaked_by_entity"].get(e)
            cells.append(f"{d['leaked']}/{d['total']}" if d else "-")
        lines.append(f"| {e} | " + " | ".join(cells) + " |")
    lines += ["", "Synthetic and small (8 invented documents): a smoke check, not a benchmark."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--configs", default="pass1,pass2,pass1+2",
                    help=f"comma list from: {', '.join(CONFIGS)}")
    ap.add_argument("--config", default=None, help="base config YAML (default: packaged defaults)")
    ap.add_argument("--out", default=str(HERE / "results.json"))
    args = ap.parse_args()
    names = [n.strip() for n in args.configs.split(",") if n.strip()]
    unknown = [n for n in names if n not in CONFIGS]
    if unknown:
        ap.error(f"unknown config(s): {unknown}")

    from anon3pass.config import load_config

    cfg0 = load_config(args.config)
    gold = yaml.safe_load((HERE / "gold.yaml").read_text(encoding="utf-8"))
    results = [run_config(n, cfg0, gold, HERE / "fixtures") for n in names]
    print(table(results))
    Path(args.out).write_text(json.dumps(
        {"note": "synthetic and small; not a benchmark", "results": results}, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
