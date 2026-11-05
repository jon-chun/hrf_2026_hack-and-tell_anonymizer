# Proposal-specific NED comparison

**Synthetic exercise.** All RFA people, partner claims, figures and organizational history are fictional. The source proposal is the actual document evaluated for this exercise; its claims are not independently verified.

Proposal SHA-256: baa0e78dcd00ce7ad1d4b7e71f1c716867bc4d325fb82ea6c6d8739433f476d8

Applicant: fictional Lithuanian association, serving Russian regions remotely; request $168,400 over 12 months; pending $42,000 cost share. Eligibility remains conditional on actual applicant documentation and country/program review. NED says nongovernmental organizations based in established democracies may work on eligible countries, and identifies accountability, independent media and human rights among its priorities. The listed January 27, 2027 deadline and May 7 board date match its published schedule when checked. [NED application](https://www.ned.org/apply-for-grant/en/).

## Similarity model and all prior projects

The six factor weights and scoring rules are in [EVAL_METRIC](EVAL_METRIC.md). Proposal vector: **[2, 0, 0, 2, 2, 1]**: encrypted secure intake and safety are central; no local/offline processing or reversible text pseudonymization is described; reporting and rights documentation are central; at-risk contributors are explicit; public reporting is present but an open-source release is not. Zero means not described, not absent. This scoring measures program/workflow resemblance rather than selection probability. See [all 253 ranked records](similarity_ranking.csv) with per-factor explanations and sources, including 20 NED records. Original source evidence is in the [prior inventory](../version_20261104-1621/award_inventory.json).

## NED comparators

|Rank within NED|Project|Score bounds|Published difference and source|
|---:|---|---:|---|
|1|Enhancing Independent Journalism|100.0–100.0|Train journalists/activists in investigative reporting, advocate press freedom, maintain a secure independent-news platform. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|2|Promoting Anticorruption Mechanisms|95.0–95.0|Investigative reporting, digital/data skills and open-source secure whistleblower submission system. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|3|Strengthening the Digital Security and Resilience of Civil Society|92.5–92.5|Digital safety training, consultations, online resources and security assessments for civil society, media and rights groups. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|4|Protecting Civil Society Access to a Free Internet and Digital Rights|87.5–87.5|Translate/localize open-source anti-censorship, secure-communication and privacy resources; train activists. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|5|Raising Awareness of Authoritarian Influence|85.0–85.0|Research foreign information manipulation and create digital identification/defense tools. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|6|Promoting Critical Thinking Among North Koreans|75.0–75.0|Online written and video content featuring defectors on rights and democracy. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|7|Defending Human Rights and Assisting Victims of Repression|75.0–75.0|Document abuses, legal aid and court-case tracking for political prisoners. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|8|Promoting Freedom of Expression and Protections for Journalists|75.0–75.0|Rights training, legal-aid online platform/mobile app and legislative advocacy. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|9|Mapping Crimes Against Humanity|75.0–75.0|Use geospatial and open-source data to document potential crimes and advocate accountability. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|10|Advocating for Freedom of the Press and Freedom of Expression|75.0–75.0|Monitor/report press-freedom violations and share findings with advocacy community. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|11|Pursuing Accountability for War-Related Crimes|75.0–75.0|Collect/analyze aggression evidence and pursue legal redress. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|12|Strengthening Civic Oversight of Political Processes|67.5–67.5|Election-period analysis, official monitoring, publicized findings and irregularity reports. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|13|Promoting Independent Journalism|67.5–67.5|Data journalism, AI and verification training; democracy/governance reporting. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|14|Strengthening an Independent Digital Publication|67.5–67.5|Russian/Belarusian multimedia reporting on political developments. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|15|Strengthening Public Access to Independent Reporting and Analysis|67.5–67.5|News, analysis, investigative reporting and multimedia adaptation for accessibility. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|16|Enhancing Technologically Innovative Networks and Pathways to Increase Information Access|67.5–67.5|Collaborate on information-distribution tools for North Korea. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|17|Promoting Accountability and Transparency Through Investigative Reporting|67.5–67.5|Investigations, data-journalism mentorship and asset database expansion. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|18|Combating a Culture of Impunity Through Investigative Reporting|67.5–67.5|Construction-project database, investigative journalism, published findings. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|
|19|Strengthening Online Civic Engagement for Democracy Activists|67.5–67.5|Digital tools/platform for citizen collaboration, dialogue and activist networks. [Source](https://www.ned.org/wp-content/uploads/2026/02/2025-Annual-Report.pdf)|
|20|Promoting Transparency in Public Spending|67.5–67.5|Maintain/expand a tender and procurement visualization platform. [Source](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf)|

The NED grant list is a set of public descriptions, not original winning applications; published active dates are not necessarily award dates. Rankings do not establish why a project was funded. The original dataset includes anonymized projects; identities have not been inferred.

## Prioritized gap analysis and proposed edits

Priority uses readiness-factor weight × gap fraction × (0.5 + 0.5 × similarity-weighted neighbor support) × confidence ÷ effort, where support is calculated among the three named NED comparators below. Scores are editorial priorities, not funding probabilities. Neighbor support reflects whether the cited descriptions contain the relevant theme; it does not show the funder required a particular sentence.

### 1. Demonstrate realistic, safe delivery — 10.12

Specify which work is performed by diaspora staff versus in-country contributors, how each region is reached, contingency triggers, and what is paused if risk rises. Document legal/security review and avoid promising risk elimination.

**Acceptance check:** 12-region workplan, delivery owners, safe fallback and escalation criteria.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 15, gap 0.75, confidence 0.9, effort 1.

### 2. Fix monitoring definitions and targets — 7.12

Define whether 90 files is cumulative or incremental and whether 120 trained means 120 participants or 120 passes. Separate unique people from platform reach, disclose deduplication and geographic uncertainty, and set collection safeguards.

**Acceptance check:** KPI table has consistent baselines, periods, denominators, sources and responsible owners.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 10, gap 0.75, confidence 0.95, effort 1.

### 3. Strengthen evidence of demand and track record — 6.38

Provide verifiable examples of prior investigations, training outcomes and local need in the synthetic scenario, with privacy-preserving references; disclose which claims would require real supporting evidence.

**Acceptance check:** At least two representative examples and a baseline source are attached in a real application.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 15, gap 0.5, confidence 0.85, effort 1.

### 4. Substantiate costs and pending co-funding — 4.75

Reconcile 4.2 FTE by role, rates and months; itemize audit, legal support and evaluation; identify whether the $42,000 is additional or included in project cost and provide a no-match contingency.

**Acceptance check:** Budget reconciles to $168,400; pending cost share is labeled uncommitted; audit scope fits the budget.

**Evidence:** neighbor support 0.0%; comparators: none; official criteria and proposal arithmetic. Inputs: weight 10, gap 1, confidence 0.95, effort 1.

### 5. Clarify outcomes and attribution — 4.25

Distinguish outputs from outcomes: track verified reuse, referrals or responses and whether contributors report improved ability to work. Treat official action as contextual, not solely attributable to reporting.

**Acceptance check:** Each outcome has a measurable indicator, evidence source and realistic attribution language.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 10, gap 0.5, confidence 0.85, effort 1.

### 6. Specify secure evidence handling — 3.38

Replace the blanket ‘anonymized’ label with a precise de-identification process, consent, data minimization, access controls, retention, safe release review and known re-identification limits.

**Acceptance check:** Threat model, responsible reviewer and consent-based disclosure rules are stated; no guarantee of anonymity.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 15, gap 0.5, confidence 0.9, effort 2.

### 7. Improve editorial and outreach detail — 2.00

Describe how stories are selected, two-source verification exceptions and corrections, editorial independence, language/accessibility and safe audience feedback.

**Acceptance check:** Editorial workflow and correction policy are clear and match budgeted capacity.

**Evidence:** neighbor support 100.0%; comparators: ned-secure-media, ned-anticorruption, ned-digital-security. Inputs: weight 5, gap 0.5, confidence 0.8, effort 1.

## Specific numerical checks

- Budget lines sum to $168,400. Personnel plus contributors are $114,000, or 67.7% of the request; the text's 68% is a reasonable rounding.
- Category shares in the proposal are individually rounded; clarify the exact percentage basis if using a line-item budget.
- 9,800 to 22,000 means 12,200 additional records, about 1,017 per month if spread evenly over 12 months. Distinguish archived records from verified records.
- Eight courses plus two workshops must accommodate 120 people; if 80% of 120 pass, that is 96 passes. If the intended target is 120 passes, participation must be at least 150 at that pass rate.
- 640,000 to 1.2 million unique annual readers is an 87.5% increase. Platform totals do not by themselves establish cross-platform unique people or Russian-region location.
- The proposal describes both two annual security audits and an independent evaluation in a combined $6,500 line. Explain whether costs are included elsewhere and how the scope is feasible.

## Limits

This is a fictional practice proposal; no application was submitted and no representation about a real organization is made. NED's public criteria supersede this analyst rubric. Winners-only data cannot quantify funding uplift. Similarity uses descriptive public information and may change when source detail is unavailable or weights change.
