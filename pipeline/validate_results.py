#!/usr/bin/env python3
"""QA gate: verify the published results are internally consistent before release.

Fails loudly rather than publishing a register that contradicts itself.
"""
import json
import pathlib
import sys

from rdflib import Graph, Namespace, RDF

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = Namespace("https://gov.tesseract.academy/def/sar#")
SARC = Namespace("https://gov.tesseract.academy/def/sar/check#")
EARL = Namespace("http://www.w3.org/ns/earl#")

VALID_OUTCOMES = {"passed", "failed", "cantTell", "inapplicable", "untested"}

errors = []
warnings = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    # 1. ontology and catalogue parse
    onto = Graph()
    onto.parse(ROOT / "ontology" / "sar.ttl", format="turtle")
    onto.parse(ROOT / "ontology" / "checks.ttl", format="turtle")
    print(f"ontology + catalogue: {len(onto)} triples")

    catalogue = {str(c).split("#")[-1] for c in onto.subjects(RDF.type, EARL.TestCase)}
    print(f"checks defined: {len(catalogue)}")

    # 2. every check carries its mandatory facets
    for c in onto.subjects(RDF.type, EARL.TestCase):
        cid = str(c).split("#")[-1]
        for p, name in [(SAR.derivesFrom, "derivesFrom"), (SAR.citation, "citation"),
                        (SAR.normativity, "normativity"), (SAR.severity, "severity"),
                        (SAR.dimension, "dimension"), (SAR.appliesToKind, "appliesToKind")]:
            check(list(onto.objects(c, p)), f"check {cid} is missing {name}")

    # 3. findings graph parses and uses only real EARL outcomes
    f = Graph()
    f.parse(ROOT / "results" / "findings.ttl", format="turtle")
    print(f"findings graph: {len(f)} triples")

    outcomes = set()
    for o in f.objects(None, EARL.outcome):
        outcomes.add(str(o).split("#")[-1])
    for o in outcomes:
        check(o in VALID_OUTCOMES, f"findings graph uses non-EARL outcome {o!r}")
    print(f"outcomes used: {sorted(outcomes)}")

    # 4. every assertion references a check that exists in the catalogue
    used = {str(t).split("#")[-1] for t in f.objects(None, EARL.test)}
    for u in used:
        check(u in catalogue, f"assertion references undefined check {u}")
    print(f"checks exercised: {len(used)} of {len(catalogue)}")
    if len(used) < len(catalogue):
        warnings.append(f"{len(catalogue) - len(used)} catalogue checks were never exercised: "
                        f"{sorted(catalogue - used)}")

    # 5. JSON and RDF agree on outcome counts
    a = json.loads((ROOT / "results" / "assessment.json").read_text())
    json_count = sum(len(v["results"]) for v in a.values())
    rdf_count = len(list(f.subjects(RDF.type, EARL.Assertion)))
    check(json_count == rdf_count,
          f"assessment.json has {json_count} results but findings.ttl has {rdf_count} assertions")
    print(f"result counts agree: {json_count}")

    # 6. no failure without evidence
    for aid, v in a.items():
        for cid, r in v["results"].items():
            if r["outcome"] == "failed":
                has_evidence = r.get("info") or r.get("example") or r.get("affected") is not None
                check(has_evidence, f"{aid}/{cid} failed with no info, example or count")
            if r["outcome"] not in VALID_OUTCOMES:
                errors.append(f"{aid}/{cid} has invalid outcome {r['outcome']!r}")

    # 7. every asset in the seed was assessed
    seed = json.loads((ROOT / "data" / "seed_assets.json").read_text())
    for s in seed["assets"]:
        check(s["id"] in a, f"seed asset {s['id']} has no assessment")

    print()
    for wmsg in warnings:
        print(f"WARNING: {wmsg}")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for e in errors[:40]:
            print(f"  - {e}")
        return 1
    print("All result integrity checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
