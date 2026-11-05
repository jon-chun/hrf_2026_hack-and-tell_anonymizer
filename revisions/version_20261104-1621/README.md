# Funder research and proposal gap analysis

**Provisional baseline:** the anonymizer technical specification, not a supplied grant application. Research date: 4 November 2026 (America/Los_Angeles).

The research covers all 15 listed funders and 253 publicly documented award/project-support records across 13 of them, capped at 20 per funder. CRD and Freedom House have program evidence but no safely attributable project-grant sample in this corpus. The 253 include 20 residency-support cases and 3 sponsored security assessments, explicitly labeled rather than represented as cash software-development grants.

## What to read

- [Weighted EVAL_METRIC and reasoning](EVAL_METRIC.md)
- [Every sampled award ranked, with score bounds](SIMILARITY_RANKING.md)
- [Ranked targeted revisions and KPI plan](RANKED_REVISIONS.md)
- [Baseline evidence and unknowns](PROPOSAL_BASELINE.md)
- [Full CSV: features, reasons, leaders, amounts, dates and citations](similarity_ranking.csv)
- [Machine-readable inventory](award_inventory.json) and [source catalog](source_catalog.json)
- [Verification results](VERIFICATION.md)

## Findings and implications

**OTF is the clearest technical-development route to investigate first**, because its public portfolio includes protected document handling, offline/local civic tools and deployment/usability work. This is a subject-matter fit judgment, not a confirmation of applicant eligibility or an open call. The next step is to identify the exact program, show user demand and demonstrate the tool's additional value. [OTF supported dComms](https://www.opentech.fund/projects-we-support/supported-projects/dcomms/).

