# Method

## The problem with ontology quality reports

Tools that score ontologies already exist. They are not widely used by the people
who publish ontologies, and the reason is not that publishers are indifferent to
quality. It is that most reports are not defensible when the publisher pushes
back.

Three failure modes recur.

**Convention presented as standard.** A report says an ontology "fails" because
its classes lack textual definitions. No W3C Recommendation requires textual
definitions. The publisher reads one such item, concludes the whole report is
someone's house style, and stops reading. One overreach discredits the twenty
findings that were real.

**Inapplicable presented as failed.** A SKOS concept scheme is scored against
OWL profile conformance and marked down for carrying no OWL axioms. It was never
meant to carry any. The score is now measuring the wrong thing, and the publisher
correctly ignores it.

**Unreproducible subjects.** A report says "the NASA GCMD keywords have N
problems". Which retrieval? On what date? From which of several endpoints? A
finding that cannot be re-derived cannot be acted on, and cannot be shown to have
been fixed.

This register is built to avoid all three.

## Prior art, and what is actually new here

Reproducible ontology quality tooling is not new, and this register would be
dishonest to imply otherwise.

**OOPS!, the Ontology Pitfall Scanner.** Poveda-Villalon, Gomez-Perez and
Suarez-Figueroa, *International Journal on Semantic Web and Information Systems*
10(2), 2014, pages 7 to 34. It defines 41 pitfalls across structural, functional
and usability-profiling dimensions, and the catalogue was derived from an
empirical analysis of more than 693 ontologies. It has been live at
https://oops.linkeddata.es/ for over a decade. Anyone presenting automated
ontology quality checking as an unsolved problem has not looked.

**FOOPS!** Garijo, Corcho and Poveda-Villalon, ISWC 2021. It scores OWL and SKOS
vocabularies against the FAIR principles, at https://foops.linkeddata.es/, with
code at https://github.com/oeg-upm/fair_ontologies. It scores artefacts on
demand and does not publish results for a corpus.

