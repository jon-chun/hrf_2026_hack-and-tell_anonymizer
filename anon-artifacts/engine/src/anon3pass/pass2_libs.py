"""Pass 2: library detection (Presidio/spaCy NER, optional gliner2 and opf, secret scanners).

Invariant I1: nothing in this module prints or logs a matched value.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import shutil
import subprocess
from functools import lru_cache

from .types import Entity, Span

for _name in ("presidio-analyzer", "presidio_analyzer", "spacy", "detect_secrets", "gliner2"):
    logging.getLogger(_name).setLevel(logging.CRITICAL)

NER_SOURCE = "pass2.presidio"
SECRETS_SOURCE = "pass2.secrets"
CHUNK_OVERLAP = 500

# Presidio names -> our entities. NER names come from spaCy; the rest are pattern recognizers.
_NER_MAP = {"PERSON": Entity.PERSON, "ORGANIZATION": Entity.ORGANIZATION, "LOCATION": Entity.LOCATION}
_PATTERN_MAP = {
    "EMAIL_ADDRESS": Entity.EMAIL, "PHONE_NUMBER": Entity.PHONE, "CREDIT_CARD": Entity.CREDIT_CARD,
    "IBAN_CODE": Entity.IBAN, "IP_ADDRESS": Entity.IP_ADDRESS, "URL": Entity.URL,
    "US_SSN": Entity.SSN, "US_BANK_NUMBER": Entity.BANK_ACCOUNT, "US_PASSPORT": Entity.ID_NUMBER,
    "US_DRIVER_LICENSE": Entity.ID_NUMBER, "US_ITIN": Entity.ID_NUMBER, "UK_NHS": Entity.ID_NUMBER,
    "MEDICAL_LICENSE": Entity.ID_NUMBER,
}  # DATE_TIME is deliberately absent: dates belong to Pass 1

_SPACY_LABELS = {"PERSON": "PERSON", "PER": "PERSON", "ORG": "ORGANIZATION",
                 "GPE": "LOCATION", "LOC": "LOCATION", "FAC": "LOCATION"}


# ================================================================== NER: Presidio + spaCy


@lru_cache(maxsize=4)
def _analyzer(model: str):
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    conf = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model}],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": _SPACY_LABELS,
            "low_score_entity_names": [],
            "labels_to_ignore": [],
        },
    }
    nlp = NlpEngineProvider(nlp_configuration=conf).create_engine()
    return AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])


def _max_length(analyzer) -> int:
    return int(analyzer.nlp_engine.nlp["en"].max_length)


def _chunk_bounds(n: int, max_len: int, overlap: int = CHUNK_OVERLAP) -> list[tuple[int, int, int, int]]:
    """(own_start, own_end, read_start, read_end) per chunk. Own ranges partition the text; each
    chunk is read with `overlap` extra characters on both sides so entities at a seam stay whole."""
    own = max(1, max_len - 2 * overlap)
    out = []
    for s in range(0, n, own):
        e = min(n, s + own)
        out.append((s, e, max(0, s - overlap), min(n, e + overlap)))
    return out


def _presidio_spans(text: str, cfg: dict) -> list[Span]:
    ner = cfg["pass2_libraries"]["ner"]
    wanted = set(ner.get("entities", []))
    names = [p for p, e in _NER_MAP.items() if e.value in wanted]
    if cfg["pass2_libraries"].get("presidio_pattern_recognizers"):
        names += list(_PATTERN_MAP)
    if not names:
        return []
    analyzer = _analyzer(ner["spacy_model"])
    table = {**_NER_MAP, **_PATTERN_MAP}
    out: list[Span] = []
    for own_s, own_e, rs, re_ in _chunk_bounds(len(text), _max_length(analyzer)):
        results = analyzer.analyze(text=text[rs:re_], language="en", entities=names,
                                   score_threshold=float(ner["score_threshold"]))
        for r in results:
            start, end = r.start + rs, r.end + rs
            if not own_s <= start < own_e:
                continue  # starts in another chunk's own range; that chunk reports it
            out.append(Span(start, end, text[start:end], table[r.entity_type], NER_SOURCE, float(r.score)))
    return out


# ================================================================== NER: optional adapters


@lru_cache(maxsize=2)
def _gliner2_model(name: str):  # untested: optional dependency not installed
    try:
        from gliner2 import GLiNER2
    except ImportError as exc:
        raise RuntimeError("ner.engine is gliner2 but the gliner2 package is not installed") from exc
    return GLiNER2.from_pretrained(name)


def _gliner2_spans(text: str, cfg: dict) -> list[Span]:  # untested: optional dependency not installed
    ner = cfg["pass2_libraries"]["ner"]
    model = _gliner2_model(ner["gliner2_model"])
    labels = {e.lower(): Entity(e) for e in ner.get("entities", [])}
    res = model.extract_entities(text, list(labels), threshold=0.5, include_confidence=True, include_spans=True)
    out = []
    for label, items in res.get("entities", {}).items():
        for it in items:
            conf = float(it.get("confidence", 1.0))
            if label in labels and conf >= float(ner["score_threshold"]):
                out.append(Span(it["start"], it["end"], text[it["start"]:it["end"]], labels[label],
                                "pass2.gliner2", conf))
    return out


def _opf_spans(text: str, cfg: dict) -> list[Span]:  # untested: optional dependency not installed
    exe = shutil.which("opf")
    if exe is None:
        raise RuntimeError("ner.engine is opf but the opf command is not on PATH")
    ner = cfg["pass2_libraries"]["ner"]
    cmd = [exe, "--device", "cpu", "--format", "json"]
    if ner.get("opf_checkpoint"):
        cmd += ["--checkpoint", str(ner["opf_checkpoint"])]
    proc = subprocess.run(cmd, input=text, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"opf exited with status {proc.returncode}")
    wanted = set(ner.get("entities", []))
    out = []
    for it in json.loads(proc.stdout):
        ent = str(it.get("label", "")).upper()
        if ent in wanted:
            out.append(Span(it["start"], it["end"], text[it["start"]:it["end"]], Entity(ent), "pass2.opf",
                            float(it.get("score", 1.0))))
    return out


def _ner_spans(text: str, cfg: dict) -> list[Span]:
    engine = cfg["pass2_libraries"]["ner"]["engine"]
    if engine == "presidio_spacy":
        return _presidio_spans(text, cfg)
    if engine == "gliner2":
        return _gliner2_spans(text, cfg)
    if engine == "opf":
        return _opf_spans(text, cfg)
    return []


# ================================================================== secrets


def _line_starts(text: str) -> list[tuple[int, str]]:
    out, pos = [], 0
    for line in text.splitlines(keepends=True):
        out.append((pos, line))
        pos += len(line)
    return out


@lru_cache(maxsize=1)
def _ds_plugins() -> tuple:
    """detect-secrets regex plugins (line scanners with analyze_string)."""
    from detect_secrets.core.plugins.util import get_mapping_from_secret_type_to_class
    from detect_secrets.plugins.base import RegexBasedDetector

    skip = {"IPPublicDetector", "PrivateKeyDetector"}  # IPs are Pass 1; PEM blocks are handled whole below
    return tuple(cls() for cls in get_mapping_from_secret_type_to_class().values()
                 if issubclass(cls, RegexBasedDetector) and cls.__name__ not in skip)


def _ds_entity(plugin) -> Entity:
    return Entity.TOKEN if "Jwt" in type(plugin).__name__ or "Token" in type(plugin).__name__ else Entity.API_KEY


def _detect_secrets_lib(text: str) -> list[Span]:
    """Run each plugin's own regexes (its `denylist`) so match offsets are exact. The credential
    group is used when the plugin captures one (e.g. the password in a basic-auth URL); a short
    capture is a mere prefix (e.g. `ghp`), so the whole match is used instead."""
    out = []
    for plugin in _ds_plugins():
        ent = _ds_entity(plugin)
        for rx in plugin.denylist:
            for m in rx.finditer(text):
                g = m.lastindex or 0
                if g and len(m.group(g)) < 8:
                    g = 0
                if m.end(g) > m.start(g):
                    out.append(Span(m.start(g), m.end(g), m.group(g), ent, SECRETS_SOURCE, 0.9))
    return out


_PH = re.compile(r"^\[[A-Z_]+_\d+\]$")  # our own placeholders are never re-detected
_VAL = r"""(?:"([^"\n]{1,200})"|'([^'\n]{1,200})'|([^\s"',;]+))"""
_TOK = r"[A-Za-z0-9._~+/=-]"

