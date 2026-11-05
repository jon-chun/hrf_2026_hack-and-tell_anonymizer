# Handoff: compaction-0d646dbb
- **Written:** 2026-11-04 17:24 PST  **Session:** `0d646dbb-9acb-4f6c-b664-e72e1e30d7ec`
- **Agent:** claude  **Stream:** main  **Continues:** unknown (automatic record)
- **Status:** Automatic record written at an automatic compaction; the session continued from its summary. Not a curated handoff.
- **Branch:** main  **HEAD:** cdefca2 Add project README, user manual and figure sources  **Working tree:** 29 uncommitted

## Dev history
**Key decisions**
- One Markdown source renders all formats, so they cannot drift; rejected separate edits.
- Figures are image files, not Mermaid fences, because they must work on GitHub, in PDF and in Word.
- Print-only width directives live in a build script, because GitHub would show `{width=}` as literal text.
- No funder coverage chart: nearly uniform at the 20-record cap, so uninformative.
- Priority chart reads the saved report so its values cannot diverge.
- Excalidraw scenes kept for editability.
- Scope `anon-artifacts/` only, Finite hackathon playbook skipped: user's choice.
- Default NER Presidio + spaCy, default audit Claude Code subagent, mapping AES-256-GCM sidecar: user's choices; rejected alternatives remain config options.
- Detection runs once on original text; surrogates never re-scanned, avoiding double replacement.
- Keyed HMAC seeding; unkeyed seeding allows a dictionary attack on names.
- Secrets irreversible by default.
- Auditor gets `known_surrogates`: false alarms fell from 33/111 to 0/92, and the list reveals nothing new.
- Human-judgment findings fail the gate until a person passes `--human-reviewed`.
- Private key header never allowlisted, since that would hide real keys globally.
- Report blind set 2 as the trusted number, not tuned scores.

**Updates and pivots**
- Added a blind second test after tuning invalidated the first set's blindness.
- Reworked auditor quotes to identifier-only because contextual quotes never matched raw text.
- User's "commit" mid-task: committed sources only, then continued the figures work uncommitted.

**Dead ends and mistakes**
- Tuning on fixtures gave a misleading 0/121; use held-out sets written blind.
- Mermaid back-edges crossed nodes; use terminal "re-run" nodes.
- Running the grant verifier dirtied a tracked file; restore after.
- `claude agents` lists sessions, not definitions; test discovery with `claude -p` from the project folder.
- Known unfixed limit: a surname after an @ handle survived on the sample proposal; manual documents it.

**Standing instructions**
- Report status in percent complete and estimated time when asked.
- Agents never push; give the push block.

## Next tasks
1. **(In progress)** Edit `docs/MANUAL.md`: replace the 2.2 ASCII diagram; add captioned figures with descriptive alt text: pipeline and surrogate-consistency (2.2), gate-decisions (2.5 step 5), data-boundary (2.6), leak-results (2.11), grant-critic-pipeline (3.4), edit-priorities (3.6). Fix 1.1's "section 3.6" to 3.7. Add a short rebuild section. State in the boundary caption that anonymized text may contain missed values.
2. Edit `README.md`: embed anonymizer-pipeline, leak-results and grant-critic-pipeline; link `docs/MANUAL.pdf` and `docs/MANUAL.docx`.
3. Write `docs/build_manual.py`: make a temp print copy in `docs/`, drop the Contents block, convert repo-relative links to plain text with paths, add width directives (about 55% for tall figures). Run `~/.claude/skills/gstack/make-pdf/dist/pdf generate --cover --toc --no-confidential` for `docs/MANUAL.pdf`, and with `--to docx` for `docs/MANUAL.docx`. Remove the temp file.
4. Verify: `pdftoppm` pages and read them; convert DOCX with soffice to PDF and read pages; compare `pdftotext` word counts with the Markdown; confirm images and tables in both; re-run the link and anchor check. Avoid `ls`; use `timeout`.
5. Report outcome and limits, stating what stays uncommitted. Commit only if asked, then print the push block.

Open questions for the user: which audit backend for high-risk documents; whether to commit and push the figures and new formats (`cdefca2` is also unpushed); whether to remove the stale hackathon memory.

## How to recover detail if needed
- Full snapshot (git state, files edited, prompts, the complete summary): `/Users/jonc/.claude/handoffs/-Users-jonc-code-hrf-2026-hack-and-tell-anonymizer/auto/2026-11-04_172340_0d646dbb_precompact.md`
- Transcript: `/Users/jonc/.claude/projects/-Users-jonc-code-hrf-2026-hack-and-tell-anonymizer/0d646dbb-9acb-4f6c-b664-e72e1e30d7ec.jsonl`
- Resume: `claude --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec`
