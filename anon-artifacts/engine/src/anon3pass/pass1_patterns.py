"""Pass 1: deterministic detection (regex rules, denylist, fuzzy denylist, extra terms).

Invariant I1: nothing in this module prints or logs a matched value.
"""
from __future__ import annotations

import ipaddress
import re
from datetime import date

from rapidfuzz import fuzz

from .types import Entity, Span

# ---------------------------------------------------------------- validators


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def iban_ok(raw: str) -> bool:
    s = raw.replace(" ", "").upper()
    if not 15 <= len(s) <= 34 or not s.isalnum():
        return False
    moved = s[4:] + s[:4]
    num = "".join(str(int(c, 36)) for c in moved)
    return int(num) % 97 == 1


def _valid_ymd(y: int, m: int, d: int) -> bool:
    try:
        date(y, m, d)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------- patterns

_MON = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
        r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?")
_DAY = r"(?:0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?"
_YEAR = r"(?:19|20)\d{2}"

RE_EMAIL = re.compile(
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
RE_URL = re.compile(r"(?<![\w/])(?:https?://|www\.)[^\s<>\"'`]+", re.IGNORECASE)
_OCT = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
RE_IPV4 = re.compile(rf"(?<![\w.])(?:{_OCT}\.){{3}}{_OCT}(?![\w]|\.\d)")
RE_IPV6 = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")
RE_PHONE_US = re.compile(
    r"(?<![\w.+-])(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\d{3}[\s.-])\d{3}[\s.-]\d{4}(?![\w-])")
RE_PHONE_INTL = re.compile(r"(?<![\w+])\+\d{1,3}(?:[\s.-]?\(?\d{1,4}\)?){2,6}(?!\d)")
RE_SSN = re.compile(r"(?<![\d-])\d{3}[- ]\d{2}[- ]\d{4}(?![\d-])")
RE_CARD = re.compile(r"(?<![\w-])\d(?:[ -]?\d){12,18}(?![\w-])")
RE_IBAN = re.compile(r"(?<!\w)[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?(?!\w)")
RE_DATE_ISO = re.compile(r"(?<![\d/.-])(\d{4})([-/.])(\d{1,2})\2(\d{1,2})(?![\d]|[-/.]\d)")
RE_DATE_NUM = re.compile(r"(?<![\d/.-])(\d{1,2})([-/.])(\d{1,2})\2(\d{4}|\d{2})(?![\d]|[-/.]\d)")
RE_DATE_MDY = re.compile(rf"(?<!\w){_MON}\s+{_DAY}(?!\d)(?:,?\s+{_YEAR}(?!\d))?")
RE_DATE_DMY = re.compile(rf"(?<![\w/-]){_DAY}\s+(?:of\s+)?{_MON}(?!\w)(?:,?\s+{_YEAR}(?!\d))?")
RE_AGE = re.compile(
    r"(?<![\w-])(?:(\d{1,3})[- ](?:years?|yrs?)[- ]old|(\d{1,3})\s?y/o|aged?\s+(\d{1,3})(?![\d]|[-–]\d))"
    r"(?!\w)", re.IGNORECASE)
RE_HANDLE = re.compile(r"(?<![\w@.])@[A-Za-z_][A-Za-z0-9_]{1,29}(?![\w@])")

TRAILING_PUNCT = ".,;:!?)]}'\""


def _s(m_start: int, m_end: int, text: str, entity: Entity, rule: str, score: float = 1.0) -> Span:
    return Span(m_start, m_end, text[m_start:m_end], entity, f"pass1.regex.{rule}", score)


# ---------------------------------------------------------------- rule functions
# Each takes the text and returns a list of Span.


def _rule_email(text: str) -> list[Span]:
    return [_s(m.start(), m.end(), text, Entity.EMAIL, "email") for m in RE_EMAIL.finditer(text)]


def _rule_url(text: str) -> list[Span]:
    out = []
    for m in RE_URL.finditer(text):
        end = m.end()
        while end > m.start() and text[end - 1] in TRAILING_PUNCT:
            # keep a closing bracket that has its opener inside the URL
            if text[end - 1] == ")" and "(" in text[m.start():end]:
                break
            end -= 1
        body = re.sub(r"^(https?://|www\.)", "", text[m.start():end], flags=re.IGNORECASE)
        if body:
            out.append(_s(m.start(), end, text, Entity.URL, "url"))
    return out


def _rule_ipv4(text: str) -> list[Span]:
    return [_s(m.start(), m.end(), text, Entity.IP_ADDRESS, "ipv4") for m in RE_IPV4.finditer(text)]


def _rule_ipv6(text: str) -> list[Span]:
    out = []
    for m in RE_IPV6.finditer(text):
        cand = m.group()
        if cand.count(":") < 2 or cand.strip(":") == "":
            continue
        try:
            ipaddress.IPv6Address(cand)
        except ValueError:
            continue
        out.append(_s(m.start(), m.end(), text, Entity.IP_ADDRESS, "ipv6"))
    return out


def _rule_phone(text: str) -> list[Span]:
    out = []
    for m in RE_PHONE_US.finditer(text):
        out.append(_s(m.start(), m.end(), text, Entity.PHONE, "phone"))
    for m in RE_PHONE_INTL.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 8 <= len(digits) <= 15:
            out.append(_s(m.start(), m.end(), text, Entity.PHONE, "phone"))
    return out


def _rule_ssn(text: str) -> list[Span]:
    out = []
    for m in RE_SSN.finditer(text):
        area, group, serial = re.split(r"[- ]", m.group())
        if area == "000" or group == "00" or serial == "0000":
            continue
        out.append(_s(m.start(), m.end(), text, Entity.SSN, "ssn"))
    return out


def _rule_credit_card(text: str) -> list[Span]:
    out = []
    for m in RE_CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            out.append(_s(m.start(), m.end(), text, Entity.CREDIT_CARD, "credit_card"))
    return out


def _rule_iban(text: str) -> list[Span]:
    out = []
    for m in RE_IBAN.finditer(text):
        groups = m.group().split(" ")
        for k in range(len(groups), 0, -1):  # shrink trailing groups until the checksum holds
            cand = " ".join(groups[:k])
            if iban_ok(cand):
                out.append(_s(m.start(), m.start() + len(cand), text, Entity.IBAN, "iban"))
                break
    return out


def _rule_date(text: str) -> list[Span]:
    out = []
    for m in RE_DATE_ISO.finditer(text):
        if _valid_ymd(int(m.group(1)), int(m.group(3)), int(m.group(4))):
            out.append(_s(m.start(), m.end(), text, Entity.DATE, "date"))
    for m in RE_DATE_NUM.finditer(text):
        a, sep, b, y = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        if len(y) == 2 and sep != "/":
            continue  # 2-digit years only with slashes; avoids version-like numbers
        if 1 <= a <= 31 and 1 <= b <= 31 and (a <= 12 or b <= 12):
            out.append(_s(m.start(), m.end(), text, Entity.DATE, "date"))
    for rx in (RE_DATE_MDY, RE_DATE_DMY):
        for m in rx.finditer(text):
            out.append(_s(m.start(), m.end(), text, Entity.DATE, "date"))
    return out


def _rule_age(text: str) -> list[Span]:
    out = []
    for m in RE_AGE.finditer(text):
        n = int(next(g for g in m.groups() if g))
        if 0 < n < 120:
            out.append(_s(m.start(), m.end(), text, Entity.AGE, "age"))
    return out


def _rule_handle(text: str) -> list[Span]:
    return [_s(m.start(), m.end(), text, Entity.USERNAME, "handle") for m in RE_HANDLE.finditer(text)]


RE_ADDRESS = re.compile(
    r"\b\d{1,5}[A-Za-z]?\s+(?:[A-Z][\w'’-]*\s+){1,4}"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Way|Court|Ct|Square|Sq|Place|Pl|Terrace|Highway|Hwy)\b\.?"
    r"(?:,?\s+(?:Apt|Apartment|Suite|Unit|Floor)\.?\s*\w+)?"
    r"|\bP\.?\s?O\.?\s+Box\s+\d+\b"
)
RE_LABELLED_ID = re.compile(
    r"(?i:passport|national\s+id|id\s+card|identity\s+card|licen[cs]e|case|file|tax\s+id|reference|ref)"
    r"(?i:\s+(?:no\.?|number|num\.?|#))?\s*[:#]?\s*(?P<v>(?=[A-Z0-9-]*\d)[A-Z0-9][A-Z0-9-]{4,})\b"
)
RE_BARE_ID = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")


