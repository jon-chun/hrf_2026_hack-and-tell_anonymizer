# Research workplan — 2026-11-04

Scope: all 15 organizations in dev/funders.md, up to 20 independently documented awards per organization. Twenty is a cap, not a target to fill with unsupported examples. Public selection evidence cannot establish causal success factors or calibrated funding probabilities. Research uses primary sources and identifies evidence gaps.

Proposal status: no grant proposal supplied. dev/chat_anon_v1_grok _20261104.md is technical background only; the refinement file is empty. User clarification pending. Do not invent applicant, geography, budget, partners, outcomes, or delivery dates. Independent funder research proceeds while pending.

Parallel read/research streams: (1) OTF, HRF Bitcoin, OpenSats, Mozilla; (2) FIJ, Journalismfund Europe, IJ4EU, Pulitzer; (3) CRD, Freedom House, EED, NED; (4) Creative Europe, OSF, ECPMF/MFRR. Agents write outside checkout; primary alone integrates repository artifacts.

Each award: actual named award/project, funder/program, award date if documented, award amount if documented, public project leader/role, contemporaneous funder people/roles (never infer selection responsibility), purpose, direct source URLs, unknowns, and six evidence-coded similarity dimensions. Retrospective project pages are proxies for funded work, not recovered application text.

Similarity dimensions (0 absent/not described, 1 partial/adjacent, 2 explicit central match, null insufficient evidence): privacy/security tooling; local/offline operation; consistent/reversible text pseudonymization; long-form/journalistic/civic text workflow; vulnerable civic users; open-source/public-good distribution. These describe the technical background, subject to user confirmation. Differentiate absence of published evidence from proof of absence. Assess independent grant-readiness criteria separately from similarity.

Deliverables: evidence-backed funder dossiers; structured award inventory and all-observed-awards ranking; independent-factor EVAL_METRIC and scoring instructions; proposal baseline and unknowns; gap analysis and ranked revisions; methodology/limitations; automated artifact/link/schema and score-reproduction checks; dated Codex checkpoint. No commits/pushes/source overwrites.

Verification: cross-check corpus totals and funder coverage, deduplicate project awards, enforce <=20 per funder, require citations for every award, recompute scores and ranks from structured inputs, validate referenced files and rubric weights. Inspect representative highest-ranked source pages independently. Record source access dates and limitations.

## Milestone reached

Research and provisional analysis delivered in this version: 15 funder dossiers, 253 deduplicated public award/support records, 82 source URLs, weighted rubric, all-record ranking, nine similarity-weighted revisions with acceptance checks and KPI plan. Includes 20 residency cases and three sponsored security assessments, distinctly labeled. CRD/Freedom House have program-only evidence and no fabricated award cases. Primary integration expanded technology archives and narrowed 39 unsupported feature codes; audit retained.

Verification: `verify_analysis.py` passed 785 assertions, including source-link presence, full CSV/JSON/Markdown coverage, independent score/rank/revision arithmetic and 35 local links. Both baseline source hashes still match. No implementation checks, commits, merges or pushes. The configured uv cache on external volume was unavailable; used installed Python through `uv run --no-cache --no-project --python /usr/bin/python3`, with no packages downloaded.

Outstanding: user was asked for actual proposal summary/file and applicant facts after inviting questions. No answer yet. This report is explicitly provisional concept analysis; proposal-specific text diff and eligibility assessment remain pending. A later proposal-specific run should use a new timestamped version directory and retain this record.