**qSKOS, and the direct ancestor of this register.** Mader, Haslhofer and Isaac,
"Finding Quality Issues in SKOS Vocabularies", TPDL 2012, arXiv:1206.1339, define
fifteen computable quality-checking functions, implement them as qSKOS
(https://github.com/cmader/qSKOS), and run them over fifteen real vocabularies.
Three of those fifteen are US federal: LCSH, MeSH and NAICS. They found issues in
all fifteen vocabularies, including 342,848 undocumented concepts and 173,149
orphan concepts in LCSH.

This is the closest prior work to what this register does, it covers part of the
same corpus, and the SKOS checks here are a narrower and more conservative
descendant of theirs. It is fourteen years old, it was a one-off methods paper
rather than a standing register, and it did not separate specification violations
from community conventions. But anyone presenting a SKOS quality audit of federal
vocabularies as unprecedented has not read it.

Related: de Coronado et al., "The NCI Thesaurus quality assurance life cycle",
*Journal of Biomedical Informatics* 42(3), 2009, is a maintainer-authored QA
account of a US federal vocabulary. Spero, "LCSH is to Thesaurus as Doorbell is to
Mammal", DC-2008, documents the unreliability of LCSH's 1986 automated conversion
to thesaural relations.

**Domain surveys.** Norouzi, Waitelonis and Sack, "The landscape of ontologies in
materials science and engineering: A survey and evaluation", arXiv:2408.06034,
2024, analyse and compare sixty ontologies against stated requirements. Published
multi-ontology evaluations therefore exist, at least in some domains.

**FAIR scoring of vocabularies is largely European infrastructure.** O'FAIRe
(Amdouni, Bouazzouni and Jonquet, ESWC 2022) scores semantic resources hosted in
AgroPortal and already returns a live score for the NAL Agricultural Thesaurus.
F-UJI and the FAIRsFAIR metrics assess datasets, not vocabularies as objects.
FAIRsharing is a registry and carries no quality or FAIR score at all, a point
worth stating plainly because it is frequently misdescribed.

**The OBO Foundry dashboard** runs a standing, re-computed quality report across
a whole community's ontologies, and is by some distance the closest thing in the
field to what this register does. It is live, it scores on the order of 190
ontologies, and it publishes its numbers. Two things follow.

First, its checks encode OBO's own conventions, which is correct for OBO and is
exactly why they cannot be lifted wholesale onto other publishers. Second, its
reach into the federal estate is two vocabularies, NCI Thesaurus and NCBI
Taxonomy, both of which are in scope because biomedicine adopted OBO, not because
anyone set out to assess what the US government publishes.

NCI Thesaurus is therefore the one asset in this register that a second,
independent standing assessment already covers, and the overlap is useful rather
than redundant: where two batteries with different check catalogues look at the
same artefact, disagreement between them is informative about the batteries.

So the contribution here is not "automated ontology checking", and it is not even
"SKOS quality checking of federal vocabularies", which Mader and colleagues did in
2012. It is three narrower things:

1. **A corpus that has largely gone unassessed, and has not been reassessed in
   fourteen years.** Mader et al. covered LCSH, MeSH and NAICS in 2012. No
   published quality assessment could be found for the USGS Thesaurus, the NAL
   Agricultural Thesaurus, the NASA GCMD keyword schemes, or the federal RDF
   estate as a whole.
2. **Normativity as a first-class, declared facet.** OOPS! grades pitfalls by
   importance, which is severity. This register additionally requires every check
   to name the authority that warrants it and to declare whether failing it
   breaks a specification or departs from a convention. Severity says how much a
   finding matters; normativity says whether the publisher is entitled to
   disagree.
3. **Standing results rather than on-demand scoring.** FOOPS! will score your
   ontology when you ask. This register publishes the corpus result, the snapshot
   hashes behind it, and a documented right of reply, so the findings can be
   contested and re-derived by the people they are about.

## Three commitments

### 1. Assess snapshots, not assets

Nothing here asserts a quality claim about an abstract vocabulary. Every claim is
about a `sar:Snapshot`: one retrieval, from one URL, at one recorded time, with
the HTTP status, the media type actually returned, the byte count and a SHA-256
of the bytes.

This makes findings falsifiable in the only way that matters. A publisher can
re-fetch the same URL and compare hashes. If the hash changed, the finding may be
stale and the register is wrong to keep asserting it. If the hash is identical
and the publisher cannot reproduce the finding, the check is wrong. Either way
the disagreement resolves against evidence rather than against recollection.

### 2. Separate normativity from severity

Every check declares two independent facets.

`sar:normativity` is a claim about authority. A check is **normative** only if
failing it violates a published specification, and the check must name the clause.
Ten of the twenty-five checks in this catalogue qualify. Six of those ten are the
SKOS integrity conditions S9, S13, S14, S27, S37 and S46, which the SKOS Reference
states normatively. The rest are RDF syntax conformance, media type correctness,
OWL 2 consistency, and HTTPS, which for US federal domains is binding under OMB
Memorandum M-15-13 rather than under any standards body.

`sar:severity` is a claim about consequence, and it is deliberately allowed to
diverge from normativity in both directions:

- **Conventional but high severity.** No specification obliges a publisher to
  state a licence inside the payload. A consumer who cannot determine the licence
  still cannot lawfully redistribute derived data. The finding matters; the
  publisher has still broken no rule.
- **Normative but low severity.** Serving Turtle under the wrong media type
  violates the media type registration. Almost every consumer sniffs the content
  anyway. The finding is technically correct and practically minor.

Collapsing these two axes into a single "error" is what produces reports that
publishers dismiss. Keeping them apart is what lets a reader triage.

### 3. Use EARL, and mean it

Findings are W3C EARL assertions. EARL was designed for conformance reporting and
already carries the distinction this domain needs: `earl:passed`, `earl:failed`,
`earl:cantTell`, `earl:inapplicable` and `earl:untested` are five different
outcomes, not two.

The register uses all of them in earnest:

- `earl:inapplicable` when the check does not fit the asset's kind. A SKOS scheme
  is not marked down for OWL profile checks. A shape graph is not marked down for
  lacking concepts.
- `earl:cantTell` when evaluation was attempted and did not complete: a reasoner
  timeout, an unparseable payload, an absent namespace. A check that could not be
  run is never silently recorded as a pass.

Because scores are computed from these counts and the counts are published, a
reader who rejects the weighting can recompute the aggregate from
`results/assessment.csv` without re-running anything.

## Check applicability

Asset kind is detected from the payload, not from the publisher's description.
An asset that declares `skos:Concept` instances is a `sar:SkosScheme` whatever it
calls itself; an asset that declares `owl:Class` is a `sar:OwlOntology`. Both
kinds can be, and often are, true of the same file, in which case both sets of
checks apply.

Kind detection drives applicability directly: a check runs only if its
`sar:appliesToKind` intersects the detected kinds, and yields `earl:inapplicable`
otherwise.

## On borrowing from OBO

ROBOT ships a report command with a substantial set of quality queries. Those
queries are excellent and this register uses ROBOT for the three OWL checks
(profile, consistency, unsatisfiability). It deliberately does not run
`robot report` wholesale.

The reason is that a meaningful part of that catalogue encodes OBO Foundry
conventions: cross-reference syntax, synonym type declarations, subset
declarations, definition capitalisation. Those are reasonable requirements inside
a community that agreed to them. The Library of Congress and NASA did not agree
to them, and reporting a NASA vocabulary as defective for lacking OBO synonym
type declarations would be precisely the category error described above.

Checks were therefore selected on a single test: can this be traced to an
authority that binds this publisher, or is it a practice that one community
adopted? The first group is normative, the second is either conventional or
excluded.

## Known limits

- The battery is defined over RDF graphs. Federal assets published only as XSD,
  JSON Schema or CSV are recorded in `sought_but_not_rdf` rather than scored,
  because scoring them against RDF criteria would be meaningless.
- Reasoning is bounded. Very large ontologies can exhaust the reasoner's time or
  memory budget, in which case the logical checks report `cantTell`. That is a
  limit of this run, not a judgement about the asset.
- Retrievability is observed from one network location at one time. A transient
  outage and a permanent removal look identical in a single run. This is the main
  reason the register is designed to be re-run rather than published once.
- Coverage is a seeded sample of the federal estate, not a census. It is biased
  toward agencies that publish RDF at all, which by construction excludes the
  agencies whose semantic assets are least accessible.