RE_ADDRESS_EXTRA = re.compile(
    r"\b\d{1,5},?\s+(?:Rue|Calle|Avenida|Via|Strasse|Straße|Ulitsa)\s+[^\n,;]{2,40}(?:,\s*\d{4,6}\s+[^\W\d]+)?"
    r"|\b(?:Plot|Flat|House\s+No\.?)\s+\d+[^\n;]{0,50}?\b\d{5,6}\b"
)
RE_LONG_NUMBER = re.compile(r"(?<![\w.+-])\d(?:[ -]?\d){7,}(?![\w-])")
RE_MIXED_ID = re.compile(r"\b\d{8}[A-Z]\b|\b[A-Z]{2}(?: ?\d{2}){3} ?[A-Z]\b")
RE_LABELLED_ACCOUNT = re.compile(
    r"(?i:\b(?:sort\s+code|acct|account|a/c|bsb|routing|iban|swift)\b)\s*(?i:no\.?|number|#)?\s*[:#]?\s*"
    r"(?P<v>\d[\d -]{3,}\d)"
)
RE_LABELLED_PLATE = re.compile(
    r"(?i:\b(?:plate|registration|reg\.?\s+no\.?|licen[cs]e\s+plate)\b)\s*[:#]?\s*(?P<v>(?=[^\n]*\d)[A-Z0-9][A-Z0-9-]*(?: [A-Z0-9-]{1,6}){0,2})"
)
RE_LABELLED_USER = re.compile(r"(?i:\b(?:user|username|user\s+id|login)\b)\s*[:=]?\s*(?P<v>(?=[a-z0-9._-]*[\d._-])[a-z0-9][a-z0-9._-]{2,})")
_N = r"(?:zero|oh|one|two|three|four|five|six|seven|eight|nine|ten|double|triple|plus|dash|hyphen)"
RE_SPOKEN_NUMBER = re.compile(rf"(?i)\b{_N}(?:[ -]+{_N}){{4,}}\b")
RE_SPOKEN_EMAIL = re.compile(r"(?i)\b[a-z0-9]+(?: dot [a-z0-9]+)* at [a-z0-9]+(?: dot [a-z]+)+\b")
_ORD = "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty[ -]\\w+|thirtieth|thirty[ -]first"
RE_ORDINAL_DATE = re.compile(
    rf"(?i)\b(?:{_ORD}) of (?:january|february|march|april|may|june|july|august|september|october|november|december)\b(?:,? \d{{4}})?"
)