# (regex, entity or callable(match)->entity, min value length). Group 1.. hold the value; whole match when none.
_CRED_RULES: list[tuple[re.Pattern, object, int]] = [
    (re.compile(rf"(?<![A-Za-z0-9_])(?:password|passwd|pwd|passphrase)[\"']?[ \t]*[:=][ \t]*{_VAL}", re.I),
     Entity.PASSWORD, 1),
    (re.compile(rf"(?<![A-Za-z0-9])([A-Za-z_]*(?:api_?key|secret|token)[A-Za-z_]*)[\"']?[ \t]*[:=][ \t]*{_VAL}", re.I),
     lambda m: (Entity.API_KEY if "key" in m.group(1).lower() else
                Entity.TOKEN if "token" in m.group(1).lower() else Entity.SECRET), 12),
    (re.compile(rf"\bAuthorization[\"']?[ \t]*[:=][ \t]*(?:Bearer|Basic|Token)[ \t]+({_TOK}{{8,}})", re.I),
     Entity.TOKEN, 8),
    (re.compile(rf"\bBearer[ \t]+({_TOK}{{16,}})", re.I), Entity.TOKEN, 16),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), Entity.TOKEN, 1),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY(?: BLOCK)?-----(?:[\s\S]*?-----END [A-Z ]*PRIVATE KEY(?: BLOCK)?-----"
                r"|(?:\s*[A-Za-z0-9+/=]{16,})*)"), Entity.PRIVATE_KEY, 1),
    (re.compile(r"\b(?:password|passwd|pwd|pw|passcode|passphrase|door[ \t]+code|pin)\b[ \t]*(?:=|:|is)?[ \t]*[\x22\x27\u201c]?(?=[^\s\x22\x27\u201d]*[\d#!$%&*])([^\s\x22\x27\u201d]+)", re.I),
     Entity.PASSWORD, 3),
    (re.compile(r"(?<![A-Za-z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}"), Entity.API_KEY, 1),
    (re.compile(r"(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{22,})"), Entity.TOKEN, 1),
    (re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}"), Entity.TOKEN, 1),
    (re.compile(r"(?<![A-Za-z0-9_-])sk-ant-[A-Za-z0-9_-]{20,}"), Entity.API_KEY, 1),
    (re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_-]{20,}"), Entity.API_KEY, 1),
    (re.compile(r"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}(?![A-Za-z0-9_-])"), Entity.API_KEY, 1),
    (re.compile(r"(?<![A-Za-z0-9_])[sr]k_live_[0-9A-Za-z]{16,}"), Entity.API_KEY, 1),
]


