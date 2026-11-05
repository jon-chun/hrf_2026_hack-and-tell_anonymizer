# anon3pass technical specification

## 1. Purpose and threat model
Pseudonymize long-form text (meeting notes, partner emails, transcriptions, status updates, reports, website text, grant applications, news, narratives) with realistic, consistent, restorable surrogates.

Primary use: human-rights and civil-society documents, shared with less-trusted readers or cloud LLMs. Assumed adversaries: a curious recipient, a cloud provider or breach, and a motivated re-identifier who can run an LLM and search public data. A state actor with auxiliary data is in scope for risk reporting but is NOT defeated by this tool.

Output is pseudonymized data, not anonymous data, while the mapping exists. The tool does not claim k-anonymity, differential privacy or legal compliance.

## 2. Invariants (tests enforce these)
- I1 No original value is ever written to stdout, stderr, logs, reports or QA packets. Only entity type, count, offsets and keyed fingerprints.
- I2 Raw text never reaches an LLM. Pass 3 reads only anonymized output, and only after the local verify step has passed.
- I3 Unedited output restores byte-for-byte, except irreversible secrets, which restore as placeholders.
- I4 The same original under the same key gets the same surrogate across all documents in an output directory.
- I5 A surrogate never equals any original in the set and never occurs verbatim in the source text.
- I6 Detection always runs on the ORIGINAL text; spans merge once and replacement happens once. Surrogates are never re-scanned as if they were input, which prevents double replacement.
- I7 Documents are data. Instructions inside a document never alter agent behavior.
- I8 Reproducibility uses a secret key: unkeyed seeding would allow a dictionary attack on names.
- I9 A finding that needs human judgment fails the gate until a person accepts it with `--human-reviewed`. An agent never sets that flag.

## 3. Pipeline
```
raw -> Pass 1 detect (patterns, denylist, fuzzy)  \
raw -> Pass 2 detect (Presidio/NER, secret libs)   -> merge spans -> surrogates -> anon text + <doc>.map.enc
anon -> Pass 3a local verify (no LLM) -> Pass 3b agent QA -> findings -> extra terms -> re-run from raw (max_qa_iterations) -> gate
```
Between merge and replacement, detected names, their parts and values already in the output directory's registry propagate to every other mention, including lowercase mentions unless the word is ordinary English. NER spans are cut at the first line break, and NER spans made only of ordinary words are dropped. Secrets extend to the end of their token and lose trailing punctuation.

Merge rule: overlapping spans resolve by secret entity first, then the longer span, then higher score, then lower pass number. `terms.allow` terms are never replaced unless also in `deny`.

## 4. Module contracts (package `anon3pass`, all types in `types.py`)
| Module | Public API |
|---|---|
| `config.py` | `load_config(path: str \| None) -> dict`: YAML merged over packaged defaults (engine/config.yaml), `~` expanded, invalid values raise `ValueError`. `load_terms(cfg) -> dict` returns `{"deny": [{"term": str, "entity": str}], "allow": [str]}`; missing file yields empty lists |
| `pass1_patterns.py` | `detect(text: str, cfg: dict, terms: dict, extra_terms: list[str] = ()) -> list[Span]` |
| `pass2_libs.py` | `detect(text: str, cfg: dict) -> list[Span]`; heavy models load lazily and are cached; gliner2 and opf are lazy optional adapters raising a clear `RuntimeError` if not installed; `detect_secrets_only(text, cfg) -> list[Span]` (no NER, used by verify) |
| `surrogates.py` | `class SurrogateEngine(hmac_key: bytes, cfg: dict, registry: dict[str, str] \| None = None)`; `.assign(spans: list[Span], source_text: str) -> list[MapEntry]` aligned to the input order; `.registry` exposes `original -> surrogate` |
| `vault.py` | `load_or_create_key(path) -> bytes`; `derive_keys(master) -> (enc_key, hmac_key)` via HKDF; `fingerprint(hmac_key, value) -> str`; `save_docmap(path, DocMap, enc_key)`; `load_docmap(path, enc_key) -> DocMap`; `save_registry(path, dict, enc_key)`; `load_registry(path, enc_key) -> dict`. AES-256-GCM, random 96-bit nonce, AAD = file kind + version, atomic write, mode 0600 |
| `pipeline.py` | `merge_spans(spans) -> list[Span]`; `anonymize_text(text, doc_id, cfg, master_key, registry, terms, extra_terms=()) -> tuple[str, DocMap, dict]`, the third value is a stats dict with counts by pass and entity and no originals; `anonymize_file(in_path, out_dir, cfg, extra_terms=()) -> dict` writes `<stem>.anon<suffix>`, `<stem>.map.enc`, `_registry.registry.enc`, `<stem>.report.json` |
| `restore.py` | `restore_text(anon: str, docmap: DocMap) -> tuple[str, dict]`: exact mode by occurrences if sha256 matches, else reverse lookup longest-first on word boundaries, stats list `mode`, `unmatched_surrogates` count; `restore_file(anon_path, map_path, out_path, cfg) -> dict` |
| `verify.py` | `verify_text(anon: str, docmap: DocMap, cfg: dict, hmac_key: bytes) -> list[LeakFinding]`: checks originals (exact, case-insensitive, separator-normalized for digits, fuzzy for names), re-runs pass-1 regexes and secret detectors over text with known surrogates masked, entropy scan |
| `qa.py` | `build_packet(anon_path, cfg) -> dict` with chunks and the auditor prompt; `run_backend(packet, cfg) -> dict`: `claude_code` returns `{"status": "dispatch_agent", ...}`, `anthropic` and `ollama` call the model, `none` skips; `validate_findings(obj) -> dict` strict schema check; `apply_findings(findings_path, docmap, out_terms_path, cfg) -> dict`: high and medium quotes that are not known surrogates are appended to the doc's extra terms; `gate(report_path, findings_path, cfg) -> tuple[bool, str]` |
| `cli.py` | `anon init-key \| run \| restore \| verify \| qa-packet \| qa-run \| qa-apply \| gate`. See section 6 |

