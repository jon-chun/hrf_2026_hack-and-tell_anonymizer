# Handoff: manual-formats-done
- **Written:** 2026-11-04 17:31 PST  **Session:** 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec
- **Agent:** claude  **Stream:** main  **Continues:** none
- **Status:** Figures embedded and manual built as Markdown, PDF and Word; all verified, nothing committed; next is the owner's commit decision.
- **Branch:** main  **HEAD:** cdefca2 Add project README, user manual and figure sources  **Working tree:** 30 uncommitted (figures, README, manual, build script, handoffs)
- **Model/effort used:** Opus 5.5  **Context at handoff:** not known

## Goal (1–3 sentences)
Add clear figures to `README.md` and `docs/MANUAL.md`, and provide the manual as Markdown, PDF and Word. Done when all three carry the same content and render cleanly.

## Done (this session)
- Seven figures embedded with captions and alt text in `docs/MANUAL.md`; three in `README.md`, which also links the PDF and Word files.
- Fixed the 1.1 cross-reference (now section 3.7) and added a rebuild appendix.
- `docs/build_manual.py` builds `docs/MANUAL.pdf` (32 pages) and `docs/MANUAL.docx` (22 pages when rendered by LibreOffice).

## In progress (state on disk right now)
- Nothing half-finished. All work is uncommitted; `cdefca2` is also not pushed.

## Next steps (ordered, concrete, each startable in <1 min)
1. Commit if the owner asks: stage everything from `git status`, including both handoffs and this one; verify with `git status` and `git log -1`. The pre-commit secret scan may refuse; resolve hits, never use `--no-verify`.
2. Print the push block for `main` (agents never push), then have the owner verify the remote matches local.
3. Open `docs/MANUAL.docx` in real Word to confirm rendering — only LibreOffice and the schema validator have checked it.

## Decisions and why (things a fresh session must not re-litigate)
- One Markdown source renders all formats — because separate edits drift. Alternative rejected: hand-editing PDF or Word.
- Word builds with pandoc, PDF with gstack make-pdf — because make-pdf's docx path merged code block lines onto one line and split inline code in table cells. Alternative rejected: make-pdf for both.
- Word keeps the manual's hyperlinked Contents list — because a pandoc TOC field can prompt for an update on opening. PDF uses make-pdf's generated contents page.
- Wide figures use `page=portrait` in the PDF — because auto-landscape separated figures from captions.
- `data-boundary` prints at 75% — because at 100% its caption fell onto the next page.
- Figures are image files, not Mermaid fences — because they must work on GitHub, in PDF and in Word. Width directives live only in the build script because GitHub shows them as literal text.
- Syntax highlighting is off in Word — because shell highlighting coloured option flags as if meaningful.

## Gotchas / traps discovered
- With highlighting off, pandoc references the `SourceCode` style but does not define it; `add_code_style` in the build script adds it.
- `ls` in a compound command hung a background shell for 27 minutes (rtk rewrites it to `eza`). Use `find` with `timeout`.
- `rm -f $VAR/*` is blocked by a safety check; use a new scratch folder instead.
- `/Volumes/RESEARCH_SSD` was an unmounted stub; set `UV_CACHE_DIR` to a scratch path for `uv`.
- Word-set comparisons report false misses for long names wrapped in table cells; check the document XML before treating them as lost text.

## Verification state
- Tests: not re-run; no code under `anon-artifacts/` changed in this stream.
- Word schema validator: passed on `docs/MANUAL.docx` (uv run with defusedxml and lxml).
- Figures: 7 of 7 in both formats, 18 of 18 tables in Word, no literal directives in either. Link and anchor check on README and manual found no bad links before the final appendix edit, which added no links.

## Pointers (read these before anything else)
- `docs/build_manual.py` — the whole build, including Word post-processing
- `docs/figures/render.sh` — redraws figures
- `docs/handoffs/2026-11-04_1722_manual-figures-claude.md` — earlier plan for this stream

## Open questions / risks
- Which audit backend for high-risk documents — owner decides.
- Whether to commit and push — owner decides.
- Stale hackathon entry in auto-memory: remove or keep — owner decides.
- Known cosmetic flaw: in the PDF, the lead-ins "Optional features:" and "Ranked edits:" sit at a page end, with their tables on the next page.

## How to recover detail if needed
- Previous session: `claude --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec`
- Ask it without loading it: `claude -p --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec --fork-session --output-format json "<question>"`
- Compaction snapshots: `~/.claude/handoffs/-Users-jonc-code-hrf-2026-hack-and-tell-anonymizer/auto/2026-11-04_172340_0d646dbb_precompact.md`
