# Verification

Artifact checks passed. This validates structure and arithmetic, not the truth of undisclosed application details, completeness of funder histories, or universal live URL availability.

- Funders: 15/15.
- Award/project-support records: 253; maximum20 per funder.
- Unique cited source URLs: 82.
- CSV/JSON/Markdown record counts and IDs reconcile.
- Score bounds, all tied ranks and revision priorities independently recomputed.
- Similarity and readiness weights each total100.
- Every record has six codes/reasons, source URLs and explicit date/role fields.
- 35 final-document local links resolve.
- 785 assertions passed.

Semantic integration review corrected39 initial feature codes; see coding_audit.json. The primary independently inspected SecureDrop audit, GlobaLeaks financing, dComms, NED active listing, OpenSats criteria/newer awards, Creative Europe records, OSF disclosures and CRD program evidence. Some OTF pages returned403, so unavailable content was not represented as fully live-verified.

## Source drift

Baseline source hashes still match their recorded reads.

## Reproduction

```sh
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/build_analysis.py
rtk proxy uv run --no-cache --no-project --python /usr/bin/python3 revisions/version_20261104-1621/verify_analysis.py
```

No package installation, implementation tests, commits, branches, merges or pushes were performed. Existing source and concurrent implementation files were read only.

