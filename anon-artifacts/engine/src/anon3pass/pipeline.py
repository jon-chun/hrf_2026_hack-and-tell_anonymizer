"""Detect on the original text, merge spans once, replace once (invariant I6)."""
from __future__ import annotations

import dataclasses
import functools
import hashlib
import importlib
import json
import os
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from anon3pass import vault
from anon3pass.surrogates import SurrogateEngine, norm, policy_for
from anon3pass.types import SECRET_ENTITIES, DocMap, Entity, MapEntry, Occurrence, Span

HONORIFIC_PREFIX = re.compile(r"^(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Sir|Madam|Mister)\.?\s+", re.I)


TOKEN_CHAR = re.compile(r"[A-Za-z0-9/+=_-]")
NER_SOURCE = "pass2.presidio"
PROPAGATED = frozenset({Entity.PERSON, Entity.ORGANIZATION, Entity.LOCATION})
PROPAGATED_NAMES = frozenset(e.value for e in PROPAGATED)
PART_STOP = frozenset({"the", "and", "van", "von", "der", "del", "des", "bin", "ibn", "mrs", "miss", "sir", "prof"})


CALENDAR = frozenset("monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september october november december".split())


@functools.lru_cache(maxsize=1)
def common_words() -> frozenset[str]:
    """Ordinary English words: not treated as a name on their own, and not matched when lowercase."""
    from faker.providers.lorem.en_US import Provider
    from spacy.lang.en.stop_words import STOP_WORDS
    return frozenset(w.casefold() for w in (*Provider.word_list, *STOP_WORDS)) | CALENDAR


def _plausible_name(span: Span) -> bool:
    """NER often tags capitalised ordinary words (Budget, Board, Monday). Drop those."""
    if span.source != NER_SOURCE or span.entity not in PROPAGATED:
        return True
    tokens = re.findall(r"\w+", span.text.casefold())
    return not tokens or not all(t in common_words() for t in tokens)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pass_number(span: Span) -> int:
    m = re.match(r"pass(\d)", span.source)
    return int(m.group(1)) if m else 9


def _priority(span: Span) -> tuple:
    return (span.entity not in SECRET_ENTITIES, -(span.end - span.start), -span.score,
            _pass_number(span), span.start)


def merge_spans(spans: list[Span]) -> list[Span]:
    """Resolve overlaps: secret entity, then longer span, then higher score, then lower pass."""
    kept: list[Span] = []
    for s in sorted((s for s in spans if s.end > s.start), key=_priority):
        if all(s.end <= k.start or s.start >= k.end for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: (s.start, s.end))


def _trim_honorific(span: Span) -> Span:
    """Honorifics stay outside the replacement."""
    if span.entity.value != "PERSON":
        return span
    m = HONORIFIC_PREFIX.match(span.text)
    if not m or m.end() >= len(span.text):
        return span
    return dataclasses.replace(span, start=span.start + m.end(), text=span.text[m.end():])


def _clean(span: Span, text: str) -> Span | None:
    """Keep NER spans on one line and extend secrets to the end of their token."""
    if span.entity in SECRET_ENTITIES:
        end = span.end
        while end > span.start + 1 and text[end - 1] in ".,;:)":
            end -= 1
        while end < len(text) and TOKEN_CHAR.match(text[end]):
            end += 1
        return dataclasses.replace(span, end=end, text=text[span.start:end])
    head = span.text.split("\n", 1)[0]
    stripped = head.rstrip(" \t\r,;:.")
    lead = len(stripped) - len(stripped.lstrip(" \t*_#>"))
    stripped = stripped[lead:]
    if len(stripped) < 2:
        return None
    start = span.start + lead
    return dataclasses.replace(span, start=start, end=start + len(stripped), text=stripped)


def _propagation_terms(spans: list[Span], registry: dict) -> dict[str, Entity]:
    """Every value worth finding again: detected names, their parts, and values known to the set."""
    found: dict[str, Entity] = {}
    for s in spans:
        if s.entity not in PROPAGATED:
            continue
        name = re.sub(r"['’]s$", "", s.text).strip(" ()[]{}\"'“”")
        found.setdefault(norm(name), s.entity)
        if s.entity is Entity.PERSON:
            for part in name.split():
                part = part.strip(".,()\"'“”")
                if len(part) >= 3 and part[0].isupper() and part.casefold() not in PART_STOP:
                    found.setdefault(norm(part), s.entity)
    for key in registry:
        kind, _, value = key.partition("|")
        if kind in PROPAGATED_NAMES and len(value) >= 4:
            found.setdefault(value, Entity(kind))
    return found


def _propagate(text: str, spans: list[Span], registry: dict, allow: set[str]) -> list[Span]:
    """Replace every later mention of a detected value, not only the mention NER happened to find."""
    terms = {t: e for t, e in _propagation_terms(spans, registry).items() if t and t not in allow}
    if not terms:
        return []
    alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    pattern = re.compile(rf"(?<![\w@.-])(?:{alternatives})(?![\w@-])", re.IGNORECASE)
    out = []
    for m in pattern.finditer(text):
        if m.group()[0].isupper() or norm(m.group()) not in common_words():
            out.append(Span(m.start(), m.end(), m.group(), terms[norm(m.group())], "pass2.propagated", 0.5))
    return out


