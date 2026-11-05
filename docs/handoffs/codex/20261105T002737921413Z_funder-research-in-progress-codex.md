# Codex handoff: funder-research-in-progress

Written (UTC): 20261105T002737921413Z

Git snapshot: {"branch": "main", "head": "2614c70b397c5c3449a21e958df28247ad903506", "dirty": true}

Previous checkpoint: none

## Goal
Create a dated local research report for all 15 funders in dev/funders.md, up to20 publicly documented awards each, weighted scoring rubric, all-observed-awards similarity ranking and targeted proposal revisions.

## Completed
Created revisions/version_20261104-1621/WORKPLAN.md. Read technical background; original refinement file empty. Primary researched Creative Europe, OSF and ECPMF; structured draft60 records in /tmp/funder-research-20261104-1621/europe.json. These are drafts pending integration. Democracy and journalism agents returned preliminary files; asked them to expand/improve structured inventories.

## Decisions
User requested all15, up to20 awards each and parallel agents. AskUserQuestion equivalent async tool asked proposal baseline; no reply yet. Proceed only with explicitly provisional concept scenario, no invented applicant/budget/timeline or funding probabilities. New concurrent-session file anon-artifacts/spec/tech-spec.md supplies useful technical baseline; SHA256 3e19a0a02e828f8dccdf1a8f4ea124fd3a2f5cb85d3db00c7cc3b7a8d05ce504. Source spec intends human-rights users, consistent reversible pseudonymization, local processing with optional cloud QA on processed text, residual risk acknowledged. Existing Apache2 license. All6 concept dimensions can score2 as design intentions; no implementation verification.
One repository writer only: agents write /tmp. Do not edit anon-artifacts, dev, source documents or instructions. No commits, branches, merges or pushes.

## Remaining work
Primary must integrate 15 funders, validate/sanitize data and score all research records. Agents: technology_funders running (OTF,HRF Bitcoin,OpenSats,Mozilla); journalism_funders resumed to structure full20/20/17/16 award records; democracy_funders resumed to expand EED/NED to20 and investigate CRD public innovation grants. Agent artifacts /tmp/funder-research-20261104-1621/{technology,journalism,democracy,europe}.{json,md}; europe.md not created yet.
Original untracked2026-11-04-151814-bash-inputcode-bash-input.txt, dev/ and newly appearing anon-artifacts/ belong user/other session. Main HEAD2614c70b397c5c3449a21e958df28247ad903506. No staging. No services started.

## Next steps
1. Read agents' JSON, enforce15 funders and<=20 per funder with citations. Reconcile all awards listed in Markdown with structured inventory.
2. Create EVAL_METRIC.md, baseline.json/PROPOSAL_BASELINE.md, award rankings JSON/CSV/Markdown, funder dossiers, ranked revisions and reproducible scoring/verification script under revisions/version_20261104-1621/ (planned).
3. Verify score arithmetic, source/citation presence, vector/schema/ID validity, local links, coverage and sensitive-name handling; independently open top source records. Save final checkpoint.

## Verification
rtk --version ->0.48.0. rtk git status --short read-only shows original untracked files plus new artifacts. Source line counts102 technical background,0 refinement,71 spec; read spec fully. Structured europe.json created via apply_patch, not yet independently schema checked. Agents reported their JSON parsed; integration unverified.

## Risks and open questions
No actual grant proposal supplied; applicant eligibility, budget and team unknown. Public awarded project descriptions are not full applications. Winning-only data cannot identify causal success factors or funding probabilities. Confidential recipients/selectors remain undisclosed. Current call deadlines not verified and must not reuse dev/funders.md dates as facts. No paid APIs needed/authorized. No permission needed for local research; commits/pushes not authorized.

## References
revisions/version_20261104-1621/WORKPLAN.md
dev/funders.md
dev/prompt_grant-proposal-diff-critiques.md
anon-artifacts/spec/tech-spec.md
