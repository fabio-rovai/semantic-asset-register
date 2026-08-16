# Corrections

Findings in this register are never quietly edited. When a result changes because
it was wrong, the change is recorded here with the date, what was claimed, what is
now claimed, and who raised it.

Corrections made before first publication are recorded in
[`../BUILD_REPORT.md`](../BUILD_REPORT.md) under "Mistakes in this build, caught
before publication", because they never reached a reader.

## Format

```
### YYYY-MM-DD  SAR-Xnn on <asset>
Raised by: <name or issue link, or "internal review">
Was: <the claim as published>
Now: <the corrected claim>
Why: <what was wrong: the retrieval, the check, or the interpretation>
```

## Log

### 2026-08-16  Provenance of the two DCAT-US assets
Raised by: reader report, same day as publication
Was: `dcat-us-shacl` and `nara-restrictions` were presented simply as GSA and
National Archives assets retrieved from `raw.githubusercontent.com/DOI-DO/dcat-us`.
Now: both are recorded as retrieved from an **archived** repository.
`github.com/DOI-DO/dcat-us` was archived on 28 April 2026 and is read-only. The
live home is `github.com/GSA/dcat-us`, maintained by the Data.gov team on a
semi-annual cycle documented in its `MAINTENANCE.md`.
Why: the register harvested a superseded location without checking whether it was
still the canonical one. The check outcomes for those two payloads are unaffected,
because the bytes assessed are the bytes that repository still serves, and the
snapshot hashes are unchanged. What was wrong was the provenance, and provenance is
most of what this register claims to get right.

What the correction surfaced, which is a finding in its own right: as of
16 August 2026 the live `GSA/dcat-us` repository contains **no SHACL directory and
no Turtle files at all**, and `nara-restrictions.ttl` sits under
`DEPRECATED/vocabularies`. DCAT-US v3.0's canonical validation artefact is now
JSON Schema, following draft 2020-12. The SHACL shapes assessed here survive only
in the archived repository. A register that measures whether published semantic
assets can be relied upon should have caught that its own source was frozen, and
it did not.