def _groups(pattern: re.Pattern, text: str, entity: Entity, rule: str) -> list[Span]:
    return [_s(m.start("v"), m.end("v"), text, entity, rule) for m in pattern.finditer(text)]


def _whole(pattern: re.Pattern, text: str, entity: Entity, rule: str) -> list[Span]:
    return [_s(m.start(), m.end(), text, entity, rule) for m in pattern.finditer(text)]


def _rule_accounts(text: str) -> list[Span]:
    return _groups(RE_LABELLED_ACCOUNT, text, Entity.BANK_ACCOUNT, "account") + _groups(RE_LABELLED_PLATE, text, Entity.ID_NUMBER, "plate")


def _rule_long_number(text: str) -> list[Span]:
    return _whole(RE_LONG_NUMBER, text, Entity.ID_NUMBER, "long_number") + _whole(RE_MIXED_ID, text, Entity.ID_NUMBER, "mixed_id")


def _rule_labelled_user(text: str) -> list[Span]:
    return _groups(RE_LABELLED_USER, text, Entity.USERNAME, "labelled_user")


def _rule_spoken(text: str) -> list[Span]:
    return (_whole(RE_SPOKEN_NUMBER, text, Entity.ID_NUMBER, "spoken_number") + _whole(RE_SPOKEN_EMAIL, text, Entity.EMAIL, "spoken_email"))


def _rule_ordinal_date(text: str) -> list[Span]:
    return _whole(RE_ORDINAL_DATE, text, Entity.DATE, "ordinal_date")


def _rule_address(text: str) -> list[Span]:
    return _whole(RE_ADDRESS, text, Entity.ADDRESS, "address") + _whole(RE_ADDRESS_EXTRA, text, Entity.ADDRESS, "address")


def _rule_id_number(text: str) -> list[Span]:
    out = [_s(m.start("v"), m.end("v"), text, Entity.ID_NUMBER, "id_number") for m in RE_LABELLED_ID.finditer(text)]
    out += [_s(m.start(), m.end(), text, Entity.ID_NUMBER, "id_number") for m in RE_BARE_ID.finditer(text)]
    return out


RULES = {
    "address": _rule_address, "id_number": _rule_id_number, "accounts": _rule_accounts,
    "long_number": _rule_long_number, "labelled_user": _rule_labelled_user, "spoken": _rule_spoken,
    "ordinal_date": _rule_ordinal_date,
    "email": _rule_email, "url": _rule_url, "ipv4": _rule_ipv4, "ipv6": _rule_ipv6,
    "phone": _rule_phone, "ssn": _rule_ssn, "credit_card": _rule_credit_card, "iban": _rule_iban,
    "date": _rule_date, "age": _rule_age, "handle": _rule_handle,
}


def _custom_rules(text: str, rules: list[dict]) -> list[Span]:
    out = []
    for rule in rules:
        rx = re.compile(rule["regex"])
        ent = Entity(rule["entity"])
        for m in rx.finditer(text):
            if m.end() > m.start():
                out.append(_s(m.start(), m.end(), text, ent, str(rule["name"])))
    return out


# ---------------------------------------------------------------- denylist


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _word_regex(terms: list[str]) -> re.Pattern | None:
    terms = sorted({t for t in terms if t.strip()}, key=len, reverse=True)
    if not terms:
        return None
    alts = [r"\s+".join(re.escape(p) for p in t.split()) for t in terms]
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