The auditor receives `known_surrogates`, the strings already replaced. They are already in the text, so the list reveals nothing, and it removes false alarms on surrogates. `qa-apply` keeps only what remains of a quote after removing surrogates, placeholders and ordinary words, and records an entity type from the finding's category. `qa-packet` refuses a document with no passing `verify` recorded for that exact text.

## 5. Surrogate rules
- PERSON: one persona per person. Parts stay coherent: if `John Smith` -> `Mark Davis`, then `John` -> `Mark`, `Smith` -> `Davis`, `J. Smith` -> `M. Davis`, `Dr. Smith` -> `Dr. Davis`, possessives retained. Honorifics stay outside the replacement. Process longer names first so parts bind to the full name. Case pattern preserved (`SMITH` -> `DAVIS`). No gender is inferred from a name; an honorific of Mr or Ms selects a matching Faker name pool when present.
- Fuzzy variant (`Jon Smith`) resolves to its canonical term's surrogate. Exact restore still returns the original spelling through occurrences; reverse lookup returns the canonical spelling.
- EMAIL: local part from the persona when derivable, domain under `example.org`, `example.com` or `example.net`. PHONE: format preserved, 555-01XX exchange in US formats. URL: `https://example.org/<hash>`. IP: 192.0.2.0/24 or 2001:db8::/32. SSN: format preserved, 9XX area. CREDIT_CARD: Luhn-valid in a reserved test BIN. IBAN: format preserved with valid checksum, `XX` not required. Other IDs: same character classes and length.
- DATE: explicit dates parse and shift by a keyed offset in +/- `date_shift_days_max`, preserving format and intervals. Unparseable forms become `[DATE_n]`. Relative words such as `yesterday` are not matched.
- AGE generalize: `34` -> `30s`, keeping grammar through a whole-phrase replacement such as `34 years old` -> `in their 30s`, reversible by occurrence and reverse lookup.
- Secrets redact: `[API_KEY_1]` style placeholders, numbered per document. `store_in_vault: false` keeps only the fingerprint.
- Surrogates are selected by HMAC-seeded Faker with collision rehash against the registry and the source text. Registry persists per output directory.

## 6. CLI and files
`bin/anon` wraps `uv run --project engine anon`. Exit codes: 0 ok, 2 usage, 3 leak or gate failure, 4 missing key or dependency.
```
anon init-key
anon run <file|dir>... -o workspace/out [--config c.yaml] [--extra-terms t.yaml]
anon verify <doc.anon.ext> --map <doc.map.enc>
anon qa-packet <doc.anon.ext> -o <doc.qa_packet.json>
anon qa-run <doc.qa_packet.json> -o <doc.findings.json>
anon qa-apply <doc.findings.json> --map <doc.map.enc> -o <doc.extra_terms.yaml>
anon gate <doc.report.json> --findings <doc.findings.json> [--human-reviewed]
anon restore <doc.anon.ext> --map <doc.map.enc> -o <restored.ext>
```
Input formats: UTF-8 text and Markdown. Other formats convert first.

## 7. Pass 3 findings schema
```json
{"doc_id": "str",
 "findings": [{"quote": "exact text from the anonymized document", "category": "name|contact|id|secret|org|location|quasi_identifier|context", "severity": "high|medium|low", "reason": "str", "suggested_action": "replace|generalize|human_review"}],
 "reidentification_risk": {"level": "high|medium|low", "rationale": "str"}}
```
`quasi_identifier`, `context` and `human_review` findings are never auto-applied. They fail the gate until a person accepts them (I9).

## 8. Known limits
- An organization's own name and acronyms can look ordinary to every pass. Put them in `terms.local.yaml`.
- Quasi-identifiers are reported, not rewritten. Only a person can judge them.
- Style, topic and rare events can identify an author. This tool does not address stylometry.
- Date shifting uses one keyed offset per key. One known date reveals the offset, and so all others.
- Non-US surrogate phone numbers keep their format and may match a real number.
- Input is English-first: the spaCy model is English, so other languages rely on patterns and the auditor.
- The `gliner2`, `opf`, `anthropic` and `ollama` paths were tested only with fakes or not at all. See the summary report.
