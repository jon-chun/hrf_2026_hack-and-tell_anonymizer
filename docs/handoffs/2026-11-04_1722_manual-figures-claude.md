# Handoff: manual-figures
- **Written:** 2026-11-04 local  **Session:** 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec
- **Agent:** claude  **Stream:** main  **Continues:** 2026-11-04_1700_anon3pass-build-claude.md
- **Status:** README and manual committed at cdefca2; figures rendered but not yet embedded; PDF and DOCX not built; later work uncommitted.
- **Branch:** main  **HEAD:** cdefca2  **Working tree:** docs/figures changes uncommitted
- **Model/effort used:** Opus 5.5, medium  **Context at handoff:** about 91% of compaction window

## Goal (1–3 sentences)
Owner asked: review README.md and docs/MANUAL.md, add clear figures, and provide the manual as md, pdf and docx. Done when all three formats carry the figures and were visually checked.

## Done (this session)
- Figure sources in docs/figures: five .mmd, build_charts.py, render.sh. Render works: `timeout 110 docs/figures/render.sh`.
- Commit cdefca2 made because owner said "commit" mid-task. The pre-fix figure sources are in it.

## In progress (state on disk right now)
- Re-rendered fixed diagrams (anonymizer-pipeline, data-boundary, gate-decisions, grant-critic-pipeline, surrogate-consistency); fixed versions NOT yet visually checked. leak-results and edit-priorities charts were checked and are good.

## Next steps (ordered, concrete, each startable in <1 min)
1. Read docs/figures/{anonymizer-pipeline,gate-decisions,grant-critic-pipeline}.png — confirm no crossing or struck-through labels.
2. Edit docs/MANUAL.md — replace the ASCII diagram in 2.2; add captioned figures: pipeline and surrogate-consistency (2.2), gate-decisions (2.5 step 5), data-boundary (2.6), leak-results (2.11), grant-critic-pipeline (3.4), edit-priorities (3.6). Fix section 1.1 reference "section 3.6" to 3.7. Add a short rebuild section. Use descriptive alt text.
3. Edit README.md — embed anonymizer-pipeline, leak-results, grant-critic-pipeline; link MANUAL.pdf and MANUAL.docx.
4. Write docs/build_manual.py — copy MANUAL.md to a temp print file in docs/: drop the Contents block (PDF has a TOC), turn repo-relative links into plain text with the path, append make-pdf width directives such as {width=60%}. Run `~/.claude/skills/gstack/make-pdf/dist/pdf generate --cover --toc --no-confidential` for PDF and add `--to docx` for Word. Output docs/MANUAL.pdf and docs/MANUAL.docx. Never put {width=} in MANUAL.md because GitHub shows it as literal text.
5. Verify — pdftoppm pages and Read them; convert docx with soffice to PDF and Read pages; pdftotext word count against MD; check images present in both; re-run link check.
6. Report; do NOT commit further unless owner asks. Print push block if committed.

## Decisions and why (things a fresh session must not re-litigate)
- One Markdown source renders all formats, so they cannot drift. Rejected: Mermaid fences in MD, because PDF and DOCX pipelines and GitHub differ; use image files.
- No funder coverage chart: 11 of 13 funders sit at the cap, so it says nothing.
- Priority chart reads the saved report through regex, so its values match it.
- Excalidraw scenes are kept for editability.

## Gotchas / traps discovered
- zsh: a word starting with = errors, and $VAR holding a command does not split. Use bash scripts.
- `ls` inside compound commands has hung twice (rtk rewrite suspected). Avoid it; use find. Cap slow commands with timeout.
- `revisions/version_20261104-1621/verify_analysis.py` rewrites VERIFICATION.md; `git restore` it.
- Earlier-found: RESEARCH_SSD unmounted; set UV_CACHE_DIR to a writable path; `git branch -D` is denied, use -d.

## Verification state
- Tests: anon-artifacts/engine 215 passed. Docs build not yet run.

## Pointers (read these before anything else)
- docs/MANUAL.md, README.md, docs/figures/render.sh

## Open questions / risks
- Unpushed: cdefca2 is local only; the owner pushes.

## How to recover detail if needed
- Previous session: `claude --resume 0d646dbb-9acb-4f6c-b664-e72e1e30d7ec`
