import csv,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
old=root.parent/"version_20261104-1621"
data=json.loads((old/"award_inventory.json").read_text())
weights=[25,15,20,15,15,10]
p=[2,0,0,2,2,1]
rows=[]
for a in data["awards_ranked"]:
 lo=hi=0
 for x,y,w in zip(p,a["features"],weights):
  v=[w*(1-abs(x-z)/2) for z in ([0,1,2] if y is None else [y])]
  lo+=min(v);hi+=max(v)
 rows.append((lo,hi,a))
rows.sort(key=lambda r:(-r[0],r[2]["id"]))
with (root/"similarity_ranking.csv").open("w",newline="") as f:
 w=csv.writer(f);w.writerow(["rank","funder","id","project","lower","upper","features","reasoning","source"])
 previous=None
 for i,(lo,hi,a) in enumerate(rows,1):
  if lo!=previous:rank=i
  previous=lo
  w.writerow([rank,a["funder"],a["id"],a["title"],lo,hi,json.dumps(a["features"]),"; ".join(a["feature_reasons"]),a["sources"][0]])
ned=[r for r in rows if r[2]["funder_slug"]=="national-endowment-for-democracy"]
source=Path("/Users/jonc/code/hrf_2026_hack-and-tell_anonymizer/dev/fictional_NED_proposal_russian-ngo.md")
out=["# Proposal-specific NED comparison","",
"**Synthetic exercise.** All RFA people, partner claims, figures and organizational history are fictional. The source proposal is the actual document evaluated for this exercise; its claims are not independently verified.",
"",
"Proposal SHA-256: "+hashlib.sha256(source.read_bytes()).hexdigest(),"",
"Applicant: fictional Lithuanian association, serving Russian regions remotely; request $168,400 over 12 months; pending $42,000 cost share. Eligibility remains conditional on actual applicant documentation and country/program review. NED says nongovernmental organizations based in established democracies may work on eligible countries, and identifies accountability, independent media and human rights among its priorities. The listed January 27, 2027 deadline and May 7 board date match its published schedule when checked. [NED application](https://www.ned.org/apply-for-grant/en/).",
"",
"## Similarity model and all prior projects","",
"The six factor weights and scoring rules are in [EVAL_METRIC](EVAL_METRIC.md). Proposal vector: **[2, 0, 0, 2, 2, 1]**: encrypted secure intake and safety are central; no local/offline processing or reversible text pseudonymization is described; reporting and rights documentation are central; at-risk contributors are explicit; public reporting is present but an open-source release is not. Zero means not described, not absent. This scoring measures program/workflow resemblance rather than selection probability. See [all 253 ranked records](similarity_ranking.csv) with per-factor explanations and sources, including 20 NED records. Original source evidence is in the [prior inventory](../version_20261104-1621/award_inventory.json).",
"",
"## NED comparators","",
"|Rank within NED|Project|Score bounds|Published difference and source|","|---:|---|---:|---|"]
for i,(lo,hi,a) in enumerate(ned,1):
 out.append(f'|{i}|{a["title"]}|{lo:.1f}–{hi:.1f}|{a["purpose"]} [Source]({a["sources"][0]})|')
