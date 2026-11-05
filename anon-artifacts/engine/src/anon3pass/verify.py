"""Pass 3a: local, deterministic leak check of an anonymized document (no LLM).

Findings carry offsets into the ANONYMIZED text and keyed fingerprints. They never
carry an original value, and `quote` stays empty (offsets are enough to locate a hit).
"""
from __future__ import annotations

import importlib
import math
import re
from collections import Counter

from .types import SECRET_ENTITIES, DocMap, LeakFinding, MapEntry

PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z_]*_\d+\]")
NAME_ENTITIES = {"PERSON", "ORGANIZATION", "LOCATION", "ADDRESS"}
MEDIUM_PATTERN_ENTITIES = {"DATE", "AGE", "URL", "USERNAME"}
SHORT = 4          # originals shorter than this only flag as whole words
TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_\-]+")
WORD_RE = re.compile(r"\w+", re.UNICODE)


def _mask(text: str, docmap: DocMap, keep_placeholders: bool = False) -> str:
    """Blank out known surrogates and placeholders, keeping offsets stable."""
    blank = list(text)

    def wipe(start: int, end: int) -> None:
        for i in range(start, end):
            blank[i] = " "

    if not keep_placeholders:
        for m in PLACEHOLDER_RE.finditer(text):
            wipe(m.start(), m.end())
    surrogates = sorted({e.surrogate for e in docmap.entries if e.surrogate and not (keep_placeholders and PLACEHOLDER_RE.fullmatch(e.surrogate))}, key=len, reverse=True)
    for s in surrogates:
        for m in re.finditer(re.escape(s), text):
            wipe(m.start(), m.end())
    return "".join(blank)


def _whole_word(value: str, flags: int = 0) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(value) + r"(?!\w)", flags)


def _digit_pattern(value: str) -> re.Pattern | None:
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7:
        return None
    sep = r"[\s\-.()/]*"
    return re.compile(r"(?<!\d)" + sep.join(digits) + r"(?!\d)")


def _entropy(token: str) -> float:
    counts = Counter(token)
    n = len(token)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


class _Collector:
    """De-duplicates findings that cover the same offsets."""

    def __init__(self) -> None:
        self.items: list[LeakFinding] = []
        self._ranges: list[tuple[int, int]] = []

    def covered(self, start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in self._ranges)

    def add(self, finding: LeakFinding) -> None:
        self.items.append(finding)
        self._ranges.append((finding.anon_start, finding.anon_end))


def _check_originals(masked: str, entries: list[MapEntry], cfg: dict, out: _Collector) -> None:
    fuzzy_cfg = cfg.get("pass1_patterns", {}).get("fuzzy", {})
    fuzzy_on = bool(fuzzy_cfg.get("enabled", True))
    threshold = float(fuzzy_cfg.get("threshold", 88))
    min_len = int(fuzzy_cfg.get("min_length", 5))

    seen: set[tuple[str, str]] = set()
    for e in entries:
        orig = e.original
        if not orig or not orig.strip() or (orig, e.fingerprint) in seen:
            continue
        seen.add((orig, e.fingerprint))
        orig = orig.strip()
        alnum = bool(re.search(r"\w", orig))

        # exact, then case-insensitive / whitespace-normalized
        if len(orig) < SHORT:
            exact_re = _whole_word(orig)
            norm_re = _whole_word(orig, re.IGNORECASE)
        else:
            exact_re = _whole_word(orig)
            norm_re = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(p) for p in orig.split()) + r"(?!\w)", re.IGNORECASE)
        for m in exact_re.finditer(masked):
            if not out.covered(m.start(), m.end()):
                out.add(_vault_finding("exact_original", e, "high", m.start(), m.end(),
                                       "an original value remains in the anonymized text"))
        for m in norm_re.finditer(masked):
            if not out.covered(m.start(), m.end()):
                out.add(_vault_finding("normalized_original", e, "high", m.start(), m.end(),
                                       "an original value remains (case or spacing differs)"))
        dp = _digit_pattern(orig)
        if dp:
            for m in dp.finditer(masked):
                if not out.covered(m.start(), m.end()):
                    out.add(_vault_finding("normalized_original", e, "high", m.start(), m.end(),
                                           "an original number remains (separators differ)"))

        # fuzzy: near-misses of names
        if fuzzy_on and e.entity in NAME_ENTITIES and alnum and len(orig) >= min_len:
            _fuzzy(masked, e, orig, threshold, fuzzy_cfg, out)

        # name parts: each word of a multi-word person original, whole word, 4+ chars
        if e.entity == "PERSON" and " " in orig:
            for part in {p for p in re.findall(r"\w+", orig) if len(p) >= SHORT}:
                for m in _whole_word(part, re.IGNORECASE).finditer(masked):
                    if not out.covered(m.start(), m.end()):
                        out.add(_vault_finding("normalized_original", e, "medium", m.start(), m.end(),
                                               "a part of an original name remains"))


