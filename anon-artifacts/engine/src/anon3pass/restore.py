"""Restore originals: exact by occurrences when the text is unedited, else reverse lookup."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from anon3pass import vault
from anon3pass.types import DocMap


def _restore_exact(anon: str, docmap: DocMap) -> tuple[str, dict]:
    out, pos, replaced, placeholders = [], 0, 0, 0
    for occ in sorted(docmap.occurrences, key=lambda o: o.anon_start):
        out.append(anon[pos:occ.anon_start])
        if occ.original is None:
            out.append(anon[occ.anon_start:occ.anon_end])
            placeholders += 1
        else:
            out.append(occ.original)
            replaced += 1
        pos = occ.anon_end
    out.append(anon[pos:])
    return "".join(out), {"mode": "exact", "replaced": replaced, "placeholders_left": placeholders,
                          "unmatched_surrogates": 0, "ambiguous_surrogates": 0}


def _alternative(surrogate: str) -> str:
    pre = r"(?<!\w)" if re.match(r"\w", surrogate[0]) else ""
    post = r"(?!\w)" if re.match(r"\w", surrogate[-1]) else ""
    return f"{pre}{re.escape(surrogate)}{post}"


def _restore_reverse(anon: str, docmap: DocMap) -> tuple[str, dict]:
    originals: dict[str, set[str]] = {}
    for e in docmap.entries:
        if e.original is not None and e.reversible and e.surrogate:
            originals.setdefault(e.surrogate, set()).add(e.original)
    ambiguous = {s for s, o in originals.items() if len(o) > 1}
    lookup = {s: next(iter(o)) for s, o in originals.items() if s not in ambiguous}
    found: set[str] = set()
    if not lookup:
        return anon, {"mode": "reverse", "replaced": 0, "unmatched_surrogates": 0,
                      "ambiguous_surrogates": len(ambiguous)}
    pattern = re.compile("|".join(_alternative(s) for s in sorted(lookup, key=len, reverse=True)))

    def sub(m: re.Match) -> str:
        found.add(m.group())
        return lookup[m.group()]

    restored, n = pattern.subn(sub, anon)
    return restored, {"mode": "reverse", "replaced": n,
                      "unmatched_surrogates": len(set(lookup) - found),
                      "ambiguous_surrogates": len(ambiguous)}


def restore_text(anon: str, docmap: DocMap) -> tuple[str, dict]:
    if hashlib.sha256(anon.encode("utf-8")).hexdigest() == docmap.sha256_anon:
        return _restore_exact(anon, docmap)
    return _restore_reverse(anon, docmap)


def restore_file(anon_path, map_path, out_path, cfg: dict) -> dict:
    master = vault.load_key(os.path.expanduser(cfg["paths"]["key_file"]))
    enc_key, _ = vault.derive_keys(master)
    docmap = vault.load_docmap(map_path, enc_key)
    anon = Path(anon_path).read_bytes().decode("utf-8")
    restored, stats = restore_text(anon, docmap)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vault.write_atomic(out_path, restored.encode("utf-8"), 0o600)
    return {**stats, "doc_id": docmap.doc_id, "out_path": str(out_path)}
