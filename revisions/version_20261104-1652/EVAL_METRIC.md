# EVAL_METRIC v1 — evidence, similarity and readiness

**Proposal-specific override:** The evaluated fictional NED proposal uses vector [2, 0, 0, 2, 2, 1], as explained in [DIFF_REPORT.md](DIFF_REPORT.md). The earlier anonymizer baseline and example readiness scores below are historical methodology examples, not this proposal's scores. Neighbor selection and priority inputs for this proposal are reported in the new diff report.

Research date: 4 November 2026 (America/Los_Angeles). Machine-readable definitions: [eval_metric.json](../version_20261104-1621/eval_metric.json). Earlier baseline: [PROPOSAL_BASELINE.md](../version_20261104-1621/PROPOSAL_BASELINE.md).

## What the metric can establish

This is an analyst-defined decision aid with two outputs: descriptive similarity to public funded-project records, and evidence of proposal readiness. It is **not a model of selection probability**. Public winners alone do not identify why projects won: we lack declined applications, applicant-pool composition, reviewer scores, original applications, and many budgets or private deliberations. No regression, causal inference or statistical independence claim is made.

Weights are explicit judgments, justified by the proposal's intended mechanism, official criteria and observed portfolio patterns. They are not coefficients estimated from successful applications. Program rules override this general rubric, including any official award criteria. Similarity never overrides eligibility.

## Gate before scoring

For each specific program, classify **pass / fail / unknown** for: applicant legal form/country; beneficiary geography; permitted activity; grant size/duration; call status; partners/outlet commitments; co-funding; license/dissemination restrictions. Unknown is an unresolved gate. A failed gate removes a route from an actionable application shortlist; it does not remove its award records from the research inventory.

Examples: reporting-only awards require an actual investigation/publication plan; relocation support requires an eligible threatened person; Bitcoin programs require a genuine ecosystem contribution; European consortium calls require qualifying partners. A wording change cannot fix a fundamentally ineligible project.

## A. Descriptive similarity factors (100%)

|ID|Dimension|Weight|Boundary and justification|
|---|---|---:|---|
|S1|Privacy/security tooling|25|Matches the core protective intervention. A tool that reduces disclosure/communication risk qualifies; reporting **about** surveillance or AI does not automatically qualify. OTF's security portfolio provides direct intervention comparables.|
|S2|Local/offline operation|15|Architecture under constrained trust/connectivity, separate from privacy intent. Offline/local processing=2; self-hosting without explicit offline operation=1; a cloud-only tool is not equivalent. Requires demonstration before claiming delivered capability.|
|S3|Consistent/reversible text pseudonymization|20|The distinctive transformation mechanism. Anonymous credentials, encryption or anonymous payments do not establish text pseudonymization. No requirement to mimic a winner's architecture if it weakens user safety.|
|S4|Long-form journalistic/civic text workflow|15|Task/workflow match: handling narrative documents or structured editorial/documentation work. Adjacent civic/communications/data tasks=1; clearly text/document-centered workflows=2. A shared political topic alone is insufficient.|
|S5|Vulnerable civic users|15|Users and operating context, separate from the data transformation. Explicit threatened journalists/defenders or marginalized civic users=2; general civic/public-interest audience=1. Target-user statements are not validated demand.|
|S6|Open-source/public-good distribution|10|Reusable delivery model. Explicit reusable open code/tools/methods=2; public outputs/materials without reusable OSS evidence=1. A nonprofit or publicly funded award does not itself establish an open license.|

