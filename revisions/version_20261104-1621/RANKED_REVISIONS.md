# Ranked targeted revisions

These are additions to the provisional technical-concept baseline, not a sentence-level redline of an application that was never supplied. Hard program/eligibility gates come first. Priorities are editorial heuristics, not estimated increases in funding probability. Read [EVAL_METRIC](EVAL_METRIC.md) for the exact formula.

## Gate first: identify an eligible program and applicant

Supply applicant country/legal status, actual program/call, requested amount, duration and partners. Prefer a direct technical route for a software-development ask. Journalism, emergency and Bitcoin routes each require a real qualifying activity; do not manufacture one through vocabulary changes.

## Scored priorities

|Order|Edit|Priority|Neighbor support|Effort|Factor|
|---:|---|---:|---:|---:|---|
|1|Name the user, threatened information and workflow; validate demand|10.125|100.0%|1|validated_need|
|2|Make open release concrete while protecting real data|7.3618|63.6%|1|adoption|
|3|Turn module contracts into a costed delivery plan|6.5847|37.7%|1|delivery|
|4|Explain the tool's distinct place beside secure-submission systems|4.9219|38.2%|1|technical_case|
|5|Supply a transparent activity-linked budget and ask|4.75|0.0%|1|economics|
|6|Secure a pilot and a maintenance/adoption owner|3.1875|50.0%|2|adoption|
|7|Replace broad safety claims with a privacy–utility–adoption evaluation plan|2.3166|37.3%|2|measurement|
|8|Write the abstract around a bounded user outcome|1.5592|38.6%|1|communication|
|9|Budget independent security and restoration review|1.4896|25.4%|3|measurement|

### 1. Name the user, threatened information and workflow; validate demand

Add one specific user group/country, the sensitive documents they handle, the adversary and current workaround. Obtain consent-safe interviews or a partner request. Treat intended civic users in the spec as a hypothesis until validated.

**Acceptance check:** At least one inspectable demand artifact and a clear harm → workflow → intervention chain; publish no sensitive identities.

**Evidence/diff:** The selected precedents explicitly protect civic/source/communication workflows. This supports user-specific framing, not a claim their applications contained demand validation.

