"""Keyed, deterministic surrogate generation (spec section 5).

Every surrogate is drawn from a Faker or a format generator seeded per value by
HMAC(hmac_key, label|attempt). A candidate that collides with a registered surrogate, any
known original, or the source text is rehashed with the next attempt counter.
"""
from __future__ import annotations

import hashlib
import hmac
import random
import re
import string
from datetime import date, datetime, timedelta

from faker import Faker

from anon3pass.types import SECRET_ENTITIES, MapEntry, Span
from anon3pass.vault import fingerprint

CASED = {"PERSON", "ORGANIZATION", "LOCATION", "ADDRESS"}
MAX_ATTEMPTS = 200
SUFFIX_RE = re.compile(r"(['’]s|['’])$")
INITIAL_RE = re.compile(r"^[A-Za-z]\.?$")
MALE_RE = re.compile(r"\b(?:Mr|Mister)\.?\s+$", re.I)
FEMALE_RE = re.compile(r"\b(?:Ms|Mrs|Miss)\.?\s+$", re.I)
HONORIFIC_RE = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Sir|Madam|Mister)\.?\s+$", re.I)
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%B %d, %Y", "%B %d %Y",
                "%d %B %Y", "%b %d, %Y", "%b %d %Y", "%d %b %Y", "%b. %d, %Y", "%Y/%m/%d", "%d.%m.%Y"]
EXAMPLE_DOMAINS = ["example.org", "example.com", "example.net"]


def norm(text: str) -> str:
    return " ".join(text.split()).casefold()


def policy_for(cfg: dict, entity) -> str:
    return (cfg.get("entity_policy") or {}).get(str(getattr(entity, "value", entity)), "surrogate")


