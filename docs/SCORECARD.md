# US Federal Semantic Asset Scorecard

Generated 2026-08-16 by `pipeline/report.py` from `results/assessment.json`. Every figure below is computed, not written by hand. Re-run the pipeline to regenerate it.

## Headline

- **28 assets** assessed across **10 publishers**, totalling **13,040,382 triples**.
- **27 of 28** payloads parsed.
- **728 check results**: 393 passed, 130 failed, 155 inapplicable, 50 could not be determined.
- Of the failures, **10 are normative** (a published specification was violated) and **120 are conventional** (a community practice was not followed, which the publisher never agreed to).

The split matters more than the totals. A conventional failure is not a defect; it is a difference. Only the normative column describes something that is wrong by the standard's own terms.

## Normative failures, by check

| Check | What it tests | Authority | Assets failing |
|---|---|---|---:|
| SAR-R04 | Served over HTTPS with a valid certificate | Retrievability | 0 |
| SAR-P01 | Parses as RDF | Parseability | 1 |
| SAR-P02 | Media type matches serialisation | Parseability | 4 |
| SAR-L02 | Logically consistent | LogicalSoundness | 0 |
| SAR-L04 | Concept and ConceptScheme disjoint | LogicalSoundness | 0 |
| SAR-L05 | Label properties pairwise disjoint | LogicalSoundness | 0 |
| SAR-L06 | One preferred label per language | LogicalSoundness | 2 |
| SAR-L07 | related disjoint with broaderTransitive | LogicalSoundness | 3 |
| SAR-L08 | Collection disjoint with Concept and ConceptScheme | LogicalSoundness | 0 |
| SAR-L09 | exactMatch disjoint with broadMatch and relatedMatch | LogicalSoundness | 0 |

## Conventional findings, by check

| Check | What it tests | Assets differing |
|---|---|---:|
| SAR-R01 | Download URL resolves | 0 |
| SAR-R02 | Namespace URI dereferences | 3 |
| SAR-R03 | Serves RDF under content negotiation | 12 |
| SAR-P03 | Payload is self-describing | 1 |
| SAR-L01 | Conforms to OWL 2 DL | 10 |
| SAR-L03 | No unsatisfiable classes | 0 |
| SAR-D01 | Minted terms carry labels | 5 |
| SAR-D02 | Minted terms carry definitions | 13 |
| SAR-D03 | Asset declares title and description | 7 |
| SAR-G01 | Declares a licence | 21 |
| SAR-G02 | Declares a version | 14 |
| SAR-G03 | Declares a publisher or creator | 20 |
| SAR-S01 | Deprecated terms name a successor | 1 |
| SAR-S02 | No live references to deprecated terms | 1 |
| SAR-I01 | Reuses external vocabularies | 6 |
| SAR-I02 | External dependencies still resolve | 6 |

## Per asset

