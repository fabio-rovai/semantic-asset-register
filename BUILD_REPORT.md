# Build report

What was actually fetched, what was computed, what could not be obtained, and
which of my own mistakes were caught before publication. Counts live in
[`docs/SCORECARD.md`](docs/SCORECARD.md) and are computed, never typed.

Build date: 16 August 2026. All retrievals on that date from a UK network
location.

## What was fetched

28 assets from 10 publishers: Library of Congress (15), NASA (4), USGS (2),
NLM, USDA NAL, NOAA NCEI, GSA/CDO Council, National Archives (via DCAT-US),
NCI, and ESIP for SWEET.

Every asset in `data/seed_assets.json` returned HTTP 200 on the final probe.
That is a corrected position, not the first result: three of my initial seed
URLs were wrong guesses (MeSH, the USGS Thesaurus, and NIEM) and four more
pointed at HTML landing pages rather than RDF. Reporting "no RDF available"
off a bad guess would have been an unfair finding, so the seed was corrected
against live probes before any assessment was run.

Retrieved payloads are not committed. `results/probe_results.json` records the
requested URL, the URL finally resolved to, HTTP status, media type, byte count
and SHA-256 for every retrieval, which is enough to reproduce or falsify any
finding.

## What could not be obtained as RDF

Recorded in `sought_but_not_rdf` in `data/seed_assets.json`. A register that
lists only what worked is not a register of the estate.

- **NIEM 6.0** (NIEMOpen, an OASIS Open Project). The normative model is XSD.
  The only RDF-adjacent artefact found in `github.com/niemopen/niem-model` is a
  single JSON-LD context of 5,418 bytes at `json-ld/context.json`. The largest
  US federal data exchange standard has no RDF or OWL serialisation of its
  model. NIEM 6 documentation does discuss RDF entailments; that is a semantics
  story, not a published artefact.
- **EPA Substance Registry Services.** Requesting RDF returns HTML. No RDF
  representation was located.
- **NIST OSCAL.** Published as XML and JSON Schema. Machine readable, but not
  RDF, so scoring it against a battery defined over RDF graphs would be
  meaningless.

Assets known to exist but deliberately out of scope for this run: the MeSH bulk
N-Triples distribution at `nlmpubs.nlm.nih.gov` (the vocabulary schema was
assessed instead of the several-gigabyte instance dump), and the id.loc.gov
bulk downloads beyond the fifteen individual vocabularies seeded.

## Findings that were verified independently before publication

Two findings carried enough weight that a single tool's opinion was not
sufficient.

**The MADS/RDF ontology does not parse.** rdflib rejects
`https://id.loc.gov/ontologies/madsrdf/v1.rdf` at line 340 with "Invalid
property attribute URI: rdf:resource". Confirmed three ways:

1. The construct is `<rdf:Description rdf:resource="..."/>` appearing as a child
   inside `<owl:unionOf rdf:parseType="Collection">`, 23 occurrences in the file.
2. The RDF 1.1 XML Syntax grammar permits only `rdf:ID`, `rdf:nodeID` or
   `rdf:about` on a node element; `rdf:resource` is a `resourceAttr` valid on an
   empty property element. `parseTypeCollectionPropertyElt` contains a
   `nodeElementList`, so its children are node elements. The construct is
   therefore invalid, and the correct attribute would be `rdf:about`.
3. A second, independent parser agrees something is wrong: OWLAPI, via ROBOT,
   does not hard fail but emits `Entity not properly recognized` and silently
   substitutes `http://org.semanticweb.owlapi/error#Error1` through `Error8`.

The same construct appears zero times in the BIBFRAME and PREMIS 3 files, so
this is specific to MADS/RDF rather than an id.loc.gov pattern. It matters
beyond one file: the Thesaurus for Graphic Materials types its 7,782 concepts
with `madsrdf:Topic`, so a substantial LOC vocabulary is typed against an
ontology whose published serialisation no conforming parser will read.

**Every ISO 639-2 concept violates SKOS S14.** All 507 concepts in
`id.loc.gov/vocabulary/iso639-2` carry three `skos:prefLabel` values, in
English, French and German, and **none of the three carries a language tag**.
S14 states that a resource has no more than one value of `skos:prefLabel` per
language tag; three untagged labels are three labels sharing the same (absent)
tag. Verified directly against the payload rather than inferred from the check.
The vocabulary of language codes is itself not language tagged.

## Mistakes in this build, caught before publication

Recorded because a register that audits others should show its own working.

**Transport findings attributed to the wrong party.** DCAT-US 3.0 SHACL shapes
and the NARA restrictions vocabulary are retrieved from
`raw.githubusercontent.com`, which serves `.ttl` as `text/plain`. The first run
recorded a media type violation against GSA and the National Archives for a
header GitHub sets. Both are now flagged `retrieval_via_mirror` in the seed and
transport-level checks return `earl:inapplicable` for them, with the reason
stated. Attributing a mirror's behaviour to a publisher is precisely the
category error this register exists to avoid.

**A dependency check that measured its own regex.** The first implementation of
SAR-I02 derived namespace prefixes by truncating term URIs at the last `/` or
`#`, then probed the prefixes. That reported `http://id.loc.gov/vocabulary/` as
a dead dependency of twelve assets. It does return 404, but no publisher ever
minted it: `http://id.loc.gov/vocabulary/relators/` and its siblings resolve
normally. The check now probes the referenced terms themselves, over a
deterministic sample, and the earlier headline was discarded rather than
published.

**A parse failure that was really an encoding assumption.** The NOAA
paleoenvironmental thesaurus initially recorded as unparseable. It is served as
`application/rdf+xml; charset=ISO-8859-1`, carries no XML declaration, and
contains byte `0xf1`, the "n" in "El Nino", at offset 9,497. A correct HTTP
client honours the charset parameter, so the loader now does, and the payload
parses to 27,326 triples. The underlying issue is real but different from a
parse failure, and it is now reported as its own check (SAR-P03): detached from
its HTTP headers, the file cannot be decoded. XML 1.0 expressly permits an
external protocol to supply the encoding, so this is graded conventional, not a
violation.

## Tooling

- Retrieval and 23 of the 26 checks: Python 3.13 with rdflib 7.6.0. No licensed
  dependency anywhere in the pipeline.
- SAR-L01 to SAR-L03 (OWL 2 DL profile, consistency, unsatisfiable classes):
  ROBOT 1.9.10 on OpenJDK 26, using the ELK reasoner, with a 900 second budget
  per asset. Assets exceeding the budget report `earl:cantTell`.
- The ontology was cross-validated with two independent parsers, rdflib and the
  `open-ontologies` Rust engine, which agree on the triple count.
- 23 unit tests in `tests/` build synthetic graphs that violate exactly one SKOS
  integrity condition each and assert the battery catches that one and no other.

## Known limits

Stated in full in [`docs/METHOD.md`](docs/METHOD.md). The load-bearing ones:

- Coverage is a seeded sample, not a census, and it is biased toward agencies
  that publish RDF at all. The agencies whose semantic assets are least
  accessible are by construction underrepresented.
- Retrievability was observed once, from one network location. A transient
  outage and a permanent removal look identical in a single run, which is the
  main reason this register is built to be re-run.
- The Library of Congress accounts for 15 of 28 assets. Estate-wide percentages
  should be read as percentages of this sample, in which one publisher is
  heavily weighted, not of the federal estate.
- Assets typed with MADS/RDF rather than SKOS, such as the Thesaurus for Graphic
  Materials, fall outside the SKOS battery entirely and are assessed only on
  retrieval, parsing, documentation and governance.