def _credential_rules(text: str) -> list[Span]:
    out = []
    for rx, ent, min_len in _CRED_RULES:
        for m in rx.finditer(text):
            grp = _value_group(m)
            s, e = (m.start(grp), m.end(grp)) if grp else (m.start(), m.end())
            if e - s < min_len or _PH.match(text[s:e]):
                continue
            kind = ent(m) if callable(ent) else ent
            out.append(Span(s, e, text[s:e], kind, SECRETS_SOURCE, 1.0))
    return out


def _value_group(m: re.Match) -> int:
    """Index of the last group that participated (the credential value), or 0 for the whole match."""
    for i in range(len(m.groups()), 0, -1):
        if m.group(i) is not None:
            return i
    return 0


def shannon(s: str) -> float:
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def _entropy_tokens(text: str, min_entropy: float, min_length: int) -> list[Span]:
    out = []
    for m in re.finditer(rf"[A-Za-z0-9+/=_-]{{{int(min_length)},}}", text):
        tok = m.group()
        if not (any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok)):
            continue
        if _PH.match(tok) or shannon(tok) < min_entropy:
            continue
        out.append(Span(m.start(), m.end(), tok, Entity.SECRET, SECRETS_SOURCE, 0.6))
    return out


def _gitleaks_binary(mode) -> str | None:
    if mode is False:
        return None
    exe = shutil.which("gitleaks") or ("/opt/homebrew/bin/gitleaks" if os.path.exists("/opt/homebrew/bin/gitleaks") else None)
    if exe is None and mode is True:
        raise RuntimeError("secrets.gitleaks is true but the gitleaks binary was not found")
    return exe


def _gitleaks_entity(rule_id: str) -> Entity:
    rid = rule_id.lower()
    if "private-key" in rid:
        return Entity.PRIVATE_KEY
    if "jwt" in rid or "token" in rid:
        return Entity.TOKEN
    return Entity.API_KEY


def _gitleaks(text: str, exe: str) -> list[Span]:
    cmd = [exe, "stdin", "--report-format", "json", "--report-path", "-", "--no-banner",
           "--exit-code", "0", "--log-level", "error"]
    proc = subprocess.run(cmd, input=text, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    starts = [p for p, _ in _line_starts(text)] or [0]
    out = []
    for f in json.loads(proc.stdout):
        secret = f.get("Secret") or ""
        line = max(1, int(f.get("StartLine", 1))) - 1
        i = text.find(secret, starts[min(line, len(starts) - 1)]) if secret else -1
        if i != -1:
            out.append(Span(i, i + len(secret), secret, _gitleaks_entity(str(f.get("RuleID", ""))),
                            SECRETS_SOURCE, 0.9))
    return out


def _drop_contained(spans: list[Span]) -> list[Span]:
    """Remove duplicates and spans wholly inside a longer secret span."""
    ordered = sorted(set(spans), key=lambda s: (s.start, -(s.end - s.start), -s.score, s.entity == Entity.SECRET))
    out: list[Span] = []
    reach = -1  # furthest end kept so far
    for s in ordered:
        if s.end <= reach:
            continue
        out.append(s)
        reach = s.end
    return out


def detect_secrets_only(text: str, cfg: dict) -> list[Span]:
    sec = cfg["pass2_libraries"]["secrets"]
    spans: list[Span] = []
    if sec.get("detect_secrets"):
        spans += _detect_secrets_lib(text)
    if sec.get("credential_rules"):
        spans += _credential_rules(text)
    if sec.get("entropy_min"):
        spans += _entropy_tokens(text, float(sec["entropy_min"]), int(sec.get("entropy_min_length", 24)))
    exe = _gitleaks_binary(sec.get("gitleaks", "auto"))
    if exe:
        spans += _gitleaks(text, exe)
    return _drop_contained([s for s in spans if not _PH.match(s.text)])


# ================================================================== public API


def detect(text: str, cfg: dict) -> list[Span]:
    spans = _ner_spans(text, cfg) + detect_secrets_only(text, cfg)
    return sorted(spans, key=lambda s: (s.start, s.end, s.source))
