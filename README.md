# Semantic Asset Register

[![CI](https://github.com/fabio-rovai/semantic-asset-register/actions/workflows/ci.yml/badge.svg)](https://github.com/fabio-rovai/semantic-asset-register/actions/workflows/ci.yml)

**A reproducible, evidence-based quality assessment of the vocabularies and
ontologies published by US federal agencies.**

Every finding here is anchored to a dated, hashed retrieval. Every check names
the authority it derives from and declares whether failing it breaks a
specification or merely departs from a convention. Publishers have a documented
right of reply.

- Method and its limits: [`docs/METHOD.md`](docs/METHOD.md)
- Results: [`docs/SCORECARD.md`](docs/SCORECARD.md)
- What was built and what could not be obtained: [`BUILD_REPORT.md`](BUILD_REPORT.md)
- Raw findings as RDF: [`results/findings.ttl`](results/findings.ttl)
- Write-up: [gov.tesseract.academy/research/semantic-asset-register](https://gov.tesseract.academy/research/semantic-asset-register)

## Why this exists

Ontology consultancies sell ontology assessment. Job descriptions in the field
ask for the ability to "assess and evaluate existing ontologies and make
recommendations for improvement and alignment with industry standards". Almost
nobody selling that service has published an assessment of a single named,
real-world ontology, and no published, reproducible quality assessment of the US
federal vocabulary corpus could be found.

Reproducible tooling does exist and this register builds on it rather than
pretending to be first. OOPS! has been scanning ontologies for pitfalls since
2014 and FOOPS! has scored FAIRness since 2021, both from the Ontology
Engineering Group at UPM, and the OBO Foundry has run a standing community
dashboard for years. What did not exist is a standing, contestable assessment of
what one government actually publishes. See the prior art section of
[`docs/METHOD.md`](docs/METHOD.md).

## The two ideas that make it defensible

**Normativity is separate from severity.** A check is *normative* only if failing
it violates a published specification, and it must cite the clause. Everything
else is *conventional*: a departure from community practice that the publisher
never agreed to, reported as a difference rather than a defect. Severity is an
independent axis, so a conventional finding can be high severity (an undeclared
licence blocks lawful reuse) and a normative one can be low severity (a wrong
media type that every client sniffs around). Collapsing these is why most
ontology quality reports get dismissed by the people they are about.

**Findings are W3C EARL assertions, using all five outcomes.** A SKOS concept
scheme carrying no OWL axioms is recorded `earl:inapplicable` for OWL profile
conformance, not `earl:failed`. A reasoner that times out yields
`earl:cantTell`, never a silent pass. Because the counts are published, a reader
who rejects the weighting can recompute the aggregate from
[`results/assessment.csv`](results/assessment.csv) without rerunning anything.

## The check catalogue

26 checks across seven dimensions, defined in
[`ontology/checks.ttl`](ontology/checks.ttl). Each carries `sar:derivesFrom`,
`sar:citation`, `sar:normativity`, `sar:severity` and `sar:appliesToKind`.

Normative checks cite W3C Recommendations, chiefly the six SKOS integrity
conditions S9, S13, S14, S27, S37 and S46, plus RDF syntax conformance, media
type correctness and OWL 2 consistency. One normative check cites government
policy rather than a standards body: OMB Memorandum M-15-13 requires federal
websites to serve only over HTTPS, which makes transport security a compliance
question for these publishers specifically.

## The model

[`ontology/sar.ttl`](ontology/sar.ttl) defines the register's own vocabulary,
reusing W3C EARL for assertions and aligning to MOD, the FAIR-IMPACT metadata
standard for semantic artefacts.

The central modelling decision is that assessments attach to a `sar:Snapshot`,
never to an abstract asset. A snapshot records the URL requested, the URL finally
resolved to, the HTTP status, the media type actually returned, the byte count
and a SHA-256 of the bytes. A publisher can therefore re-fetch and compare
hashes: if the hash changed, the finding may be stale and this register is wrong
to keep asserting it. That is the property that makes the results contestable
instead of merely assertive.

## Running it

```bash
pip install -r requirements.txt
./pipeline/setup.sh            # fetches ROBOT; needs java for the three OWL checks
python3 pipeline/probe.py      # retrieval  -> results/probe_results.json
python3 pipeline/assess.py     # checks     -> results/findings.ttl, assessment.csv
python3 pipeline/report.py     # scorecard  -> docs/SCORECARD.md
python3 pipeline/validate_results.py   # QA gate on the published results
python3 -m pytest tests/ -q    # 23 unit tests over the check implementations
```

The probe stage hits live government infrastructure, sleeps between requests and
identifies itself in the User-Agent. Please keep both properties.

Retrieved payloads are not committed. They are other publishers' artefacts, some
are tens of megabytes, and all are regenerable, with hashes recorded so a rerun
can prove whether they changed.

## If this register is wrong about your asset

Open an issue labelled `publisher-response`. Corrections are recorded in
`docs/CORRECTIONS.md` with the date and what changed; findings are never quietly
edited. The most useful response you can give is "this check does not apply to
us", because that is a defect in the catalogue rather than in your asset. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

Code MIT, ontology and results CC BY 4.0. Assessed artefacts remain their
publishers'. See [`LICENSE.md`](LICENSE.md).

## Citation

See [`CITATION.cff`](CITATION.cff).

---

Built by [Fabio Rovai](https://fabiorovai.com) at
[The Tesseract Academy](https://thetesseractacademy.com).
If you are trying to work out whether your own ontology estate would survive this
battery, the whole thing is open and runnable above, and
fabio@thetesseractacademy.com reaches a human.
