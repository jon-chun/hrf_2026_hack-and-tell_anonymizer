"""Independently verify corpus coverage, rank arithmetic, revision arithmetic and local links."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
def load(name):
    return json.loads((ROOT/name).read_text())
data = load("award_inventory.json")
awards = data["awards_ranked"]
funders = data["funders"]
metric = load("eval_metric.json")
baseline = load("proposal_baseline.json")
checks = []
def check(condition, description):
    if not condition:
        raise AssertionError(description)
    checks.append(description)
weights = metric["similarity"]["weights"]
check(sum(weights)==100, "Similarity weights sum to100")
check(sum(metric["readiness"]["weights"].values())==100, "Readiness weights sum to100")
check(len(funders)==15 and len({f["slug"] for f in funders})==15, "All15 distinct funders covered")
source_funders = (ROOT.parent.parent/"dev/funders.md").read_text()
check(len(re.findall(r"^\[.+\]\(https://", source_funders, re.M))==15, "Funder-list source contains15 organizations")
check(all(0<=len(f["awards"])<=20 for f in funders), "Every funder stays within20-record cap")
check(len(awards)==sum(len(f["awards"]) for f in funders), "Structured funder counts equal global ranking")
check(len({a["id"] for a in awards})==len(awards), "Every award ID unique")
check(len({(a["funder_slug"],a["title"],str(a["year"])) for a in awards})==len(awards),
      "No duplicate funder/title/date record")
check(all(len(a["features"])==len(a["feature_reasons"])==6 for a in awards), "Six codes and reasons per record")
check(all(a["sources"] and all(urlparse(u).scheme=="https" and urlparse(u).hostname for u in a["sources"]) for a in awards),
      "Every award has parseable HTTPS citations")
check(all(a.get("date_basis") and a.get("leader_role") is not None and a.get("funder_people") for a in awards),
      "Date basis, project-role field and selection-role uncertainty preserved")
check(baseline["features"]==[2]*6, "Current provisional baseline explicit and matched to independent arithmetic")
last = 101
expected_rank = None
for i,a in enumerate(awards,1):
    vector = a["features"]
    # With p=2, independently reduce normalized L1 to weighted feature support.
    expected_low = sum(w*(x or 0)/2 for w,x in zip(weights,vector))
    expected_high = expected_low + sum(w for w,x in zip(weights,vector) if x is None)
    check(abs(expected_low-a["similarity_lower"])<1e-6 and abs(expected_high-a["similarity_upper"])<1e-6,
          "Arithmetic verified: "+a["id"])
    if a["similarity_lower"]!=last:
        expected_rank=i
    check(a["similarity_lower"]<=last and a["rank"]==expected_rank, "Ordering/tie verified: "+a["id"])
    last=a["similarity_lower"]
    check(a["similarity_lower"]<=a["similarity_upper"]<=100, "Bounds valid: "+a["id"])
with (ROOT/"similarity_ranking.csv").open(newline="") as inp:
    csv_rows=list(csv.DictReader(inp))
check({a["id"] for a in awards}=={r["id"] for r in csv_rows}, "CSV contains every ranked record exactly once")
check(len(csv_rows)==len(awards), "CSV row count reconciles")
markdown=(ROOT/"SIMILARITY_RANKING.md").read_text()
check(len([l for l in markdown.splitlines() if re.match(r"^\|\d+\|",l)])==len(awards),
      "Markdown ranking contains every record")
index={a["id"]:a for a in awards}
ri=load("revision_inputs.json")
rows=load("ranked_revisions.json")
total=sum(index[i]["similarity_lower"] for i in ri["neighborhood"])
for r in rows:
    support=sum(index[i]["similarity_lower"] for i in r["supports"])/total
    value=metric["readiness"]["weights"][r["factor"]]*r["gap_fraction"]*(.5+.5*support)*r["confidence"]/r["effort"]
    check(abs(value-r["priority"])<.0001, "Revision priority independently verified: "+r["id"])
check([r["priority"] for r in rows]==sorted([r["priority"] for r in rows],reverse=True), "Revision priorities sorted")
broken=[]
local_count=0
for path in ROOT.rglob("*.md"):
    if "evidence" in path.parts:
        continue  # Preliminary notes may use stream-local companion paths.
    for target in re.findall(r"\]\(([^)]+)\)",path.read_text()):
        target=target.strip("<>")
        parsed=urlparse(target)
        if parsed.scheme or target.startswith("#"):
            continue
        dest=(path.parent/unquote(parsed.path)).resolve()
        local_count+=1
        if not dest.exists():
            broken.append(str(path.relative_to(ROOT))+": "+target)
check(not broken, "All"+str(local_count)+" final-document local links resolve: "+str(broken))
warnings=[]
for s in baseline["sources"]:
    if "sha256" not in s:
        continue
    p=ROOT.parent.parent/s["path"]
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if digest!=s["sha256"]:
        warnings.append("Concurrent source drift since baseline read: "+s["path"])
source_urls=len(load("source_catalog.json"))
public_record_count=len(awards)
summary=[
    "# Verification","",
    "Artifact checks passed. This validates structure and arithmetic, not the truth of undisclosed application details, completeness of funder histories, or universal live URL availability.","",
    "- Funders: "+str(len(funders))+"/15.",
    "- Award/project-support records: "+str(public_record_count)+"; maximum20 per funder.",
    "- Unique cited source URLs: "+str(source_urls)+".",
    "- CSV/JSON/Markdown record counts and IDs reconcile.",
    "- Score bounds, all tied ranks and revision priorities independently recomputed.",
    "- Similarity and readiness weights each total100.",
    "- Every record has six codes/reasons, source URLs and explicit date/role fields.",
    "- "+str(local_count)+" final-document local links resolve.",
    "- "+str(len(checks))+" assertions passed.","",
    "Semantic integration review corrected39 initial feature codes; see coding_audit.json. The primary independently inspected SecureDrop audit, GlobaLeaks financing, dComms, NED active listing, OpenSats criteria/newer awards, Creative Europe records, OSF disclosures and CRD program evidence. Some OTF pages returned403, so unavailable content was not represented as fully live-verified.","",
    "## Source drift","",
    "\n".join("- "+w for w in warnings) if warnings else "Baseline source hashes still match their recorded reads.","",
    "## Reproduction","",
    "```sh",
    "rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/build_analysis.py",
    "rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/verify_analysis.py",
    "```","",
    "No package installation, implementation tests, commits, branches, merges or pushes were performed. Existing source and concurrent implementation files were read only.",""]
(ROOT/"VERIFICATION.md").write_text("\n".join(summary)+"\n")
print("PASS: "+str(len(funders))+" funders; "+str(public_record_count)+" records; "+str(source_urls)+" source URLs")
print("PASS: "+str(len(checks))+" assertions; ranking/CSV/JSON coverage, weights, scores, ties, revision priorities and local links")
for warning in warnings:
    print("NOTE: "+warning)