**Neighbors:** otf-securedrop-audit, otf-globaleaks, otf-mapeo, otf-dcomms, ned-anticorruption, otf-qaul, otf-rcbox, otf-dangerzone-audit. [Official criterion/source](https://www.opentech.fund/).

**Priority inputs:** gap=0.75, confidence=0.9, effort=1, support=1.0. Inference + known baseline evidence gap.

### 2. Make open release concrete while protecting real data

Specify the deliverable code/license, release tags, install documentation, synthetic benchmarks and public remediation notes. Keep source documents, keys and restoration maps out of shared artifacts.

**Acceptance check:** Public artifacts are usable without the sensitive corpus; an owner is assigned for releases and support.

**Evidence/diff:** These precedents explicitly expose reusable tools. Open distribution strengthens reuse; it does not make confidential beneficiary data publishable.

**Neighbors:** otf-globaleaks, otf-mapeo, otf-qaul, ned-anticorruption, otf-securedrop-audit. [Official criterion/source](https://opensats.org/apply).

**Priority inputs:** gap=1, confidence=0.9, effort=1, support=0.635965. Conditional criterion: exact license rules vary by funder.

### 3. Turn module contracts into a costed delivery plan

Add accountable lead, team experience, calendar, dependencies and milestone acceptance criteria: minimum local prototype, independent review, partner pilot, stable release and maintenance handover. Choose actual duration and staffing instead of invented commitments.

**Acceptance check:** Each milestone has owner, date, deliverable, verification and cost; claimed team availability is confirmed.

**Evidence/diff:** The dated deployment/product-maturity awards demonstrate bounded funded work. They do not reveal the original application schedule.

**Neighbors:** otf-dcomms, otf-rcbox, otf-globaleaks. [Official criterion/source](https://digital-strategy.ec.europa.eu/en/funding/call-proposals-journalism-partnerships-collaborations-2025).

**Priority inputs:** gap=0.75, confidence=0.85, effort=1, support=0.377193. Inference + known baseline evidence gap.

### 4. Explain the tool's distinct place beside secure-submission systems

Add a workflow diagram showing where sensitive text enters, what is transformed, where the key/map lives, who can restore it, and what optional QA sends off-device. Compare content pseudonymization with secure transport, document isolation and metadata removal. Do not claim those are interchangeable.

**Acceptance check:** Each claimed improvement has a testable baseline comparison; restoration rights and residual context risks are explicit.

**Evidence/diff:** SecureDrop/GlobaLeaks protect document receipt/handling. Neither establishes a funded reversible-pseudonymization mechanism in this sample.

**Neighbors:** otf-securedrop-audit, otf-globaleaks, ned-anticorruption. [Official criterion/source](https://www.opentech.fund/security-safety-audits/securedrop-security-audit/).

**Priority inputs:** gap=0.5, confidence=0.95, effort=1, support=0.381579. Mechanism gap analysis.

### 5. Supply a transparent activity-linked budget and ask

State requested amount, duration, rates, work allocation, audit/user-research costs, accessible deployment and maintenance. Show any co-financing only when the selected call requires it.

**Acceptance check:** Every cost maps to a deliverable and an eligible cost category; totals reconcile with the funding request.

**Evidence/diff:** Public award amounts are not original budget evidence. This revision rests on official application criteria, so historical-neighbor support is deliberately zero.

**Neighbors:** None; criterion-led. [Official criterion/source](https://fij.org/grants-faq/).

**Priority inputs:** gap=1, confidence=0.95, effort=1, support=0.0. Unknown proposal evidence; criterion-led.

### 6. Secure a pilot and a maintenance/adoption owner

Add an eligible partner's confirmed pilot workflow, integration owner, onboarding/support responsibilities and a post-grant maintenance plan. Specify language/hardware constraints and safe training materials.

**Acceptance check:** Pilot commitment and maintenance responsibility documented; field use has a consent and feedback plan.

**Evidence/diff:** Product maturity, easy deployment and usability recur in close technical comparators. Actual partner commitments remain a proposal requirement to obtain.

**Neighbors:** otf-globaleaks, otf-dcomms, otf-qaul, otf-mapeo. [Official criterion/source](https://www.opentech.fund/projects-we-support/supported-projects/dcomms/).

**Priority inputs:** gap=1, confidence=0.85, effort=2, support=0.5. Unknown proposal evidence, not established defect.

### 7. Replace broad safety claims with a privacy–utility–adoption evaluation plan

Add the KPI plan below with baseline, denominator, test corpus, target-setting process, independent reviewer and measurement date. Report per-language/entity failure rates rather than one aggregate accuracy number.

**Acceptance check:** Targets are agreed after baseline measurement; privacy misses and utility failures are both reported with uncertainty.

**Evidence/diff:** Sponsored assessments and usability-focused deployment support motivate inspectable evaluation. Exact KPI thresholds are analyst recommendations, not inferred winning thresholds.

**Neighbors:** otf-securedrop-audit, otf-dangerzone-audit, otf-dcomms. [Official criterion/source](https://pulitzercenter.org/grants-fellowships/opportunities-journalists/machine-learning-reporting-grants).

**Priority inputs:** gap=0.75, confidence=0.9, effort=2, support=0.372807. Method recommendation; no results supplied.

### 8. Write the abstract around a bounded user outcome

Use a plain-language problem, mechanism, deliverable, beneficiary outcome and ask. Say pseudonymization where mapping exists. State local/cloud boundaries, expected failure modes and human review rather than absolute anonymity or quantified funding odds.

**Acceptance check:** A reader can identify who benefits, how, what will be delivered and what remains risky in one paragraph.

**Evidence/diff:** The strongest analogues describe a specific protective workflow, not a generic claim about AI or privacy.

**Neighbors:** otf-securedrop-audit, otf-globaleaks, otf-dcomms. [Official criterion/source](https://www.opentech.fund/projects-we-support/supported-projects/dcomms/).

**Priority inputs:** gap=0.5, confidence=0.9, effort=1, support=0.385965. Editorial inference.

### 9. Budget independent security and restoration review

Include external review of key/map access, storage/log exposure, restoration correctness, surrogate collisions, QA export boundaries and adversarial context inference; document remediation and retest. Separate local-only deployment from optional cloud modes.

**Acceptance check:** Reviewer scope, cost and deliverables are explicit; no independent validation claim until the report exists.

**Evidence/diff:** These are sponsored assessment precedents, a different instrument from a cash development award.

**Neighbors:** otf-securedrop-audit, otf-dangerzone-audit. [Official criterion/source](https://securedrop.org/news/securedrop-completes-sixth-security-audit/).

**Priority inputs:** gap=0.75, confidence=0.95, effort=3, support=0.254386. Safety-validation recommendation.

## Safe draft abstract scaffold

> [Applicant] seeks [amount] over [duration] to help [confirmed users/geography] handle [specific sensitive documents] while reducing [documented disclosure risk]. We will deliver an open-source local-first pseudonymization workflow with consistent surrogates and encrypted restoration mappings, evaluate privacy leakage and task utility against [baseline], and pilot with [confirmed partner]. Optional external QA will use only approved transformed material under an explicit review policy. [Measured target] and [adoption outcome] will be reported with limitations; the tool does not promise irreversible anonymity or eliminate contextual re-identification risk.

Bracketed fields are unresolved inputs, not facts or commitments. Tailor the outcome and activity to a genuine eligible program. Fund-specific additions are in [the funder dossiers](README.md#funder-dossiers).

## KPI design

All thresholds below require baseline measurement and partner agreement; none is a claimed result or a threshold learned from past awards.

|Outcome|Definition and denominator|Verification|Target-setting|
|---|---|---|---|
|Direct-identifier leakage|Missed annotated sensitive spans / annotated sensitive spans, by language/entity/severity|Held-out consented/synthetic corpus; adjudicated labels; confidence intervals|Set maximum high-severity miss rate after baseline; separate rare entity classes|
|Contextual exposure|Successful adversarial attribution attempts / specified attempts, conditional on stated auxiliary-data access|Pre-registered threat scenarios and independent review; disclose attack limits|Reduce vs raw/redaction baseline; do not call an attack failure proof of anonymity|
|Restoration correctness|Exactly restored unedited eligible documents / eligible tested documents; irreversible-secret exceptions separate|Byte-level comparison and collision/variant tests|Require all supported invariants on release test corpus; edited outputs measured separately|
|Narrative/task utility|Blinded task success and human-rated readability compared with raw and redacted versions|Paired reviewer study; protect originals; measure false-positive distortion|Pre-agreed acceptable degradation; report both mean and harmful failures|
|Local boundary|Unapproved outbound payload events / tested execution paths|Network/log inspection for each configured backend|Zero unapproved events in tested configurations; state coverage limits|
|Operational usability|Completed safe workflows / attempted workflows; median correction time|Pilot observation and error logs with no original identifiers|Improvement over partner's current process, with hardware/language context|
|Adoption and durability|Active consenting pilot organizations, retained workflows and resolved issues / enrolled organizations|Partner confirmation and follow-up; avoid sensitive telemetry|Partner-agreed milestone and follow-up dates, not downloads alone|
|Civic/reporting result|Protected documentation/reporting tasks completed / planned eligible tasks|Partner/editor confirmation; distinguish contribution from causation|Program-specific outcome; never promise a funding decision or policy change attributable to tool alone|

