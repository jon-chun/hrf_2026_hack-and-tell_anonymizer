"""Rebuild the evidence rankings and report tables using Python's standard library."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT / name).read_text())
def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
def md(value):
    if value is None:
        return "Not publicly established"
    return str(value).replace("|", "/").replace("\n", " ")
metric = read("eval_metric.json")
baseline = read("proposal_baseline.json")
funders = []
for stream in ("technology", "democracy", "journalism", "europe"):
    for f in read("evidence/" + stream + ".json")["funders"]:
        f["research_stream"] = stream
        funders.append(f)
groups = read("evidence/journalism_all_awards.json")["groups"]
supplement = read("evidence/primary_supplement.json")
for f in funders:
    if f["slug"] in supplement:
        f["awards"].extend(supplement[f["slug"]])
        f["limitations"] += " Integrator expanded the sample to20 using additional official/grantee primary sources; supplemental records include explicitly labeled sponsored audits where applicable. The original stream notes are preliminary; the final inventory controls counts and coding."
for f in funders:
    if f["slug"] not in groups:
        continue
    g = groups[f["slug"]]
    f["awards"] = []
    for row in g["records"]:
        keys = ("id", "title", "program", "year", "amount", "leader", "leader_role", "purpose")
        a = dict(zip(keys, row))
        a.update(features=g["feature_vector"][:], feature_reasons=g["feature_reasons"][:],
                 funder_people="Individual award selector not published", sources=[g["source_url"]])
        if f["slug"] == "pulitzer-center":
            # Program-level openness is not individual-project implementation evidence.
            a["features"][5] = None
            a["feature_reasons"][5] = "Public-method orientation is program-level; award-specific open distribution insufficiently documented"
            if a["id"] in {"pc-01","pc-02","pc-03","pc-04","pc-05"}:
                a["sources"] = ["https://pulitzercenter.org/grants-fellowships/opportunities-journalists/machine-learning-reporting-grants"]
            if a["id"] == "pc-16":
                a["sources"] = ["https://pulitzercenter.org/people/tatsiana-ashurkevich"]
        if a["id"] in {"ij4eu-07","ij4eu-16"}:
            a["features"][4] = 2
            a["feature_reasons"][4] = "Refugee/affected-person subject matter explicitly described; reporting subject is not necessarily a tool user"
            # Avoid equating affected subjects with intended users of the intervention.
            a["features"][4] = 1
        f["awards"].append(a)

audit = []
def recode(a, index, value, reason):
    old = a["features"][index]
    if old == value:
        return
    audit.append({"id":a["id"],"dimension":index+1,"old":old,"new":value,"reason":reason})
    a["features"][index] = value
    a["feature_reasons"][index] = reason

for f in funders:
    for a in f["awards"]:
        # Apply the narrower final codebook consistently across research streams.
        if a["features"][2] not in (0, None):
            recode(a, 2, 0, "Secure communications/submissions do not document consistent reversible TEXT pseudonymization")
        if f["slug"] == "mozilla-mtf" and a["features"][0] == 1:
            recode(a, 0, 0, "AI accountability/environmental transparency is not documented privacy/security protective tooling")
        if a["id"] in {"os-blindbit","os-lawallet"}:
            recode(a, 1, 1, "Self-hosting is adjacent; offline operation is not documented in the cited description")
        if a["id"] == "hrf-seedsigner":
            recode(a, 1, 1, "Hardware signing suggests a local architecture; explicit offline grant scope not established in this award description")
        if f["slug"] == "european-endowment-for-democracy" and a["features"][0] == 1:
            recode(a, 0, 0, "A high-risk civic/media context alone does not document protective security tooling")
        if f["slug"] == "national-endowment-for-democracy" and a["features"][0] == 1:
            reason = a["feature_reasons"][0].lower()
            if not any(word in reason for word in ("security explicit","defense tools","secure platform","digital/operational")):
                recode(a, 0, 0, "Sensitive information/journalism alone does not establish a protective technical intervention")
        if a["id"] == "ned-mapping-crimes":
            recode(a, 5, 1, "Open-source evidence/data is not necessarily reusable open-source SOFTWARE")
        if a["id"] == "eed-humanitarian-kherson":
            recode(a, 5, 0, "Humanitarian benefit alone does not establish public artifact distribution")
        if a["id"] == "otf-llm-censorship":
            recode(a, 0, 0, "Censorship research alone does not establish protective tooling")
        if a["id"] == "otf-dcomms":
            recode(a, 5, 1, "Decentralization/self-hosting alone does not establish an open-source license in cited award text")
        if a["id"] == "OSFJ24-1":
            recode(a, 3, 1, "Technology/state-harm research is adjacent; a long-form text workflow is not specified")

assert len(funders) == 15
assert len({f["slug"] for f in funders}) == 15
awards = []
for f in funders:
    assert len(f["awards"]) <= 20, f["name"]
    for a in f["awards"]:
        assert len(a["features"]) == len(a["feature_reasons"]) == 6, a["id"]
        assert all(x in (0,1,2,None) for x in a["features"])
        assert a["sources"] and all(u.startswith("https://") for u in a["sources"])
        a["funder"] = f["name"]
        a["funder_slug"] = f["slug"]
        a["instrument"] = ("sponsored audit/support service" if "audit" in a["id"] else
                           "residency support" if f["slug"] == "ecpmf-mfrr" else
                           "fellowship/project" if "fellow" in str(a["program"]).lower() else "grant/project support")
        a["accessed"] = "2026-11-04"
        a["date_basis"] = "Source-reported year/period; original award date not independently established unless expressly stated"
        if f["slug"] == "national-endowment-for-democracy":
            a["year"] = "Active as of 2025-07-15" if "2025/10/" in a["sources"][0] else "Reported in 2025 annual report"
            a["date_basis"] = "Active/reporting period, not original grant award date"
        if a.get("funder_people") in (None, [], ""):
            a["funder_people"] = "Not publicly established for this award"
        if a.get("leader_role") is None:
            a["leader_role"] = "Not publicly established"
        a["feature_scope"] = "Public award/project description; stated intentions are not verified outcomes"
        awards.append(a)
assert len({a["id"] for a in awards}) == len(awards), "duplicate ID"
def score(vector, weights):
    lower = upper = coverage = 0.0
    for p, x, w in zip(baseline["features"], vector, weights):
        if x is None:
            values = [w * (1 - abs(p - v)/2) for v in (0,1,2)]
            lower += min(values)
            upper += max(values)
        else:
            c = w * (1 - abs(p-x)/2)
            lower += c
            upper += c
            coverage += w
    return round(lower,4), round(upper,4), round(coverage,4)
for a in awards:
    lo, hi, coverage = score(a["features"],metric["similarity"]["weights"])
    a.update(similarity_lower=lo,similarity_upper=hi,known_weight=coverage)
    for name, weights in metric["sensitivity"].items():
        a[name+"_lower"] = score(a["features"], weights)[0]
awards.sort(key=lambda a:(-a["similarity_lower"],a["funder"],a["id"]))
def ranks(items, field, outfield):
    previous = None
    for i,a in enumerate(sorted(items,key=lambda a:-a[field]),1):
        if a[field] != previous:
            rank = i
        a[outfield] = rank
        previous = a[field]
ranks(awards,"similarity_lower","rank")
for name in metric["sensitivity"]:
    ranks(awards,name+"_lower",name+"_rank")
for f in funders:
    local = [a for a in awards if a["funder_slug"] == f["slug"]]
    ranks(local,"similarity_lower","funder_rank")
save("award_inventory.json",{"research_date":"2026-11-04","baseline_status":baseline["status"],
     "funders":funders,"awards_ranked":awards})
save("coding_audit.json",audit)

with (ROOT/"similarity_ranking.csv").open("w",newline="") as out:
    fields = ["rank","funder_rank","id","funder","title","program","year","instrument",
              "similarity_lower","similarity_upper","known_weight","uniform_lower","uniform_rank",
              "civic_lower","civic_rank","amount","leader","leader_role","funder_people",
              "date_basis","features","feature_reasons","sources"]
    writer = csv.DictWriter(out,fieldnames=fields)
    writer.writeheader()
    for a in awards:
        row = {k:a.get(k) for k in fields}
        for k in ("features","feature_reasons","sources"):
            row[k] = json.dumps(row[k],ensure_ascii=False)
        writer.writerow(row)

readiness_weights = metric["readiness"]["weights"]
known = sum(readiness_weights[k] for k,v in baseline["readiness_scores"].items() if v is not None)
points = sum(readiness_weights[k]*v/4 for k,v in baseline["readiness_scores"].items() if v is not None)
save("readiness_result.json",{"known_weight":known,"known_points":points,
     "lower":points,"upper":points+100-known,"interpretation":"Partial design evidence only; not an application score or probability",
     "factors":baseline["readiness_scores"]})

lines = ["# All-sampled-awards similarity ranking","",
    "Baseline: provisional technical concept, not a supplied grant application. Scores describe published feature overlap, not merit or funding probability. Nulls produce bounds; zeros mean no match documented, not proven absence. Ties share ranks. Every inventory record appears below. Full six-factor reasons, people/roles, amounts and sources are in [the CSV](similarity_ranking.csv) and [JSON](award_inventory.json).","",
    "|Rank|Funder|Award/project|Similarity lower–upper|Known weight|Vector S1–S6|Evidence|",
    "|---:|---|---|---:|---:|---|---|"]
for a in awards:
    vector = "/".join("?" if x is None else str(x) for x in a["features"])
    source = "[source]("+a["sources"][0]+")"
    lines.append("|"+ "|".join(map(md,[a["rank"],a["funder"],a["title"],
       str(a["similarity_lower"])+"–"+str(a["similarity_upper"]),a["known_weight"],vector,source]))+"|")
(ROOT/"SIMILARITY_RANKING.md").write_text("\n".join(lines)+"\n")

# Pairwise correlation is a descriptive diagnostic; pairwise missing-data deletion is explicit.
pairs = []
for i in range(6):
    for j in range(i+1,6):
        vals = [(a["features"][i],a["features"][j]) for a in awards
                if a["features"][i] is not None and a["features"][j] is not None]
        if len(vals) < 3:
            r = None
        else:
            xs,ys = zip(*vals)
            mx,my = sum(xs)/len(xs),sum(ys)/len(ys)
            xx=sum((x-mx)**2 for x in xs); yy=sum((y-my)**2 for y in ys)
            r = None if not xx or not yy else sum((x-mx)*(y-my) for x,y in vals)/math.sqrt(xx*yy)
        pairs.append({"i":i+1,"j":j+1,"n":len(vals),"r":None if r is None else round(r,4)})
save("dependence_diagnostic.json",pairs)

profiles = {
"otf":("Best direct technical route, subject to live program and eligibility",
"Lead with a specific surveillance/censorship threat to civil-society users. Explain local handling, restoration-key risk, optional cloud QA and a usable deployment. Add partner demand, an independent security evaluation, language-specific tests and a maintenance budget."),
"hrf-bdf":("Conditional: genuine Bitcoin/freedom-technology contribution required",
"State the actual Bitcoin/Nostr/ecash or financial-freedom workflow served. Define a verifiable integration, maintainers and open artifacts. Do not insert a token Bitcoin reference into an unrelated general-purpose tool."),
"opensats":("Conditional: direct ecosystem contribution and open licensing",
"Provide a concise one-page case, inspectable repository/license, direct Bitcoin/Nostr utility and public education materials. A general privacy product without ecosystem benefit remains a weak route."),
"mozilla-mtf":("Conditional: match the actual current theme/program",
"Name the exact open call and public-interest community. Show a reusable open artifact, transparent evaluation and community stewardship. Historical AI/environmental awards do not prove a generic privacy fellowship is available."),
"fij":("Standalone software route weak; needs a qualifying investigation",
"Identify the new wrongdoing question, preliminary findings, sources, reporting roadmap and US English-language publication commitment. Budget the tool only where it enables eligible reporting costs; do not omit the investigation."),
"jfe":("Program-dependent: newsroom innovation or qualifying cross-border team",
"Select the actual microgrant versus cross-border program first. For cross-border reporting, specify journalists/countries, European public relevance, story plan and editorial outlets. For newsroom innovation, define a bounded prototype and audience benefit."),
"ij4eu":("Reporting-led route; eligible multinational investigation required",
"Open with the cross-border investigation and publication partners. Connect pseudonymization to a documented collaboration/source-protection bottleneck, risk assessment, hard costs and independent editorial judgment."),
"pulitzer-center":("Reporting-led route with concrete data method",
"Specify the underreported public-interest question, outlet commitment, data access and verified methodology. Separate privacy of source material from safely shareable code/methods. AI-accountability topic similarity alone is not product-grant eligibility."),
"civil-rights-defenders":("Emergency/partnership route, not established open product R&D",
"Connect a documented defender threat to a practical deployment/training intervention and safety outcome; consider a separate long-term implementation partnership. Do not present general software research as acute emergency relief."),
"freedom-house":("Emergency/resilience support only where actual need qualifies",
"Describe the verified threat, urgency, eligible short-term cost and how the intervention lets a defender/organization continue its work. Protect identities; a long software roadmap does not establish emergency eligibility."),
"european-endowment-for-democracy":("Conditional: eligible geography and locally rooted democracy actors",
"Lead with a named or safely pseudonymized local partner's democratic work, why ordinary support is unavailable and how the tool enables continuity/accountability. Provide references and a proportionate operational budget."),
"national-endowment-for-democracy":("Plausible civic deployment route; organizational eligibility unknown",
"Center a country/region and local accountability users. Link the tool to secure documentation/reporting, deliver training and maintenance, and connect activity costs to observable civic outcomes."),
"creative-europe":("Consortium workstream; program/call conditions must be checked",
"Develop a real transnational newsroom partnership with languages, work packages, distribution, editorial independence and shared evaluation. Check topic-specific co-financing; avoid confusing an intermediary grant with software funding."),
"open-society":("Program/relationship access unknown; history spans distinct strategies",
"Start with civic actors' ability to act safely and the implementing organization's capacity. Identify the relevant program and approach route before writing. Historical regional/Justice grants do not prove current eligibility."),
"ecpmf-mfrr":("JiR residency is a different instrument from software development",
"For a real relocation request, document journalism and verified threat. For the tool, seek a separate eligible partnership/training or capacity-support route; residency precedents do not support a product-development ask.")
}
save("funder_fit_profiles.json", {s:{"status":p[0],"targeted_edits":p[1]} for s,p in profiles.items()})
for f in funders:
    status,edits = profiles[f["slug"]]
    local = sorted([a for a in awards if a["funder_slug"]==f["slug"]],
                   key=lambda a:(-a["similarity_lower"],a["id"]))
    doc = ["# "+f["name"],"","Research date: 2026-11-04. Public evidence only; baseline is a technical concept, not a grant proposal.",
      "","## Program fit and targeted revision","",status+".", "",edits,"",
      "## Documented criteria and eligibility",""]
    for cat in ("criteria","eligibility"):
        for c in f.get(cat,[]):
            doc.append("- "+c["claim"]+" [Source]("+c["url"]+").")
    doc += ["","## Public people and roles","",
      "Roles below are bounded to their source dates. Institutional leadership is not evidence that someone selected a particular grant or prefers a personal narrative.",""]
    for p in f.get("people",[]):
        doc.append("- "+md(p.get("name"))+" — "+md(p.get("role"))+"; "+md(p.get("period"))+
          ". Award-specific selection role established: "+str(p.get("selection_role_known",False))+
          ". [Source]("+p["url"]+").")
    doc += ["","## Communication implications",""]
    for c in f.get("communication_advice",[]):
        doc.append("- "+c["advice"]+" [Evidence]("+c["evidence_url"]+"). "+
                   ("Analyst inference." if c.get("inference") else "Criterion-aligned recommendation; exact wording is not a funder quote."))
    doc += ["","## Coverage limits","",md(f.get("limitations")),"",
       str(len(local))+" sampled records; maximum permitted20. No record implies recovery of the original application. For projects with unnamed individual leaders, organizational recipients are reported as organizations, not invented project managers.",
       "","## Every sampled award: ranked comparison",""]
    for a in local:
        doc += ["### "+str(a["funder_rank"])+". "+a["title"]+" ("+a["id"]+")","",
          "- Program/date: "+md(a["program"])+" / "+md(a["year"])+".",
          "- Date basis: "+a["date_basis"]+".",
          "- Amount: "+md(a["amount"])+".",
          "- Public lead/recipient: "+md(a["leader"])+"; role: "+md(a["leader_role"])+".",
          "- Funder selection people: "+md(a.get("funder_people"))+".",
          "- Published purpose: "+md(a["purpose"]),
          "- Concept similarity: "+str(a["similarity_lower"])+"–"+str(a["similarity_upper"])+
             "/100; known weight "+str(a["known_weight"])+"%.",
          "- Factor vector: "+str(a["features"])+".",
          "- Reasoning: "+"; ".join("S"+str(i+1)+": "+r for i,r in enumerate(a["feature_reasons"]))+".",
          "- Evidence: "+", ".join("[source "+str(i+1)+"]("+u+")" for i,u in enumerate(a["sources"]))+".",""]
    (ROOT/"funders"/(f["slug"]+".md")).write_text("\n".join(doc)+"\n")

urls = {}
for f in funders:
    for key in ("criteria","eligibility","people"):
        for item in f.get(key,[]):
            urls.setdefault(item["url"],set()).add(f["name"]+" / "+key)
    for a in f["awards"]:
        for u in a["sources"]:
            urls.setdefault(u,set()).add(a["id"])
save("source_catalog.json", [{"url":u,"used_for":sorted(v),"access_date":"2026-11-04",
       "verification":"Accessed by research agent or primary; some sources only search-index accessible; not all links independently re-fetched by integrator"}
       for u,v in sorted(urls.items())])
counts = {f["name"]:len(f["awards"]) for f in funders}
save("analysis_summary.json",{"funders":len(funders),"award_records":len(awards),"counts":counts,
     "source_urls":len(urls),"coding_adjustments":len(audit),"readiness_known_weight":known,
     "readiness_bounds":[points,points+100-known],"exact_pseudonymization_matches":
     [a["id"] for a in awards if a["features"][2]==2]})
print(json.dumps(read("analysis_summary.json"),ensure_ascii=False,indent=2))

# Similarity-weighted revision ledger; assumptions are explicit and independently editable.
revision_inputs = read("revision_inputs.json")
lookup = {a["id"]:a for a in awards}
neighborhood = revision_inputs["neighborhood"]
assert len(neighborhood) == len(set(neighborhood))
denominator = sum(lookup[i]["similarity_lower"] for i in neighborhood)
revision_rows = revision_inputs["revisions"]
for row in revision_rows:
    assert set(row["supports"]).issubset(neighborhood)
    assert len(row["supports"]) == len(set(row["supports"]))
    support = sum(lookup[i]["similarity_lower"] for i in row["supports"]) / denominator
    row["neighbor_support"] = round(support,6)
    row["neighborhood"] = neighborhood
    row["priority"] = round(readiness_weights[row["factor"]] * row["gap_fraction"] *
        (0.5 + 0.5*support) * row["confidence"] / row["effort"],4)
revision_rows.sort(key=lambda r:(-r["priority"],r["id"]))
save("ranked_revisions.json",revision_rows)
revision_doc = ["# Ranked targeted revisions","",
    "These are additions to the provisional technical-concept baseline, not a sentence-level redline of an application that was never supplied. Hard program/eligibility gates come first. Priorities are editorial heuristics, not estimated increases in funding probability. Read [EVAL_METRIC](EVAL_METRIC.md) for the exact formula.","",
    "## Gate first: identify an eligible program and applicant","",
    "Supply applicant country/legal status, actual program/call, requested amount, duration and partners. Prefer a direct technical route for a software-development ask. Journalism, emergency and Bitcoin routes each require a real qualifying activity; do not manufacture one through vocabulary changes.","",
    "## Scored priorities","",
    "|Order|Edit|Priority|Neighbor support|Effort|Factor|",
    "|---:|---|---:|---:|---:|---|"]
for i,r in enumerate(revision_rows,1):
    revision_doc.append("|"+ "|".join(map(md,[i,r["title"],r["priority"],
       str(round(r["neighbor_support"]*100,1))+"%",r["effort"],r["factor"]]))+"|")
for i,r in enumerate(revision_rows,1):
    revision_doc += ["","### "+str(i)+". "+r["title"],"",r["change"],"",
       "**Acceptance check:** "+r["check"],"",
       "**Evidence/diff:** "+r["lesson"],"",
       "**Neighbors:** "+(", ".join(r["supports"]) if r["supports"] else "None; criterion-led")+
       ". [Official criterion/source]("+r["criterion_url"]+").","",
       "**Priority inputs:** gap="+str(r["gap_fraction"])+", confidence="+str(r["confidence"])+
       ", effort="+str(r["effort"])+", support="+str(r["neighbor_support"])+". "+r["status"]+"."]
revision_doc += ["","## Safe draft abstract scaffold","",
    "> [Applicant] seeks [amount] over [duration] to help [confirmed users/geography] handle [specific sensitive documents] while reducing [documented disclosure risk]. We will deliver an open-source local-first pseudonymization workflow with consistent surrogates and encrypted restoration mappings, evaluate privacy leakage and task utility against [baseline], and pilot with [confirmed partner]. Optional external QA will use only approved transformed material under an explicit review policy. [Measured target] and [adoption outcome] will be reported with limitations; the tool does not promise irreversible anonymity or eliminate contextual re-identification risk.","",
    "Bracketed fields are unresolved inputs, not facts or commitments. Tailor the outcome and activity to a genuine eligible program. Fund-specific additions are in [the funder dossiers](README.md#funder-dossiers).","",
    "## KPI design","",
    "All thresholds below require baseline measurement and partner agreement; none is a claimed result or a threshold learned from past awards.","",
    "|Outcome|Definition and denominator|Verification|Target-setting|",
    "|---|---|---|---|",
    "|Direct-identifier leakage|Missed annotated sensitive spans / annotated sensitive spans, by language/entity/severity|Held-out consented/synthetic corpus; adjudicated labels; confidence intervals|Set maximum high-severity miss rate after baseline; separate rare entity classes|",
    "|Contextual exposure|Successful adversarial attribution attempts / specified attempts, conditional on stated auxiliary-data access|Pre-registered threat scenarios and independent review; disclose attack limits|Reduce vs raw/redaction baseline; do not call an attack failure proof of anonymity|",
    "|Restoration correctness|Exactly restored unedited eligible documents / eligible tested documents; irreversible-secret exceptions separate|Byte-level comparison and collision/variant tests|Require all supported invariants on release test corpus; edited outputs measured separately|",
    "|Narrative/task utility|Blinded task success and human-rated readability compared with raw and redacted versions|Paired reviewer study; protect originals; measure false-positive distortion|Pre-agreed acceptable degradation; report both mean and harmful failures|",
    "|Local boundary|Unapproved outbound payload events / tested execution paths|Network/log inspection for each configured backend|Zero unapproved events in tested configurations; state coverage limits|",
    "|Operational usability|Completed safe workflows / attempted workflows; median correction time|Pilot observation and error logs with no original identifiers|Improvement over partner's current process, with hardware/language context|",
    "|Adoption and durability|Active consenting pilot organizations, retained workflows and resolved issues / enrolled organizations|Partner confirmation and follow-up; avoid sensitive telemetry|Partner-agreed milestone and follow-up dates, not downloads alone|",
    "|Civic/reporting result|Protected documentation/reporting tasks completed / planned eligible tasks|Partner/editor confirmation; distinguish contribution from causation|Program-specific outcome; never promise a funding decision or policy change attributable to tool alone|",""]
(ROOT/"RANKED_REVISIONS.md").write_text("\n".join(revision_doc)+"\n")

report = ["# Funder research and proposal gap analysis","",
    "**Provisional baseline:** the anonymizer technical specification, not a supplied grant application. Research date: 4 November 2026 (America/Los_Angeles).","",
    "The research covers all15 listed funders and253 publicly documented award/project-support records across13 of them, capped at20 per funder. CRD and Freedom House have program evidence but no safely attributable project-grant sample in this corpus. The253 include20 residency-support cases and3 sponsored security assessments, explicitly labeled rather than represented as cash software-development grants.","",
    "## What to read","",
    "- [Weighted EVAL_METRIC and reasoning](EVAL_METRIC.md)","- [Every sampled award ranked, with score bounds](SIMILARITY_RANKING.md)",
    "- [Ranked targeted revisions and KPI plan](RANKED_REVISIONS.md)",
    "- [Baseline evidence and unknowns](PROPOSAL_BASELINE.md)","- [Full CSV: features, reasons, leaders, amounts, dates and citations](similarity_ranking.csv)",
    "- [Machine-readable inventory](award_inventory.json) and [source catalog](source_catalog.json)",
    "- [Verification results](VERIFICATION.md)","",
    "## Findings and implications","",
    "**OTF is the clearest technical-development route to investigate first**, because its public portfolio includes protected document handling, offline/local civic tools and deployment/usability work. This is a subject-matter fit judgment, not a confirmation of applicant eligibility or an open call. The next step is to identify the exact program, show user demand and demonstrate the tool's additional value. [OTF supported dComms](https://www.opentech.fund/projects-we-support/supported-projects/dcomms/).","",
    "**SecureDrop and GlobaLeaks are the strongest document-security comparisons.** SecureDrop's80/100 score concerns a sponsored audit/support record, not a directly comparable cash-development award; GlobaLeaks'72.5/100 record is a development/maturity grant. They motivate a clear distinction between secure receipt/handling and reversible transformation of narrative content. [SecureDrop assessment](https://www.opentech.fund/security-safety-audits/securedrop-security-audit/), [GlobaLeaks award](https://public.opentech.fund/documents/FY2017_OTF_Annual_Report.pdf).","",
    "**No sampled description documents the exact reversible consistent text-pseudonymization mechanism.** This is a finding about the inspected descriptions, not a claim that no funder has ever funded it or that novelty is disfavored. The proposal must justify the mechanism with privacy and utility evidence rather than claiming it is a proven funded pattern.","",
    "**NED and EED offer conditional civic-deployment comparisons.** NED's secure-submission and digital-rights records connect protective tools with reporting, training and civic users; EED's sample is more strongly about locally embedded democracy/media actors. Applicant geography, organizational status and genuine beneficiary demand remain unresolved. [NED active listing](https://www.ned.org/wp-content/uploads/2025/10/FINAL-Active-Grant-Listing-7-15-For-Listing-1.pdf), [EED support](https://www.democracyendowment.eu/support).","",
    "**Journalism funders generally need a real investigation or newsroom innovation project.** A general anonymizer build does not become investigative journalism by changing the abstract. Identify the actual story, team, editorial/outlet commitment and permitted costs; choose the appropriate innovation versus reporting program. [FIJ criteria](https://fij.org/grants-faq/), [IJ4EU scheme](https://investigativejournalismforeu.net/grants/investigation-support-scheme/), [Pulitzer reporting method](https://pulitzercenter.org/grants-fellowships/opportunities-journalists/machine-learning-reporting-grants).","",
    "**HRF BDF and OpenSats require an authentic ecosystem connection.** Privacy alone does not establish a Bitcoin/Nostr-related application. Conversely, a genuine long-form Nostr workflow may have a documented adjacency in YakiHonne; prove the integration rather than adding token language. [HRF remit and awards](https://hrf.org/latest/hrf-grants-800-million-satoshis-to-22-freedom-tech-projects-worldwide/), [OpenSats criteria](https://opensats.org/apply), [Nostr grant example](https://opensats.org/blog/fourteenth-wave-of-nostr-grants).","",
    "**CRD, Freedom House and ECPMF require instrument-specific treatment.** Protection, resilience, legal assistance and relocation are not generic software R&D. Consider a real eligible deployment/partnership where relevant; do not manufacture emergency status. [CRD Emergency Fund](https://crd.org/emergency-fund/), [Freedom House assistance](https://freedomhouse.org/pl/node/464), [ECPMF JiR](https://www.ecpmf.eu/support/journalists-in-residence/).","",
    "## Closest observed comparisons","",
    "Scores below use fixed, declared weights and conservative missing-data handling. Other reasonable weights can change positions. A highly similar project may still be the wrong program or instrument.","",
    "|Rank|Record|Similarity lower–upper|Interpretation|","|---:|---|---:|---|"]
for a in awards[:15]:
    report.append("|"+ "|".join(map(md,[a["rank"],a["title"],str(a["similarity_lower"])+"–"+str(a["similarity_upper"]),a["instrument"]]))+"|")
report += ["","The full ranking retains sparse records. For example, recipient-only journalism announcements can score7.5 with an upper bound92.5 and only15% known weight; their lower ranking reflects lack of published detail. They are not evidence of weak projects. Scores for awards with zero-coded features also remain documentation-dependent.","",
    "## The actionable proposal differences","",
    "The technical spec is comparatively specific about pipeline mechanics and risk boundaries. The main evidence gaps are the applicant/program, validated users, a bounded delivery team and calendar, a budget/ask, pilot ownership, and measured privacy/utility/adoption outcomes. The first revision is to ground the tool in a verified user workflow; next make open release, delivery and differentiation inspectable. [The ranked revision ledger](RANKED_REVISIONS.md) exposes every numeric assumption and supporting neighbor.","",
    "The readiness rubric has60% observed weight and a design-evidence interval of20–60/100. This is **not** a low funding probability:40% of the information is unknown, and the evaluated document is a technical design rather than an application. No readiness score is invented for historical awards whose applications are unavailable.","",
    "## Coverage and sampling","",
    "|Funder|Records ranked|Coverage note|","|---|---:|---|"]
for f in funders:
    count = len(f["awards"])
    note = ("Program-only evidence; no attributable grants reconstructed" if count==0 else
            "Public residency-support cases; not software grants" if f["slug"]=="ecpmf-mfrr" else
            "20-record cap; includes3 labeled sponsored assessments" if f["slug"]=="otf" else
            "Bounded public evidence sample; fewer than20" if count<20 else "20-record cap; purposive sample")
    report.append("|"+md(f["name"])+"|"+str(count)+"|"+note+"|")
report += ["","This is not an exhaustive historical inventory. Selection prioritizes relevance, readable official records and sufficiently attributable awards. Source archives vary in date, instrument and disclosure. The source-specific sampling limitations appear in each dossier. IJ4EU's selected round has17 awards; Pulitzer includes16 public precedents. No missing projects were fabricated to reach20. Current-call deadlines and the size fields in dev/funders.md are not assumed verified.","",
    "## Funder dossiers",""]
for f in funders:
    report.append("- ["+f["name"]+"](funders/"+f["slug"]+".md)")
report += ["","## Evidence quality and methodological limits","",
    "Public project profiles, grant registers and grantee disclosures are proxies for funded work, not recovered applications. Reported goals are not verified outcomes. A winner-only corpus cannot separate necessary features from features common to unsuccessful applicants, estimate marginal funding lift, or identify private reviewer preferences. Historical organizations, staff titles and strategies can change.","",
    "The feature dimensions are separated by mechanism, architecture, workflow, users and distribution. They are conceptually useful but not proven statistically independent. The [dependence diagnostic](dependence_diagnostic.json) uses pairwise complete observations; constant dimensions, selection and missingness limit interpretation. No pair in this corpus exceeds absolute0.6 correlation, but the all-zero observed pseudonymization dimension has no variance, so that statistic cannot validate the feature model.","",
    "Integrator review narrowed39 initial feature codes to prevent counting anonymous credentials as text pseudonymization, self-hosting as fully offline, AI accountability as protective security tooling, or publicly funded humanitarian work as open-source distribution. [Coding audit](coding_audit.json). Program-level openness has been removed from Pulitzer project vectors where unsupported. Preliminary research notes under evidence/ retain their original, less calibrated counts/codes; the final inventory, codebook and audit control the report.","",
    "Some records share upstream funding: EC → IJ4EU/Journalismfund, and HRF → ecosystem organizations. Counts and similarity weights are not independent confirmations. OpenSats can fund different contributors within the same ecosystem; this is not a randomized sample. Source URLs are preserved even where the integrator could only inspect search-index text or encountered403 responses. Citation presence has been validated; universal live availability has not.","",
    "Named public project leaders and documented funder roles are included where available. No confidential person is identified, no selector is inferred from job title, and no personal psychological or political profile is used as a persuasion strategy.","",
    "## Reproduce","",
    "From the repository root, using installed Python without package downloads or the unavailable external uv cache:","",
    "```sh",
    "rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/build_analysis.py",
    "rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/verify_analysis.py",
    "```","",
    "Inputs are the saved evidence packets, eval_metric.json, proposal_baseline.json and revision_inputs.json. Rebuilding updates only generated files in this version directory; source documents are untouched. A later proposal-specific revision should use a new timestamped version directory.",""]
(ROOT/"README.md").write_text("\n".join(report)+"\n")

# Polish generated prose without altering identifiers, source URLs or reproduction commands.
replacements = {
    "all15":"all 15", "and253":"and 253", "across13":"across 13", "at20":"at 20",
    "The253":"The 253", "include20":"include 20", "and3 sponsored":"and 3 sponsored",
    "SecureDrop's80":"SecureDrop's 80", "GlobaLeaks'72.5":"GlobaLeaks' 72.5",
    "score7.5":"score 7.5", "bound92.5":"bound 92.5", "only15%":"only 15%",
    "has60%":"has 60%", "of20–60":"of 20–60", "probability:40%":"probability: 40%",
    "includes3":"includes 3", "than20":"than 20", "has17":"has 17", "reach20":"reach 20",
    "absolute0.6":"absolute 0.6", "narrowed39":"narrowed 39", "encountered403":"encountered 403",
    "permitted20":"permitted 20", "to20":"to 20"
}
for path in [ROOT/"README.md", ROOT/"RANKED_REVISIONS.md", *sorted((ROOT/"funders").glob("*.md"))]:
    content=path.read_text()
    for old,new in replacements.items():
        content=content.replace(old,new)
    path.write_text(content)