Supporting examples: [OTF dComms](https://www.opentech.fund/projects-we-support/supported-projects/dcomms/), [OpenSats criteria](https://opensats.org/apply), [Creative Europe collaboration scope](https://digital-strategy.ec.europa.eu/en/funding/call-proposals-journalism-partnerships-collaborations-2025), and [NED active listing](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf). These sources support dimensions and boundaries, not the exact numeric weights.

**Coding:** 2=explicit central match; 1=partial/adjacent match; 0=no match described in inspected evidence; null=insufficient description to code. Zero is a conservative documentary code, not proof a project lacked a feature. Null is not zero in storage. A public recipient listing may leave five dimensions null; it must not receive an inflated score by renormalizing around its one observed dimension. Award features are supported by the URLs and reasons in the inventory. Program-level provisions must be labeled as such rather than passed off as measured project implementation.

For proposal vector p and award vector x, each dimension contributes:

`c_k = w_k × (1 − |p_k − x_k| / 2)`

`Similarity = sum(c_k)`, on a 0–100 scale because weights sum to 100. For null award values, the lower bound uses the least matching possible value in {0,1,2}; the upper bound uses the best possible value. Rank by **lower bound**, with ties sharing a rank. Report upper bound and known-weight coverage. A lower rank can reflect sparse documentation rather than actual dissimilarity. The baseline is all 2, so its lower-bound similarity simplifies to `sum(w_k × (x_k or 0) / 2)`.

All researched award records are retained, including low matches and different instrument types. Comparisons are not an exhaustive historical census. The maximum is 20 sampled records per listed funder; independent awards may belong to the same upstream network. Repeat awards are not independent evidence of a causal preference.

## B. Proposal-readiness factors (100%)

|ID|Factor|Weight|Evidence needed; do not double-count|
|---|---|---:|---|
|R1|Strategic fit|20|Exact program, eligible applicant/users and intended institutional result. This scores relevance beyond the mandatory gates; no points merely for repeating mission vocabulary.|
|R2|Validated need|15|User interviews, workflow observation, partner requests and the specific harm/bottleneck. User relevance belongs here; technical quality belongs in R3.|
|R3|Technical case and differentiation|15|Threat model, baseline alternatives, transformation design, leak/restoration boundaries and technical feasibility. Tests/results belong to R6, not a second architectural claim.|
|R4|Delivery capability|15|Named accountable team, track record, responsibilities, dependencies, milestones and risk owners. Distribution commitments belong to R5.|
|R5|Adoption and sustainability|10|Pilot partners, integration, training/localization, maintenance and public reuse plan. Count actual commitments rather than audience size aspirations.|
|R6|Outcomes and evaluation|10|Baseline, target, denominator, method, verification and reporting dates for privacy, utility and civic outcomes. Downloads do not substitute for safe successful use.|
|R7|Economics|10|Activity-linked costs, justified rates, eligible expenses, co-funding and ongoing cost. This evaluates resources, not the same delivery milestone twice.|
|R8|Narrative precision|5|Clear problem-to-action-to-outcome chain, truthful scope, appropriate language and concise ask. Style receives a modest weight because it cannot compensate for weak substance.|

Use 0=explicitly deficient/contradictory; 1=asserted or early design; 2=specific plausible plan; 3=credible evidence/pilot/commitments; 4=strong independently inspectable evidence with validation. **Null means unknown**, including a document that was never provided. Do not score an omitted application as if it had been rejected.

Weighted readiness points = `sum(weight × score/4)` over known factors. Show observed weight and an interval [known points, known points + unknown weight]. The normalized observed-only score may be shown for diagnostic context, never as an overall application score. Historical award listings generally do not support full R1–R8 coding, so this report ranks them using S1–S6 and does not fabricate their readiness scores. Full application-to-application readiness differences require the actual proposals.

The factor separation is conceptual, not statistically established. If one sentence supplies two factors, require distinct evidence: “we have partners” is not both validated need and an adoption commitment unless the source establishes both. The generated dependence report flags strongly correlated **descriptive** factors; no sample supports asserting causal independence.

## C. Funder-specific use and sensitivity

Technology routes emphasize the threat model, differentiated open artifact, safety/usability and maintenance. Journalism routes emphasize reporting novelty, editorial commitments, access and publication; the tool is an enabling cost, not an excuse to omit the investigation. Democracy routes emphasize locally rooted agency and an accountable civic outcome. Emergency/residency routes use documented threat and immediate assistance, not a software roadmap.

The general weights stay fixed for reproducibility. Recompute similarity with uniform weights and a civic-user-heavy profile (15/10/15/20/25/15); both are published in the ranking CSV. These alternatives expose weight sensitivity and are not independent confirmations. The actual call's published rubric takes precedence. Human reviewers should inspect tied or sparsely documented neighbors instead of interpreting one decimal place as meaningful precision.

## D. Similarity-weighted gap prioritization

A revision is linked to specific neighbor IDs and an independent official criterion. It must state the evidence gap, the edit/addition, an acceptance check, effort and confidence. For each revision, use unique referenced neighbors with nonzero lower-bound similarity. Within that neighborhood, normalize similarity weights; calculate support from the explicitly identified supporting neighbor subset. Exclude irrelevant award instruments and do not multiply support by duplicating an award.

`neighbor_support = sum(similarity of supporting neighbors) / sum(similarity of all selected neighbors)`

`priority = readiness_factor_weight × gap_fraction × (0.5 + 0.5 × neighbor_support) × evidence_confidence / effort`

Gap fraction is `(4 − score)/4` where the baseline has a readiness score. For unknown proposal evidence use 1 as a **research priority assumption**, not proof of a defect. Confidence and effort are analyst judgments on 0–1 and 1–3 scales; the revision ledger records them. Hard eligibility gates are handled first and are not traded against these numeric priorities.

If the observed awards do not describe a feature, report “not evidenced” rather than recommending its removal. Novelty can be valuable; absence of reversible pseudonymization in a sample does not show funders oppose it. The goal is to improve relevance and evidence while retaining truthful claims.