| Asset | Publisher | Kinds | Triples | R01 | R02 | R03 | R04 | P01 | P02 | P03 | L01 | L02 | L03 | L04 | L05 | L06 | L07 | L08 | L09 | D01 | D02 | D03 | G01 | G02 | G03 | S01 | S02 | I01 | I02 |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `dcat-us-shacl` | GSA / CDO Council | Owl, ShapeGraph | 4,042 | pass | FAIL | FAIL | n/a | pass | n/a | pass | FAIL | ? | ? | n/a | n/a | n/a | n/a | n/a | n/a | ? | ? | pass | pass | pass | pass | n/a | n/a | pass | FAIL |
| `loc-bibframe` | Library of Congress | Owl | 2,735 | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | n/a | n/a | pass | pass |
| `loc-carriers` | Library of Congress | Skos | 247 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | FAIL |
| `loc-contentTypes` | Library of Congress | Owl, Skos | 171 | pass | pass | pass | pass | pass | pass | pass | FAIL | ? | ? | pass | pass | pass | pass | pass | pass | FAIL | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | FAIL |
| `loc-countries` | Library of Congress | Skos | 3,027 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-ethnographicTerms` | Library of Congress | Skos | 228 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-geographicareas` | Library of Congress | Skos | 291 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-graphicMaterials` | Library of Congress | CodeList | 23,716 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ? | ? | FAIL | FAIL | FAIL | FAIL | n/a | n/a | pass | FAIL |
| `loc-iso639-2` | Library of Congress | Skos | 8,580 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | FAIL | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-iso639-5` | Library of Congress | Skos | 333 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-languages` | Library of Congress | Skos | 6,308 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-madsrdf` | Library of Congress | - | did not parse | pass | pass | pass | pass | FAIL | ? | pass | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| `loc-mediaTypes` | Library of Congress | Owl, Skos | 83 | pass | pass | pass | pass | pass | pass | pass | FAIL | ? | ? | pass | pass | pass | pass | pass | pass | FAIL | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | FAIL |
| `loc-premis3` | Library of Congress | Owl | 471 | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | pass | FAIL | pass | FAIL | pass | FAIL | n/a | n/a | FAIL | n/a |
| `loc-preservation` | Library of Congress | Skos | 152 | pass | pass | pass | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | pass |
| `loc-relators` | Library of Congress | Owl, Skos | 1,846 | pass | pass | pass | pass | pass | pass | pass | FAIL | ? | ? | pass | pass | pass | pass | pass | pass | FAIL | FAIL | pass | FAIL | FAIL | FAIL | n/a | n/a | pass | FAIL |
| `nasa-gcmd-instruments` | NASA | Skos | 26,701 | pass | pass | FAIL | pass | pass | FAIL | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | FAIL | FAIL | pass | FAIL | n/a | n/a | pass | pass |
| `nasa-gcmd-platforms` | NASA | Skos | 24,247 | pass | pass | FAIL | pass | pass | FAIL | pass | n/a | n/a | n/a | pass | pass | pass | FAIL | pass | pass | ? | ? | FAIL | FAIL | pass | FAIL | n/a | n/a | pass | pass |
| `nasa-gcmd-providers` | NASA | Skos | 26,155 | pass | pass | FAIL | pass | pass | FAIL | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | FAIL | FAIL | pass | FAIL | n/a | n/a | pass | pass |
| `nasa-gcmd-science` | NASA | Skos | 24,268 | pass | pass | FAIL | pass | pass | FAIL | pass | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | FAIL | FAIL | pass | FAIL | n/a | n/a | pass | pass |
| `sweet` | NASA JPL origin, ESIP maintained | Owl | 244 | pass | pass | FAIL | n/a | pass | pass | pass | FAIL | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | ? | ? | pass | pass | pass | FAIL | n/a | n/a | pass | pass |
| `noaa-paleo` | NOAA NCEI | Skos | 27,326 | pass | FAIL | FAIL | pass | pass | pass | FAIL | n/a | n/a | n/a | pass | pass | pass | pass | pass | pass | ? | ? | pass | FAIL | pass | pass | n/a | n/a | FAIL | n/a |
| `nara-restrictions` | National Archives (via DCAT-US) | Owl, Skos | 331 | pass | FAIL | FAIL | n/a | pass | n/a | pass | FAIL | pass | pass | pass | pass | pass | pass | pass | pass | ? | ? | pass | FAIL | pass | pass | n/a | n/a | FAIL | n/a |
| `nci-thesaurus` | National Cancer Institute | Owl | 10,855,010 | pass | pass | FAIL | pass | pass | n/a | pass | pass | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | FAIL | FAIL | FAIL | FAIL | pass | FAIL | FAIL | FAIL | pass | pass |
| `nlm-mesh-vocab` | National Library of Medicine | Owl | 342 | pass | pass | pass | pass | pass | pass | pass | FAIL | pass | pass | n/a | n/a | n/a | n/a | n/a | n/a | FAIL | FAIL | FAIL | FAIL | pass | FAIL | n/a | n/a | FAIL | n/a |
| `usda-nalt` | USDA National Agricultural Library | Owl, Skos | 1,153,267 | pass | pass | FAIL | pass | pass | n/a | pass | FAIL | pass | pass | pass | pass | FAIL | pass | pass | pass | pass | FAIL | pass | pass | pass | pass | n/a | n/a | pass | pass |
| `usgs-geographic` | USGS | Skos | 840,572 | pass | pass | FAIL | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | FAIL | pass | pass | pass | pass | pass | pass | FAIL | pass | n/a | n/a | FAIL | n/a |
| `usgs-thesaurus` | USGS | Skos | 9,689 | pass | pass | FAIL | pass | pass | pass | pass | n/a | n/a | n/a | pass | pass | pass | FAIL | pass | pass | pass | pass | pass | pass | FAIL | pass | n/a | n/a | FAIL | n/a |

Legend: `pass` passed, `FAIL` failed, `n/a` inapplicable to this asset kind, `?` could not be determined.

## By publisher

| Publisher | Assets | Passed | Failed | of which normative | Inapplicable | Undetermined |
|---|---:|---:|---:|---:|---:|---:|
| NASA | 4 | 55 | 21 | 5 | 20 | 8 |
| Library of Congress | 15 | 219 | 65 | 2 | 74 | 32 |
| USGS | 2 | 32 | 8 | 2 | 12 | 0 |
| USDA National Agricultural Library | 1 | 19 | 4 | 1 | 3 | 0 |
| National Library of Medicine | 1 | 10 | 7 | 0 | 9 | 0 |
| NOAA NCEI | 1 | 13 | 5 | 0 | 6 | 2 |
| GSA / CDO Council | 1 | 8 | 4 | 0 | 10 | 4 |
| National Archives (via DCAT-US) | 1 | 14 | 5 | 0 | 5 | 2 |
| NASA JPL origin, ESIP maintained | 1 | 12 | 3 | 0 | 9 | 2 |
| National Cancer Institute | 1 | 11 | 8 | 0 | 7 | 0 |

## Sought but not available as RDF

A register that lists only what worked is not a register of the estate.

- **NIEM 6.0 reference model** (NIEMOpen (OASIS Open Project), checked 2026-08-16): The normative model is XSD. The only RDF-adjacent artefact in github.com/niemopen/niem-model is a single JSON-LD context file of 5,418 bytes at json-ld/context.json. No OWL or RDF serialisation of the model itself was found.
- **Substance Registry Services** (EPA, checked 2026-08-16): Requesting RDF from https://sor.epa.gov/sor_internet/registry/substreg/ returns HTML. No RDF representation was located.
- **OSCAL** (NIST, checked 2026-08-16): Published as XML and JSON schemas. Structured and machine readable, but not RDF, and therefore out of scope for a battery whose checks are defined over RDF graphs.