def _exact_spans(text: str, terms: list[tuple[str, Entity]], source: str) -> list[Span]:
    lookup = {_norm(t): e for t, e in terms}
    rx = _word_regex([t for t, _ in terms])
    if rx is None:
        return []
    out = []
    for m in rx.finditer(text):
        ent = lookup.get(_norm(m.group()))
        if ent is not None:
            out.append(Span(m.start(), m.end(), m.group(), ent, source))
    return out


_TOKEN = re.compile(r"\w+")


def _fuzzy_spans(text: str, terms: list[tuple[str, Entity]], threshold: float, min_length: int,
                 extra_tokens: int, covered: list[Span]) -> list[Span]:
    terms = [(t, e) for t, e in terms if len(t) >= min_length]
    if not terms:
        return []
    toks = [(m.start(), m.end()) for m in _TOKEN.finditer(text)]
    # unique windows (normalised) -> list of (start, end); one pass over the tokens
    windows: dict[str, list[tuple[int, int]]] = {}
    sizes = {len(t.split()) for t, _ in terms}
    for n in sizes:
        for k in range(n, n + extra_tokens + 1):
            for i in range(len(toks) - k + 1):
                a, b = toks[i][0], toks[i + k - 1][1]
                key = " ".join(text[s:e] for s, e in toks[i:i + k]).lower()
                windows.setdefault(key, []).append((a, b))
    keys = list(windows)
    by_len: dict[int, list[str]] = {}
    for key in keys:
        by_len.setdefault(len(key), []).append(key)
    out = []
    for term, ent in terms:
        tn = _norm(term)
        slack = int(len(tn) * (100 - threshold) / threshold) + 1  # length difference that can still reach the threshold
        cands: list[tuple[float, int, int]] = []
        for ln in range(max(1, len(tn) - slack), len(tn) + slack + 1):
            for key in by_len.get(ln, ()):
                if key == tn:
                    continue  # exact hits belong to the exact denylist
                score = fuzz.ratio(tn, key, score_cutoff=threshold)
                if score:
                    cands.extend((score, a, b) for a, b in windows[key])
        cands.sort(key=lambda c: (-c[0], -(c[2] - c[1]), c[1]))
        taken: list[tuple[int, int]] = []
        for score, a, b in cands:
            if any(a < s.end and s.start < b for s in covered):
                continue
            if any(a < e and s < b for s, e in taken):
                continue
            taken.append((a, b))
            out.append(Span(a, b, text[a:b], ent, "pass1.fuzzy", score / 100.0, canonical=term))
    return out


# ---------------------------------------------------------------- allow list


def _allow_ranges(text: str, allow: list[str]) -> list[tuple[int, int]]:
    rx = _word_regex(allow)
    return [(m.start(), m.end()) for m in rx.finditer(text)] if rx else []


# ---------------------------------------------------------------- public API


def _extra_pairs(extra_terms) -> list[tuple[str, Entity]]:
    """Extra terms are plain strings or {term, entity} mappings written by `anon qa-apply`."""
    pairs = []
    for t in extra_terms:
        if isinstance(t, dict):
            pairs.append((str(t["term"]), Entity(t.get("entity", "CUSTOM"))))
        else:
            pairs.append((str(t), Entity.CUSTOM))
    return pairs


def detect(text: str, cfg: dict, terms: dict, extra_terms: list = ()) -> list[Span]:
    p1 = cfg["pass1_patterns"]
    spans: list[Span] = []
    for name in p1.get("enabled_rules", []):
        spans.extend(RULES[name](text))
    spans.extend(_custom_rules(text, p1.get("custom_rules") or []))

    deny = [(d["term"], Entity(d["entity"])) for d in terms.get("deny", [])]
    exact = _exact_spans(text, deny, "pass1.denylist")
    extra = _exact_spans(text, _extra_pairs(extra_terms), "pass1.extra_terms")
    spans.extend(exact + extra)

    fz = p1.get("fuzzy", {})
    if fz.get("enabled"):
        spans.extend(_fuzzy_spans(text, deny, float(fz["threshold"]), int(fz["min_length"]),
                                  int(fz.get("max_edit_window", 1)), exact + extra))

    # allow terms suppress matches, unless the same term is also denied (or an extra term)
    protected = {_norm(t) for t, _ in deny} | {_norm(t) for t, _ in _extra_pairs(extra_terms)}
    allow = [a for a in terms.get("allow", []) if _norm(a) not in protected]
    ranges = _allow_ranges(text, allow)
    if ranges:
        spans = [s for s in spans if not any(a <= s.start and s.end <= b for a, b in ranges)]

    return sorted(set(spans), key=lambda s: (s.start, s.end, s.source))