def _fuzzy(masked: str, e: MapEntry, orig: str, threshold: float, fuzzy_cfg: dict, out: _Collector) -> None:
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return
    words = [(m.start(), m.end(), m.group()) for m in WORD_RE.finditer(masked)]
    n = len(orig.split())
    extra = int(fuzzy_cfg.get("max_edit_window", 1))
    target = orig.lower()
    for size in range(max(1, n - extra), n + extra + 1):
        for i in range(0, len(words) - size + 1):
            window = words[i:i + size]
            start, end = window[0][0], window[-1][1]
            if out.covered(start, end):
                continue
            cand = masked[start:end].lower()
            if abs(len(cand) - len(target)) > max(2, len(target) // 4):
                continue
            if fuzz.ratio(cand, target) >= threshold:
                out.add(_vault_finding("fuzzy_original", e, "medium", start, end,
                                       "text close to an original name remains"))


def _vault_finding(category: str, e: MapEntry, severity: str, start: int, end: int, reason: str) -> LeakFinding:
    return LeakFinding(category=category, entity=e.entity, severity=severity, anon_start=start,
                       anon_end=end, fingerprint=e.fingerprint, quote="", reason=reason)


def _fp(hmac_key: bytes, value: str) -> str:
    vault = importlib.import_module("anon3pass.vault")
    return vault.fingerprint(hmac_key, value)


def _skip_policy(cfg: dict, entity: str) -> bool:
    return cfg.get("entity_policy", {}).get(str(entity)) == "keep"


def _check_patterns(masked: str, cfg: dict, hmac_key: bytes, out: _Collector) -> None:
    pass1 = importlib.import_module("anon3pass.pass1_patterns")
    for sp in pass1.detect(masked, cfg, {"deny": [], "allow": []}):
        entity = str(sp.entity)
        if _skip_policy(cfg, entity) or out.covered(sp.start, sp.end):
            continue
        sev = "medium" if entity in MEDIUM_PATTERN_ENTITIES else "high"
        category = "secret" if sp.entity in SECRET_ENTITIES else "pattern"
        out.add(LeakFinding(category=category, entity=entity, severity=sev, anon_start=sp.start,
                            anon_end=sp.end, fingerprint=_fp(hmac_key, masked[sp.start:sp.end]),
                            reason=f"{entity} pattern matched in anonymized text ({sp.source})"))


def _check_secrets(masked: str, cfg: dict, hmac_key: bytes, out: _Collector) -> None:
    pass2 = importlib.import_module("anon3pass.pass2_libs")
    # Credential rules read the word after "password =". Placeholders stay visible here, so that
    # word is the placeholder itself and not whatever follows a blanked region.
    for sp in pass2.detect_secrets_only(masked, cfg):
        if out.covered(sp.start, sp.end) or PLACEHOLDER_RE.search(masked[sp.start:sp.end]):
            continue
        out.add(LeakFinding(category="secret", entity=str(sp.entity), severity="high",
                            anon_start=sp.start, anon_end=sp.end,
                            fingerprint=_fp(hmac_key, masked[sp.start:sp.end]),
                            reason=f"secret detected in anonymized text ({sp.source})"))


def _check_entropy(masked: str, cfg: dict, hmac_key: bytes, out: _Collector) -> None:
    sec = cfg.get("pass2_libraries", {}).get("secrets", {})
    min_entropy = float(sec.get("entropy_min", 4.0))
    min_len = int(sec.get("entropy_min_length", 24))
    for m in TOKEN_RE.finditer(masked):
        tok = m.group()
        if len(tok) < min_len or out.covered(m.start(), m.end()):
            continue
        if _entropy(tok) >= min_entropy:
            out.add(LeakFinding(category="entropy", entity="SECRET", severity="medium",
                                anon_start=m.start(), anon_end=m.end(),
                                fingerprint=_fp(hmac_key, tok),
                                reason="high-entropy string in anonymized text"))


def verify_text(anon: str, docmap: DocMap, cfg: dict, hmac_key: bytes) -> list[LeakFinding]:
    """Return leak findings for `anon`. Known surrogates and placeholders are masked first."""
    masked = _mask(anon, docmap)
    out = _Collector()
    _check_originals(masked, docmap.entries, cfg, out)
    _check_patterns(masked, cfg, hmac_key, out)
    _check_secrets(_mask(anon, docmap, keep_placeholders=True), cfg, hmac_key, out)
    _check_entropy(masked, cfg, hmac_key, out)
    return sorted(out.items, key=lambda f: (f.anon_start, f.anon_end))