out += ["","The NED grant list is a set of public descriptions, not original winning applications; published active dates are not necessarily award dates. Rankings do not establish why a project was funded. The original dataset includes anonymized projects; identities have not been inferred.",
"",
"## Prioritized gap analysis and proposed edits","",
"Priority uses readiness-factor weight × gap fraction × (0.5 + 0.5 × similarity-weighted neighbor support) × confidence ÷ effort, where support is calculated among the three named NED comparators below. Scores are editorial priorities, not funding probabilities. Neighbor support reflects whether the cited descriptions contain the relevant theme; it does not show the funder required a particular sentence.",
""]
comp=[a for _,_,a in ned if a["id"] in ("ned-anticorruption","ned-digital-security","ned-secure-media")]
if len(comp)!=3: comp=[a for _,_,a in ned[:3]]
lookup={a["id"]:lo for lo,hi,a in rows}
den=sum(lookup[a["id"]] for a in comp)
revs=[
("Demonstrate realistic, safe delivery",15,.75,.9,1,[a["id"] for a in comp],"Specify which work is performed by diaspora staff versus in-country contributors, how each region is reached, contingency triggers, and what is paused if risk rises. Document legal/security review and avoid promising risk elimination.","12-region workplan, delivery owners, safe fallback and escalation criteria."),
("Fix monitoring definitions and targets",10,.75,.95,1,[a["id"] for a in comp if a["features"][3]>=1],"Define whether 90 files is cumulative or incremental and whether 120 trained means 120 participants or 120 passes. Separate unique people from platform reach, disclose deduplication and geographic uncertainty, and set collection safeguards.","KPI table has consistent baselines, periods, denominators, sources and responsible owners."),
("Substantiate costs and pending co-funding",10,1,.95,1,[],"Reconcile 4.2 FTE by role, rates and months; itemize audit, legal support and evaluation; identify whether the $42,000 is additional or included in project cost and provide a no-match contingency.","Budget reconciles to $168,400; pending cost share is labeled uncommitted; audit scope fits the budget."),
("Specify secure evidence handling",15,.5,.9,2,[a["id"] for a in comp if a["features"][0]>=1],"Replace the blanket ‘anonymized’ label with a precise de-identification process, consent, data minimization, access controls, retention, safe release review and known re-identification limits.","Threat model, responsible reviewer and consent-based disclosure rules are stated; no guarantee of anonymity."),
("Strengthen evidence of demand and track record",15,.5,.85,1,[a["id"] for a in comp if a["features"][4]>=1],"Provide verifiable examples of prior investigations, training outcomes and local need in the synthetic scenario, with privacy-preserving references; disclose which claims would require real supporting evidence.","At least two representative examples and a baseline source are attached in a real application."),
("Clarify outcomes and attribution",10,.5,.85,1,[a["id"] for a in comp if a["features"][3]>=1],"Distinguish outputs from outcomes: track verified reuse, referrals or responses and whether contributors report improved ability to work. Treat official action as contextual, not solely attributable to reporting.","Each outcome has a measurable indicator, evidence source and realistic attribution language."),
("Improve editorial and outreach detail",5,.5,.8,1,[a["id"] for a in comp if a["features"][3]>=1],"Describe how stories are selected, two-source verification exceptions and corrections, editorial independence, language/accessibility and safe audience feedback.","Editorial workflow and correction policy are clear and match budgeted capacity.")
]
scored=[]
for title,weight,gap,conf,eff,sup,edit,check in revs:
 support=sum(lookup[x] for x in sup)/den if den else 0
 score=weight*gap*(.5+.5*support)*conf/eff
 scored.append((score,title,edit,check,support,sup,weight,gap,conf,eff))
for i,r in enumerate(sorted(scored,reverse=True),1):
 score,title,edit,check,support,sup,weight,gap,conf,eff=r
 out += [f"### {i}. {title} — {score:.2f}", "",edit,"",f"**Acceptance check:** {check}","",f"**Evidence:** neighbor support {support:.1%}; comparators: {', '.join(sup) or 'none; official criteria and proposal arithmetic'}. Inputs: weight {weight}, gap {gap}, confidence {conf}, effort {eff}.",""]
out += ["## Specific numerical checks","",
"- Budget lines sum to $168,400. Personnel plus contributors are $114,000, or 67.7% of the request; the text's 68% is a reasonable rounding.",
"- Category shares in the proposal are individually rounded; clarify the exact percentage basis if using a line-item budget.",
"- 9,800 to 22,000 means 12,200 additional records, about 1,017 per month if spread evenly over 12 months. Distinguish archived records from verified records.",
"- Eight courses plus two workshops must accommodate 120 people; if 80% of 120 pass, that is 96 passes. If the intended target is 120 passes, participation must be at least 150 at that pass rate.",
"- 640,000 to 1.2 million unique annual readers is an 87.5% increase. Platform totals do not by themselves establish cross-platform unique people or Russian-region location.",
"- The proposal describes both two annual security audits and an independent evaluation in a combined $6,500 line. Explain whether costs are included elsewhere and how the scope is feasible.",
"",
"## Limits","",
"This is a fictional practice proposal; no application was submitted and no representation about a real organization is made. NED's public criteria supersede this analyst rubric. Winners-only data cannot quantify funding uplift. Similarity uses descriptive public information and may change when source detail is unavailable or weights change."]
(root/"DIFF_REPORT.md").write_text("\n".join(out)+"\n")
print("PASS",len(rows),"ranked records;",len(ned),"NED comparators; budget total",sum([78000,36000,16500,14000,13100,6500,4300]))

