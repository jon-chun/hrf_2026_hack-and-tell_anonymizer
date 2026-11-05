"""Shared contracts. All modules import from here; do not redefine these types."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum

class Entity(StrEnum):
    PERSON="PERSON"; ORGANIZATION="ORGANIZATION"; LOCATION="LOCATION"; ADDRESS="ADDRESS"
    EMAIL="EMAIL"; PHONE="PHONE"; URL="URL"; IP_ADDRESS="IP_ADDRESS"; DATE="DATE"; AGE="AGE"
    SSN="SSN"; CREDIT_CARD="CREDIT_CARD"; IBAN="IBAN"; BANK_ACCOUNT="BANK_ACCOUNT"
    ID_NUMBER="ID_NUMBER"; USERNAME="USERNAME"; API_KEY="API_KEY"; PASSWORD="PASSWORD"
    PRIVATE_KEY="PRIVATE_KEY"; TOKEN="TOKEN"; SECRET="SECRET"; CUSTOM="CUSTOM"

SECRET_ENTITIES = frozenset({Entity.API_KEY, Entity.PASSWORD, Entity.PRIVATE_KEY, Entity.TOKEN, Entity.SECRET})

@dataclass(frozen=True)
class Span:
    """A detected sensitive region of the ORIGINAL text. [start, end) are character offsets."""
    start: int
    end: int
    text: str
    entity: Entity
    source: str                    # e.g. pass1.regex.email, pass1.denylist, pass1.fuzzy, pass2.presidio, pass2.secrets
    score: float = 1.0
    canonical: str | None = None   # denylist term a fuzzy variant resolved to

@dataclass(frozen=True)
class Occurrence:
    """Where one replacement landed. Enables byte-exact restore of unedited output."""
    anon_start: int
    anon_end: int
    original: str | None           # None when irreversible (secrets, by default)

@dataclass
class MapEntry:
    surrogate: str
    entity: str
    original: str | None           # None when irreversible
    fingerprint: str               # keyed HMAC hex, safe to print
    reversible: bool = True

@dataclass
class DocMap:
    """Plaintext of `<doc>.map.enc`."""
    doc_id: str
    sha256_original: str
    sha256_anon: str
    entries: list[MapEntry] = field(default_factory=list)
    occurrences: list[Occurrence] = field(default_factory=list)
    version: int = 1

@dataclass(frozen=True)
class LeakFinding:
    """Output of verification or the QA agent. Must never carry an original value from the vault."""
    category: str                  # exact_original | normalized_original | fuzzy_original | pattern | secret | entropy | agent
    entity: str
    severity: str                  # high | medium | low
    anon_start: int = -1
    anon_end: int = -1
    fingerprint: str = ""
    quote: str = ""                # text from the ANONYMIZED document only
    reason: str = ""
