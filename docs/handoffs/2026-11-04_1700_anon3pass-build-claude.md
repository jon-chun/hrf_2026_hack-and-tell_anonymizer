# Handoff: anon3pass-build
- **Written:** 2026-11-04 16:59 PST  **Session:** 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec
- **Agent:** claude  **Stream:** main  **Continues:** none
- **Status:** Report, spec, three-pass engine and skills are finished in anon-artifacts/; nothing committed; live backends and a live /anonymize run remain untested.
- **Branch:** main  **HEAD:** 2614c70 Initial commit  **Working tree:** many staged files, none committed (listed in Gotchas)
- **Model/effort used:** Fable 5.1 then Opus 5.5, medium; workers Sonnet, medium  **Context at handoff:** unknown

## Goal (1–3 sentences)
Critique and correct the Grok chat in `dev/chat_anon_v1_grok _20261104.md`, then deliver a summary report, a tech spec and a Claude Code skills implementation in `anon-artifacts/`. The anonymizer runs at least three passes configurable in YAML: patterns and fuzzy matching, Python PII and secret libraries, and an AI agent leak check. Done means the report's numbers come from real runs.

## Done (this session)
- `anon-artifacts/report/summary-report.md`: critique, tool landscape, measured results, unverified list, decisions for the owner.
- `anon-artifacts/spec/tech-spec.md`, `anon-artifacts/README.md`, `anon-artifacts/terms.local.yaml.example`.
- `anon-artifacts/engine/`: package `anon3pass`, `config.yaml`, 215 passing tests, `eval/` with fixtures and two blind sets.
- `anon-artifacts/.claude/`: skills `anonymize`, `anon-qa`, `anon-restore`, agent `anon-leak-auditor`, guard hook. A fresh `claude -p` session found them, and the hook blocked a raw file read.
- Blind set 2 with final rules: 10 of 81 values leaked after passes 1 and 2, 0 of 81 after one audit round, 15 of 26 keep-words over-redacted.

## In progress (state on disk right now)
- Nothing half-finished. A cleanup command (removing `__pycache__` and `.pytest_cache`) moved to the background and may not have finished; those folders are harmless and gitignored by the root `.gitignore`.

## Next steps (ordered, concrete, each startable in <1 min)
1. Review `anon-artifacts/report/summary-report.md` sections 2 and 7 and choose the audit backend for high-risk documents — the owner's decision; set `pass3_agent_qa.backend` in `anon-artifacts/engine/config.yaml`.
2. Run `/anonymize` on a synthetic file from a session started in `anon-artifacts/`, after copying one from `engine/eval/fixtures/` to `workspace/raw/` — verify it reaches the gate. This full skill flow has never run live.
3. Test `bin/anon qa-run` with `backend: anthropic` on a synthetic packet — check `fallbacks="default"` is accepted on `client.beta.messages.stream` in `engine/src/anon3pass/qa.py`; the worker assumed it from docs showing it on `create`.
4. Mount `/Volumes/RESEARCH_SSD`, then test `backend: ollama` — `ollama list` must work first.
5. Reduce over-redaction by extending `pipeline.keep_public_entities` in `engine/config.yaml`, using `engine/eval/heldout` — do not tune on `engine/eval/heldout2`, and write a new blind set to measure the change.

## Decisions and why (things a fresh session must not re-litigate)
- Scope is `anon-artifacts/` only; the Finite mini-hack playbook was skipped for this session — owner's answer. Rejected: building a Finite demo as well.
- Default NER is Presidio with spaCy `en_core_web_lg` — owner's choice for speed of setup. GLiNER2 and OpenAI Privacy Filter stay as config options.
- Default audit backend is a Claude Code subagent — owner's choice. Rejected as defaults: Anthropic API, local Ollama.
- Mapping is an AES-256-GCM sidecar per document plus a registry per output directory — owner's choice. Rejected: plaintext JSON, irreversible placeholders.
- All detection runs on the original text and replacement happens once — otherwise surrogates get re-detected and replaced twice.
- Surrogate seeds come from a keyed HMAC — unkeyed seeding allows a dictionary attack on names.
- Secrets are irreversible by default — a vault of live credentials is a needless risk. Toggle: `secrets_policy.store_in_vault`.
- Auditors receive `known_surrogates` — these strings are already in the text, and the list took surrogate false alarms from 33 of 111 flags to 0 of 92.
- Quasi-identifier and context findings are never auto-applied and fail the gate until a person passes `--human-reviewed` — only a person can judge them, and agents never set the flag.
- Guard hook blocks protected paths in Bash rather than all non-`bin/anon` commands — the stricter version stopped ordinary work such as running tests.

## Gotchas / traps discovered
- Staged files: all of `anon-artifacts/`, `dev/`, `revisions/`, `docs/handoffs/codex/` and `transcripts/` were staged by something other than this session, probably another session in this checkout. This session staged nothing. Check before committing.
- `/Volumes/RESEARCH_SSD` is an unmounted stub, while `UV_CACHE_DIR`, `HF_HOME` and `OLLAMA_MODELS` point at it, so `uv` and `ollama` fail. This session set `UV_CACHE_DIR` to its scratchpad, and `engine/.venv` (577 MB) sits on the internal disk. `bin/anon` uses the venv directly to avoid this.
- Commit hooks will flag the deliberately fake credentials in `engine/eval/` and `engine/tests/`. gitleaks reported 12 hits, all fake values or their caches. Allowlist exact false positives and never use `--no-verify`.
- Scores on `engine/eval/fixtures` and `engine/eval/heldout` are tuned, not blind. Fixtures showed 0 of 121 while the first blind set showed 59 of 194.
- Fixtures share a registry in `run_eval.py`, which helps later documents. Run alone they leak 3 of 121.
- `gh repo view --json licenseInfo` has no `spdxId` field; use `.licenseInfo.key`.
- `claude agents` lists running sessions, not agent definitions, so it cannot test discovery.
- Project hooks and agents load only when Claude Code starts in `anon-artifacts/`.

## Verification state
- Tests: `cd anon-artifacts/engine && .venv/bin/python -m pytest tests -q` → 215 passed.
- Lint/type: not run; Pyright shows unresolved imports because the editor does not use the venv.
- Benchmarks: `PYTHONPATH=src .venv/bin/python eval/run_eval.py --configs pass1,pass2,pass1+2,pass1+2-noterms` → all configs ran; 8 of 8 round-trip excluding secrets with NER on. Scoring scripts for blind sets were in the session scratchpad and are not in the repo.

## Pointers (read these before anything else)
- `anon-artifacts/report/summary-report.md` — results and what was not verified.
- `anon-artifacts/spec/tech-spec.md` — invariants and module contracts.
- `anon-artifacts/engine/config.yaml` — all settings.
- No ADR written. The owner did not ask for one; the spec holds the lasting decisions.

## Open questions / risks
- Passes 1 and 2 leave about one value in eight, so the default audit can send real values to the provider — the owner decides the backend for sensitive documents.
- Results come from small synthetic English sets written by the same model family as the auditor, so they are probably optimistic — settled only by testing on real documents under review.
- The `gliner2` and `opf` adapters have never run, and the `opf` flags are guesses.
- Memory `ai-summit-mini-hack-protocol` tells future sessions to follow the hackathon playbook; the event deadline has passed — the owner may want it removed.

## How to recover detail if needed
- Previous session: `claude --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec`
- Ask it without loading it: `claude -p --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec --fork-session --output-format json "<question>"`
- Compaction snapshots: `~/.claude/handoffs/-Users-jonc-code-hrf-2026-hack-and-tell-anonymizer/auto/*_precompact.md`
