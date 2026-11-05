# Codex handoff: funder-report-provisional

Written (UTC): 20261105T004036532016Z

Git snapshot: {"branch": "main", "head": "2614c70b397c5c3449a21e958df28247ad903506", "dirty": true}

Previous checkpoint: 20261105T002737921413Z_funder-research-in-progress-codex.md

## Goal
Research all15 funders, up to20 public awards each, and provide weighted rubric, all-record similarity ranking and targeted grant-proposal edits. Research milestone complete; actual proposal-specific final evaluation awaits user input.

## Completed
revisions/version_20261104-1621/README.md is the entry point. Final evidence covers15 funders,253 deduplicated public support records and82 source URLs. Each funder has a dossier with criteria, public people/roles, limitations, all sampled awards and targeted edits. EVAL_METRIC.md separates similarity and readiness, with weights, reasons, formula and missing-data handling. SIMILARITY_RANKING.md and similarity_ranking.csv/award_inventory.json rank every record. RANKED_REVISIONS.md contains9 weighted revisions, acceptance checks, abstract scaffold and KPI plan. build_analysis.py and verify_analysis.py reproduce the analysis. Inputs are frozen under evidence/, proposal_baseline.json, eval_metric.json and revision_inputs.json.
Verified: 785 assertions pass;35 local links; independent arithmetic for253 scores/ranks and9 priorities. All capped<=20. Twenty residency cases and3 sponsored assessments are labeled distinctly. CRD and FreedomHouse have program evidence but0 reconstructed named grant awards. Narrowed39 unsupported feature codes in coding_audit.json. No exact documented reversible text-pseudonymization precedent in sampled descriptions.

## Decisions
User explicitly chose all15 funders, maximum20 prior grants per funder and parallel agents. Used primary official/grantee sources. Not a causal selection model or funding-probability estimate. Actual applications unavailable; public descriptions are proxies.
No actual grant proposal supplied. Asked async clarification initially and again after user said to ask any useful question. No answer received as of checkpoint. Provisional baseline uses anon-artifacts/spec/tech-spec.md (read-only concurrent-session source) plus original background and repo Apache2 license, all six features2 as DESIGN INTENT. Unknown applicant, country/legal status, budget, duration, team/pilot commitments. Do not pretend sentence redline or eligibility established.
No edits to original/concurrent sources, instructions or Claude files. No commits/branches/worktrees/merges/pushes authorized. One primary repository writer; agents used /tmp.

## Remaining work
User must identify proposal summary/file and applicant facts to support precise proposal-specific critique. Do not repeat funder research unnecessarily. Create a NEW timestamped version for further proposal-specific assessment; preserve this dated evidence.
All subagents completed: technology_funders, democracy_funders, journalism_funders and its pulitzer child. No running services. Raw agent outputs remain /tmp/funder-research-20261104-1621/ and are copied to evidence/. Original untracked dev/, anon-artifacts/, .claude/ and root session export belong user/other sessions. No tracked code changed.

## Next steps
1. On user response, read the actual supplied proposal and identify applicant/program facts, compare to PROPOSAL_BASELINE.md, then create a new version directory and recode it. Verify all scores with the included independent verification after adapting paths.
2. If no new proposal input, report research artifacts and limitation; no additional authority needed for local research.
3. Do not commit or push unless separately allowed; pushes remain prohibited.

## Verification
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/build_analysis.py ->15 funders,253 records,82 URLs.
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/verify_analysis.py ->PASS785 assertions. Re-read VERIFICATION.md and README.md. Baseline source hashes match. No code implementation tested. Source URL availability not universally live rechecked; several OTF pages403 and relied on official indexed reports.
Configured external uv cache inaccessible; default uv failed. Resolved using installed Python with no-cache/no-project flags, no installs or downloads.

## Risks and open questions
Missing proposal and applicant facts limit application-specific advice. Historical program/call conditions not assumed current. Winners-only evidence cannot identify causal success factors, statistically independent causal features or funding lift. Audit/residency and downstream/upstream grants not interchangeable or independent votes. Dates distinguish reporting/active-grant period from original award date. Named selectors not invented from executive titles.
Potential source drift from concurrent implementation: baseline hash recorded, matches verification. No permissions needed for local report continuation. No publication/commit/push.

## References
revisions/version_20261104-1621/README.md
revisions/version_20261104-1621/WORKPLAN.md
revisions/version_20261104-1621/VERIFICATION.md
revisions/version_20261104-1621/proposal_baseline.json
dev/funders.md
anon-artifacts/spec/tech-spec.md