def apply_case(base: str, text: str) -> str:
    """Reapply the case pattern of `text` (UPPER, lower, else as generated) to `base`."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 2 and text.isupper():
        return base.upper()
    if letters and text.islower():
        return base.lower()
    return base


def _fill_digits(text: str, digits: str) -> str:
    it = iter(digits)
    return "".join(next(it) if c.isdigit() else c for c in text)


def _rand_digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _luhn_check_digit(body: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return str((10 - total % 10) % 10)


def _same_class(text: str, rng: random.Random) -> str:
    out = []
    for c in text:
        if c.isdigit():
            out.append(rng.choice(string.digits))
        elif c.isascii() and c.isupper():
            out.append(rng.choice(string.ascii_uppercase))
        elif c.isascii() and c.islower():
            out.append(rng.choice(string.ascii_lowercase))
        else:
            out.append(c)
    return "".join(out)


def _iban_check(country: str, bban: str) -> str:
    def num(s: str) -> str:
        return "".join(str(int(c, 36)) for c in s)
    return f"{98 - int(num(bban + country) + '00') % 97:02d}"


def _render_date(fmt: str, d: date, padded: bool) -> str:
    fmt = fmt.replace("%d", f"{d.day:02d}" if padded else str(d.day))
    fmt = fmt.replace("%m", f"{d.month:02d}" if padded else str(d.month))
    return d.strftime(fmt)


def parse_date(text: str):
    """Return (date, fmt, padded) when `text` is an explicit date in a known format, else None."""
    text = text.strip()
    for fmt in DATE_FORMATS:
        for padded in (True, False):
            try:
                d = datetime.strptime(text, fmt).date()
            except ValueError:
                continue
            if _render_date(fmt, d, padded) == text:
                return d, fmt, padded
    return None


def age_phrase(text: str) -> str | None:
    m = re.search(r"\d+", text)
    if not m:
        return None
    n = int(m.group())
    if n < 13:
        return "a child"
    if n < 20:
        return "in their teens"
    if n >= 100:
        return "over 100"
    return f"in their {n // 10 * 10}s"


class SurrogateEngine:
    def __init__(self, hmac_key: bytes, cfg: dict, registry: dict[str, str] | None = None):
        self.hmac_key = hmac_key
        self.cfg = cfg
        self.registry: dict[str, str] = registry if registry is not None else {}
        scfg = cfg.get("surrogates") or {}
        self._fake = Faker(scfg.get("locale", "en_US"))
        self._date_max = int(scfg.get("date_shift_days_max", 180))
        self._store_secrets = bool((cfg.get("secrets_policy") or {}).get("store_in_vault", False))
        self._used = {v.casefold() for v in self.registry.values()}
        self._origs = {k.split("|", 1)[1] for k in self.registry if "|" in k}
        self._src = ""
        self._placeholders: dict[tuple[str, str], str] = {}
        self._ph_count: dict[str, int] = {}

    # ---- public -------------------------------------------------------------------------
    def assign(self, spans: list[Span], source_text: str) -> list[MapEntry]:
        """One MapEntry per span, aligned to the input order. Longer persons are bound first."""
        self._src = source_text.casefold()
        for s in spans:
            for t in (s.text, s.canonical):
                if t:
                    self._origs.add(norm(t))
                    self._origs.update(norm(p) for p in t.split())
        order = sorted(range(len(spans)),
                       key=lambda i: (spans[i].entity.value != "PERSON", -len(spans[i].text), i))
        entries: list[MapEntry | None] = [None] * len(spans)
        for i in order:
            entries[i] = self._entry(spans[i], source_text)
        return entries  # type: ignore[return-value]

    # ---- keyed randomness ------------------------------------------------------------
    def _digest(self, label: str, attempt: int) -> bytes:
        return hmac.new(self.hmac_key, f"{label}|{attempt}".encode(), hashlib.sha256).digest()

    def _rng(self, label: str, attempt: int) -> random.Random:
        rng = random.Random(self._digest(label, attempt))
        self._fake.seed_instance(rng.getrandbits(64))
        return rng

    def _ok(self, cand: str) -> bool:
        cf = cand.casefold()
        return bool(cf) and cf not in self._used and cf not in self._origs and cf not in self._src

    def _unique(self, label: str, make) -> str:
        for attempt in range(MAX_ATTEMPTS):
            cand = make(self._rng(label, attempt), attempt)
            if cand is None:
                return None
            if self._ok(cand):
                self._used.add(cand.casefold())
                return cand
        raise RuntimeError("could not find a collision-free surrogate")

    # ---- per-span dispatch -----------------------------------------------------------
    def _entry(self, span: Span, source: str) -> MapEntry:
        ent = span.entity.value
        policy = policy_for(self.cfg, span.entity)
        irreversible = span.entity in SECRET_ENTITIES and not self._store_secrets
        if policy == "keep":
            return MapEntry(span.text, ent, span.text, fingerprint(self.hmac_key, span.text), True)
        if irreversible or policy == "redact":
            return self._redacted(span, irreversible)
        if policy == "generalize":
            phrase = age_phrase(span.text) if ent == "AGE" else None
            if phrase is None:
                return self._redacted(span, irreversible)
            return MapEntry(phrase, ent, span.text, fingerprint(self.hmac_key, span.text), True)
        if ent == "PERSON":
            return self._person(span, source)
        return self._plain(span)

    def _placeholder(self, entity: str, text: str) -> str:
        k = (entity, norm(text))
        if k not in self._placeholders:
            n = self._ph_count.get(entity, 0) + 1
            while f"[{entity}_{n}]".casefold() in self._src:
                n += 1
            self._ph_count[entity] = n
            self._placeholders[k] = f"[{entity}_{n}]"
        return self._placeholders[k]

    def _redacted(self, span: Span, irreversible: bool) -> MapEntry:
        ent = span.entity.value
        return MapEntry(self._placeholder(ent, span.text), ent,
                        None if irreversible else span.text,
                        fingerprint(self.hmac_key, span.text), not irreversible)

    def _plain(self, span: Span) -> MapEntry:
        ent = span.entity.value
        ktext = (span.canonical or span.text).strip()
        key = f"{ent}|{norm(ktext)}"
        base = self.registry.get(key)
        if base is None:
            base = self._unique(key, lambda rng, a: self._generate(ent, ktext, rng, a))
            if base is None:  # unparseable date
                return MapEntry(self._placeholder(ent, span.text), ent, span.text,
                                fingerprint(self.hmac_key, ktext), True)
            self.registry[key] = base
        out = apply_case(base, span.text) if ent in CASED else base
        original = span.canonical or span.text
        return MapEntry(out, ent, original, fingerprint(self.hmac_key, norm(ktext)), True)

    # ---- persons -----------------------------------------------------------------------
    def _person(self, span: Span, source: str) -> MapEntry:
        text = span.text.strip()
        m = SUFFIX_RE.search(text)
        suffix = m.group() if m else ""
        core = text[:m.start()] if m else text
        ctext = (span.canonical or span.text).strip()
        cm = SUFFIX_RE.search(ctext)
        ccore = ctext[:cm.start()] if cm else ctext
        toks = ccore.split()
        pre = source[max(0, span.start - 12):span.start]
        pool = "male" if MALE_RE.search(pre) else "female" if FEMALE_RE.search(pre) else "any"
        honorific = bool(HONORIFIC_RE.search(pre))
        key = f"PERSON|{norm(ccore)}"
        base = self.registry.get(key)
        if base is None:
            n = len(toks)
            kinds = ["last" if honorific else "first"] if n == 1 else \
                ["first"] * (n - 1) + ["last"]
            base = " ".join(self._token(t, k, pool) for t, k in zip(toks, kinds))
            self.registry[key] = base
            self._used.add(base.casefold())
        out = apply_case(base, core) + suffix
        original = (ccore + suffix) if span.canonical else span.text
        return MapEntry(out, "PERSON", original, fingerprint(self.hmac_key, norm(ccore)), True)

    def _token(self, tok: str, kind: str, pool: str) -> str:
        if INITIAL_RE.match(tok):
            return self._initial(tok)
        pkey = f"PERSON.PART|{tok.casefold()}"
        if pkey in self.registry:
            return self.registry[pkey]

        def make(rng, attempt):
            if kind == "last":
                return self._fake.last_name()
            if pool == "male":
                return self._fake.first_name_male()
            if pool == "female":
                return self._fake.first_name_female()
            return self._fake.first_name()
        self.registry[pkey] = self._unique(pkey, make)
        return self.registry[pkey]

    def _initial(self, tok: str) -> str:
        letter = tok[0].casefold()
        ikey = f"PERSON.INIT|{letter}"
        if ikey not in self.registry:
            bound = sorted(k for k in self.registry if k.startswith(f"PERSON.PART|{letter}"))
            if bound:
                self.registry[ikey] = self.registry[bound[0]][0].upper()
            else:
                self.registry[ikey] = self._rng(ikey, 0).choice(string.ascii_uppercase)
        return self.registry[ikey] + ("." if tok.endswith(".") else "")

    # ---- format generators -----------------------------------------------------------
    def _generate(self, ent: str, text: str, rng: random.Random, attempt: int):
        gen = getattr(self, f"_gen_{ent.lower()}", None)
        return gen(text, rng, attempt) if gen else _same_class(text, rng)

    def _gen_organization(self, text, rng, attempt):
        return self._fake.company()

    def _gen_location(self, text, rng, attempt):
        return self._fake.city()

    def _gen_address(self, text, rng, attempt):
        return self._fake.street_address()

    def _gen_username(self, text, rng, attempt):
        return ("@" if text.startswith("@") else "") + self._fake.user_name()

    def _gen_email(self, text, rng, attempt):
        local = text.rsplit("@", 1)[0]
        pieces = re.split(r"([._+-])", local)
        words = [p for p in pieces if p and p not in "._+-"]
        bound = [self.registry.get(f"PERSON.PART|{w.casefold()}") for w in words]
        if words and all(bound):
            it = iter(b.casefold() for b in bound)
            new_local = "".join(p if (not p or p in "._+-") else next(it) for p in pieces)
            new_local += str(attempt) if attempt else ""
        else:
            new_local = self._fake.user_name() + (str(attempt) if attempt else "")
        return f"{new_local}@{rng.choice(EXAMPLE_DOMAINS)}"

    def _gen_phone(self, text, rng, attempt):
        n = sum(c.isdigit() for c in text)
        if n in (10, 11):
            area = str(rng.randint(2, 9)) + _rand_digits(rng, 2)
            digits = ("1" if n == 11 else "") + area + "55501" + _rand_digits(rng, 2)
        elif n == 7:
            digits = "55501" + _rand_digits(rng, 2)
        else:
            digits = _rand_digits(rng, n)
        return _fill_digits(text, digits)

    def _gen_url(self, text, rng, attempt):
        return f"https://example.org/{rng.getrandbits(40):010x}"

    def _gen_ip_address(self, text, rng, attempt):
        if ":" in text:
            return f"2001:db8::{rng.getrandbits(16):x}:{rng.getrandbits(16):x}"
        return f"192.0.2.{rng.randint(1, 254)}"

    def _gen_ssn(self, text, rng, attempt):
        n = sum(c.isdigit() for c in text)
        digits = "9" + _rand_digits(rng, n - 1) if n else ""
        return _fill_digits(text, digits)

    def _gen_credit_card(self, text, rng, attempt):
        n = sum(c.isdigit() for c in text)
        if n < 8:
            return _same_class(text, rng)
        body = "400000" + _rand_digits(rng, n - 7)
        return _fill_digits(text, body + _luhn_check_digit(body))

    def _gen_iban(self, text, rng, attempt):
        compact = re.sub(r"\s", "", text)
        if len(compact) < 8 or not compact[:2].isalpha():
            return _same_class(text, rng)
        country = compact[:2].upper()
        bban = _same_class(compact[4:].upper(), rng)
        new = country + _iban_check(country, bban) + bban
        it = iter(new)
        return "".join(next(it) if c.isalnum() else c for c in text)

    def _gen_date(self, text, rng, attempt):
        parsed = parse_date(text)
        if parsed is None:
            return None
        d, fmt, padded = parsed
        h = self._digest("date-shift", attempt)
        shift = int.from_bytes(h[:8], "big") % (2 * self._date_max + 1) - self._date_max
        return _render_date(fmt, d + timedelta(days=shift or 1), padded)