**SecureDrop and GlobaLeaks are the strongest document-security comparisons.** SecureDrop's 80/100 score concerns a sponsored audit/support record, not a directly comparable cash-development award; GlobaLeaks' 72.5/100 record is a development/maturity grant. They motivate a clear distinction between secure receipt/handling and reversible transformation of narrative content. [SecureDrop assessment](https://www.opentech.fund/security-safety-audits/securedrop-security-audit/), [GlobaLeaks award](https://public.opentech.fund/documents/FY2017_OTF_Annual_Report.pdf).

**No sampled description documents the exact reversible consistent text-pseudonymization mechanism.** This is a finding about the inspected descriptions, not a claim that no funder has ever funded it or that novelty is disfavored. The proposal must justify the mechanism with privacy and utility evidence rather than claiming it is a proven funded pattern.

**NED and EED offer conditional civic-deployment comparisons.** NED's secure-submission and digital-rights records connect protective tools with reporting, training and civic users; EED's sample is more strongly about locally embedded democracy/media actors. Applicant geography, organizational status and genuine beneficiary demand remain unresolved. [NED active listing](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf), [EED support](https://www.democracyendowment.eu/support).

**Journalism funders generally need a real investigation or newsroom innovation project.** A general anonymizer build does not become investigative journalism by changing the abstract. Identify the actual story, team, editorial/outlet commitment and permitted costs; choose the appropriate innovation versus reporting program. [FIJ criteria](https://fij.org/grants-faq/), [IJ4EU scheme](https://investigativejournalismforeu.net/grants/investigation-support-scheme/), [Pulitzer reporting method](https://pulitzercenter.org/grants-fellowships/opportunities-journalists/machine-learning-reporting-grants).

**HRF BDF and OpenSats require an authentic ecosystem connection.** Privacy alone does not establish a Bitcoin/Nostr-related application. Conversely, a genuine long-form Nostr workflow may have a documented adjacency in YakiHonne; prove the integration rather than adding token language. [HRF remit and awards](https://hrf.org/latest/hrf-grants-800-million-satoshis-to-22-freedom-tech-projects-worldwide/), [OpenSats criteria](https://opensats.org/apply), [Nostr grant example](https://opensats.org/blog/fourteenth-wave-of-nostr-grants).

**CRD, Freedom House and ECPMF require instrument-specific treatment.** Protection, resilience, legal assistance and relocation are not generic software R&D. Consider a real eligible deployment/partnership where relevant; do not manufacture emergency status. [CRD Emergency Fund](https://crd.org/emergency-fund/), [Freedom House assistance](https://freedomhouse.org/pl/node/464), [ECPMF JiR](https://www.ecpmf.eu/support/journalists-in-residence/).

## Closest observed comparisons

Scores below use fixed, declared weights and conservative missing-data handling. Other reasonable weights can change positions. A highly similar project may still be the wrong program or instrument.

|Rank|Record|Similarity lower–upper|Interpretation|
|---:|---|---:|---|
|1|SecureDrop — sponsored security audit|80.0–80.0|sponsored audit/support service|
|2|RCBox: Extend East|75.0–75.0|grant/project support|
|3|GlobaLeaks — product maturity|72.5–72.5|grant/project support|
|3|Mapeo|72.5–72.5|grant/project support|
|3|qaul — Scaling, Usability, and Trust|72.5–72.5|grant/project support|
|6|Lower the Barrier to Adopt Awala|67.5–67.5|grant/project support|
|6|dComms|67.5–67.5|grant/project support|
|8|Stringer News|65.0–65.0|grant/project support|
|8|Promoting Anticorruption Mechanisms|65.0–65.0|grant/project support|
|8|Dangerzone — security assessment|65.0–65.0|sponsored audit/support service|
|8|Tails Sustainability|65.0–65.0|grant/project support|
|12|Enhancing Independent Journalism|60.0–60.0|grant/project support|
|12|YakiHonne|60.0–60.0|grant/project support|
|14|SeedSigner|57.5–57.5|grant/project support|
|14|Protecting Civil Society Access to a Free Internet and Digital Rights|57.5–57.5|grant/project support|

The full ranking retains sparse records. For example, recipient-only journalism announcements can score 7.5 with an upper bound 92.5 and only 15% known weight; their lower ranking reflects lack of published detail. They are not evidence of weak projects. Scores for awards with zero-coded features also remain documentation-dependent.

## The actionable proposal differences

The technical spec is comparatively specific about pipeline mechanics and risk boundaries. The main evidence gaps are the applicant/program, validated users, a bounded delivery team and calendar, a budget/ask, pilot ownership, and measured privacy/utility/adoption outcomes. The first revision is to ground the tool in a verified user workflow; next make open release, delivery and differentiation inspectable. [The ranked revision ledger](RANKED_REVISIONS.md) exposes every numeric assumption and supporting neighbor.

The readiness rubric has 60% observed weight and a design-evidence interval of 20–60/100. This is **not** a low funding probability: 40% of the information is unknown, and the evaluated document is a technical design rather than an application. No readiness score is invented for historical awards whose applications are unavailable.

## Coverage and sampling

|Funder|Records ranked|Coverage note|
|---|---:|---|
|Open Technology Fund|20|20-record cap; includes 3 labeled sponsored assessments|
|Human Rights Foundation — Bitcoin Development Fund|20|20-record cap; purposive sample|
|OpenSats|20|20-record cap; purposive sample|
|Mozilla Foundation — Mozilla Technology Fund|20|20-record cap; purposive sample|
|Civil Rights Defenders|0|Program-only evidence; no attributable grants reconstructed|
|Freedom House|0|Program-only evidence; no attributable grants reconstructed|
|European Endowment for Democracy|20|20-record cap; purposive sample|
|National Endowment for Democracy|20|20-record cap; purposive sample|
|Fund for Investigative Journalism|20|20-record cap; purposive sample|
|Journalismfund Europe|20|20-record cap; purposive sample|
|Investigative Journalism for Europe|17|Bounded public evidence sample; fewer than 20|
|Pulitzer Center|16|Bounded public evidence sample; fewer than 20|
|European Commission Creative Europe|20|20-record cap; purposive sample|
|Open Society Foundations|20|20-record cap; purposive sample|
|ECPMF / Media Freedom Rapid Response|20|Public residency-support cases; not software grants|

This is not an exhaustive historical inventory. Selection prioritizes relevance, readable official records and sufficiently attributable awards. Source archives vary in date, instrument and disclosure. The source-specific sampling limitations appear in each dossier. IJ4EU's selected round has 17 awards; Pulitzer includes16 public precedents. No missing projects were fabricated to reach 20. Current-call deadlines and the size fields in dev/funders.md are not assumed verified.

## Funder dossiers

- [Open Technology Fund](funders/otf.md)
- [Human Rights Foundation — Bitcoin Development Fund](funders/hrf-bdf.md)
- [OpenSats](funders/opensats.md)
- [Mozilla Foundation — Mozilla Technology Fund](funders/mozilla-mtf.md)
- [Civil Rights Defenders](funders/civil-rights-defenders.md)
- [Freedom House](funders/freedom-house.md)
- [European Endowment for Democracy](funders/european-endowment-for-democracy.md)
- [National Endowment for Democracy](funders/national-endowment-for-democracy.md)
- [Fund for Investigative Journalism](funders/fij.md)
- [Journalismfund Europe](funders/jfe.md)
- [Investigative Journalism for Europe](funders/ij4eu.md)
- [Pulitzer Center](funders/pulitzer-center.md)
- [European Commission Creative Europe](funders/creative-europe.md)
- [Open Society Foundations](funders/open-society.md)
- [ECPMF / Media Freedom Rapid Response](funders/ecpmf-mfrr.md)

## Evidence quality and methodological limits

Public project profiles, grant registers and grantee disclosures are proxies for funded work, not recovered applications. Reported goals are not verified outcomes. A winner-only corpus cannot separate necessary features from features common to unsuccessful applicants, estimate marginal funding lift, or identify private reviewer preferences. Historical organizations, staff titles and strategies can change.

The feature dimensions are separated by mechanism, architecture, workflow, users and distribution. They are conceptually useful but not proven statistically independent. The [dependence diagnostic](dependence_diagnostic.json) uses pairwise complete observations; constant dimensions, selection and missingness limit interpretation. No pair in this corpus exceeds absolute 0.6 correlation, but the all-zero observed pseudonymization dimension has no variance, so that statistic cannot validate the feature model.

Integrator review narrowed 39 initial feature codes to prevent counting anonymous credentials as text pseudonymization, self-hosting as fully offline, AI accountability as protective security tooling, or publicly funded humanitarian work as open-source distribution. [Coding audit](coding_audit.json). Program-level openness has been removed from Pulitzer project vectors where unsupported. Preliminary research notes under evidence/ retain their original, less calibrated counts/codes; the final inventory, codebook and audit control the report.

Some records share upstream funding: EC → IJ4EU/Journalismfund, and HRF → ecosystem organizations. Counts and similarity weights are not independent confirmations. OpenSats can fund different contributors within the same ecosystem; this is not a randomized sample. Source URLs are preserved even where the integrator could only inspect search-index text or encountered 403 responses. Citation presence has been validated; universal live availability has not.

Named public project leaders and documented funder roles are included where available. No confidential person is identified, no selector is inferred from job title, and no personal psychological or political profile is used as a persuasion strategy.

## Reproduce

From the repository root, using installed Python without package downloads or the unavailable external uv cache:

```sh
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/build_analysis.py
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/verify_analysis.py
```

Inputs are the saved evidence packets, eval_metric.json, proposal_baseline.json and revision_inputs.json. Rebuilding updates only generated files in this version directory; source documents are untouched. A later proposal-specific revision should use a new timestamped version directory.