def _allowed(span: Span, terms: dict) -> bool:
    """`allow` terms are never replaced unless also in `deny`."""
    allow = {norm(t) for t in terms.get("allow", [])}
    deny = {norm(d["term"]) for d in terms.get("deny", [])}
    t = norm(span.text)
    t = t.removeprefix("the ")
    return t in allow and t not in deny


def _mod(name: str):
    return importlib.import_module(f"anon3pass.{name}")


def _detect(text: str, cfg: dict, terms: dict, extra_terms) -> list[Span]:
    passes = (cfg.get("pipeline") or {}).get("passes", [])
    spans: list[Span] = []
    if "patterns" in passes:
        spans += list(_mod("pass1_patterns").detect(text, cfg, terms, list(extra_terms)))
    if "libraries" in passes:
        spans += list(_mod("pass2_libs").detect(text, cfg))
    return spans


def _pass_label(span: Span) -> str:
    m = re.match(r"pass\d", span.source)
    return m.group() if m else "other"


def anonymize_text(text: str, doc_id: str, cfg: dict, master_key: bytes, registry: dict,
                   terms: dict, extra_terms=()) -> tuple[str, DocMap, dict]:
    _, hmac_key = vault.derive_keys(master_key)
    detected = _detect(text, cfg, terms, extra_terms)
    by_pass = Counter(_pass_label(s) for s in detected)
    pipe = cfg.get("pipeline") or {}
    terms = {**terms, "allow": [*terms.get("allow", []), *pipe.get("keep_public_entities", [])]}
    cleaned = [c for c in (_clean(s, text) for s in detected) if c is not None]
    cleaned = [s for s in cleaned if _plausible_name(s)]
    spans = [_trim_honorific(s) for s in cleaned]
    spans = merge_spans([s for s in spans if not _allowed(s, terms)])
    if pipe.get("propagate_mentions", True):
        allow = {norm(t) for t in terms["allow"]}
        again = _propagate(text, spans, registry, allow)
        by_pass["propagated"] = len(again)
        spans = merge_spans([*spans, *again])
    spans = [s for s in spans if policy_for(cfg, s.entity) != "keep"]

    entries = SurrogateEngine(hmac_key, cfg, registry).assign(spans, text)
    out: list[str] = []
    occurrences: list[Occurrence] = []
    unique: dict[tuple, MapEntry] = {}
    pos = 0
    out_len = 0
    for span, entry in zip(spans, entries):
        gap = text[pos:span.start]
        out.append(gap)
        out_len += len(gap)
        out.append(entry.surrogate)
        occ_original = span.text if entry.original is not None else None
        occurrences.append(Occurrence(out_len, out_len + len(entry.surrogate), occ_original))
        out_len += len(entry.surrogate)
        pos = span.end
        unique.setdefault((entry.surrogate, entry.entity, entry.original), entry)
    out.append(text[pos:])
    anon = "".join(out)

    docmap = DocMap(doc_id=doc_id, sha256_original=_sha(text), sha256_anon=_sha(anon),
                    entries=list(unique.values()), occurrences=occurrences)
    stats = {
        "by_pass": dict(by_pass),
        "by_entity": dict(Counter(s.entity.value for s in spans)),
        "spans_detected": len(detected),
        "spans_replaced": len(spans),
        "passes": list((cfg.get("pipeline") or {}).get("passes", [])),
    }
    return anon, docmap, stats


def _make_private_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(mode=0o700, parents=True)
        os.chmod(path, 0o700)


def anonymize_file(in_path, out_dir, cfg: dict, extra_terms=(), now: datetime | None = None) -> dict:
    """Write <stem>.anon<suffix>, <stem>.map.enc, _registry.registry.enc, <stem>.report.json."""
    in_path, out_dir = Path(in_path), Path(out_dir)
    master = vault.load_key(os.path.expanduser(cfg["paths"]["key_file"]))
    enc_key, _ = vault.derive_keys(master)
    terms = _mod("config").load_terms(cfg)
    text = in_path.read_bytes().decode("utf-8")
    _make_private_dir(out_dir)

    registry_path = out_dir / "_registry.registry.enc"
    registry = vault.load_registry(registry_path, enc_key) if registry_path.exists() else {}
    doc_id = in_path.stem
    anon, docmap, stats = anonymize_text(text, doc_id, cfg, master, registry, terms, extra_terms)

    anon_path = out_dir / f"{in_path.stem}.anon{in_path.suffix}"
    map_path = out_dir / f"{in_path.stem}.map.enc"
    report_path = out_dir / f"{in_path.stem}.report.json"
    vault.write_atomic(anon_path, anon.encode("utf-8"), 0o644)
    vault.save_docmap(map_path, docmap, enc_key)
    vault.save_registry(registry_path, registry, enc_key)
    report = {
        "doc_id": doc_id,
        "sha256_original": docmap.sha256_original,
        "sha256_anon": docmap.sha256_anon,
        "counts": {"by_pass": stats["by_pass"], "by_entity": stats["by_entity"]},
        "passes": stats["passes"],
        "timestamp": (now or datetime.now(UTC)).isoformat(),
        "status": "ok",
    }
    vault.write_atomic(report_path, json.dumps(report, indent=2).encode("utf-8"), 0o600)
    return {"doc_id": doc_id, "anon_path": str(anon_path), "map_path": str(map_path),
            "registry_path": str(registry_path), "report_path": str(report_path),
            "stats": stats, "status": "ok"}
