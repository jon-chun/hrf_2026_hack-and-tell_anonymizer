"""Configuration loader: YAML merged over packaged defaults (engine/config.yaml)."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

from .types import Entity

ACTIONS = {"surrogate", "generalize", "redact", "keep"}
BACKENDS = {"claude_code", "anthropic", "ollama", "none"}
NER_ENGINES = {"presidio_spacy", "gliner2", "opf", "none"}
PASSES = {"patterns", "libraries", "agent_qa"}
FAIL_ON = {"high", "medium", "low"}


def default_config_path() -> Path:
    """Walk up from this module to the engine/ directory holding config.yaml."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("packaged config.yaml not found above anon3pass/")


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, val in over.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def _read_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return data


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def validate(cfg: dict) -> None:
    valid = {e.value for e in Entity}
    pipe = cfg.get("pipeline", {})
    _check(isinstance(pipe.get("passes"), list) and set(pipe["passes"]) <= PASSES,
           f"pipeline.passes must be a list drawn from {sorted(PASSES)}")
    _check(pipe.get("fail_on") in FAIL_ON, f"pipeline.fail_on must be one of {sorted(FAIL_ON)}")
    _check(isinstance(pipe.get("max_qa_iterations"), int) and pipe["max_qa_iterations"] >= 0,
           "pipeline.max_qa_iterations must be a non-negative integer")

    p2 = cfg.get("pass2_libraries", {})
    ner = p2.get("ner", {})
    _check(ner.get("engine") in NER_ENGINES, f"pass2_libraries.ner.engine must be one of {sorted(NER_ENGINES)}")
    thr = ner.get("score_threshold")
    _check(isinstance(thr, (int, float)) and 0 <= thr <= 1,
           "pass2_libraries.ner.score_threshold must be between 0 and 1")
    for name in ner.get("entities", []):
        _check(name in valid, f"pass2_libraries.ner.entities: unknown entity {name!r}")
    gl = p2.get("secrets", {}).get("gitleaks")
    _check(gl == "auto" or isinstance(gl, bool),
           "pass2_libraries.secrets.gitleaks must be auto, true or false")

    p1 = cfg.get("pass1_patterns", {})
    fthr = p1.get("fuzzy", {}).get("threshold")
    _check(isinstance(fthr, (int, float)) and 0 <= fthr <= 100, "pass1_patterns.fuzzy.threshold must be 0-100")
    for rule in p1.get("custom_rules") or []:
        _check(isinstance(rule, dict) and {"name", "regex", "entity"} <= set(rule),
               "pass1_patterns.custom_rules entries need name, regex, entity")
        _check(rule["entity"] in valid, f"custom rule {rule.get('name')!r}: unknown entity")

    _check(cfg.get("pass3_agent_qa", {}).get("backend") in BACKENDS,
           f"pass3_agent_qa.backend must be one of {sorted(BACKENDS)}")

    for ent, action in cfg.get("entity_policy", {}).items():
        _check(ent in valid, f"entity_policy: unknown entity {ent!r}")
        _check(action in ACTIONS, f"entity_policy.{ent}: action must be one of {sorted(ACTIONS)}")


def load_config(path: str | None) -> dict:
    cfg = _read_yaml(default_config_path())
    if path:
        cfg = _merge(cfg, _read_yaml(Path(path).expanduser()))
    for key in ("key_file", "terms_file"):
        val = cfg.get("paths", {}).get(key)
        if val:
            cfg["paths"][key] = str(Path(val).expanduser())
    validate(cfg)
    return cfg


def load_terms(cfg: dict) -> dict:
    """Return {"deny": [{"term", "entity"}], "allow": [str]}; a missing file yields empty lists."""
    out: dict = {"deny": [], "allow": []}
    tf = cfg.get("paths", {}).get("terms_file")
    if not tf or not Path(tf).expanduser().is_file():
        return out
    data = _read_yaml(Path(tf).expanduser())
    valid = {e.value for e in Entity}
    for item in data.get("deny") or []:
        if isinstance(item, str):
            term, ent = item, "CUSTOM"
        else:
            term, ent = item.get("term"), item.get("entity", "CUSTOM")
        _check(isinstance(term, str) and term.strip() != "", "terms.deny: each entry needs a term")
        _check(ent in valid, "terms.deny: unknown entity in an entry")
        out["deny"].append({"term": term, "entity": ent})
    for item in data.get("allow") or []:
        _check(isinstance(item, str), "terms.allow: entries must be strings")
        out["allow"].append(item)
    return out
