#!/usr/bin/env python3
"""Compute every headline number twice and refuse to agree with myself.

Path A: set-based Python over results/assessment.json.
Path B: SPARQL over results/findings.ttl joined to ontology/checks.ttl.

The two paths share no code. If they disagree, one of them is wrong and the
register must not ship. Exits non-zero on any disagreement.
"""
import json
import pathlib
import sys
from collections import Counter

from rdflib import Graph

ROOT = pathlib.Path(__file__).resolve().parent.parent

PREFIXES = """
PREFIX sar:  <https://gov.tesseract.academy/def/sar#>
PREFIX sarc: <https://gov.tesseract.academy/def/sar/check#>
PREFIX earl: <http://www.w3.org/ns/earl#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
"""

failures = []


def compare(label, a, b):
    ok = (a == b)
    mark = "ok " if ok else "MISMATCH"
    print(f"  [{mark}] {label:52s} python={a!s:>12} sparql={b!s:>12}")
    if not ok:
        failures.append(f"{label}: python={a} sparql={b}")


def main():
    data = json.loads((ROOT / "results" / "assessment.json").read_text())

    g = Graph()
    g.parse(ROOT / "results" / "findings.ttl", format="turtle")
    g.parse(ROOT / "ontology" / "checks.ttl", format="turtle")
    g.parse(ROOT / "ontology" / "sar.ttl", format="turtle")

    print("Cross-checking headline figures by two independent paths.\n")

    # ---- 1. total assertions -------------------------------------------
    py_total = sum(len(v["results"]) for v in data.values())
    sp_total = int(list(g.query(PREFIXES + """
        SELECT (COUNT(?a) AS ?n) WHERE { ?a rdf:type earl:Assertion }"""))[0][0])
    compare("total assertions", py_total, sp_total)

    # ---- 2. outcome distribution ---------------------------------------
    py_out = Counter()
    for v in data.values():
        for r in v["results"].values():
            py_out[r["outcome"]] += 1

    sp_out = {}
    for row in g.query(PREFIXES + """
        SELECT ?o (COUNT(?a) AS ?n) WHERE {
          ?a rdf:type earl:Assertion ; earl:result ?res .
          ?res earl:outcome ?o .
        } GROUP BY ?o"""):
        sp_out[str(row[0]).split("#")[-1]] = int(row[1])

    for outcome in ("passed", "failed", "inapplicable", "cantTell"):
        compare(f"outcome {outcome}", py_out.get(outcome, 0), sp_out.get(outcome, 0))

    # ---- 3. normative vs conventional failures -------------------------
    cat_norm = {}
    for row in g.query(PREFIXES + """
        SELECT ?c ?n WHERE { ?c rdf:type earl:TestCase ; sar:normativity ?n }"""):
        cat_norm[str(row[0]).split("#")[-1]] = str(row[1]).split("#")[-1]

    py_norm_fail = sum(1 for v in data.values() for cid, r in v["results"].items()
                       if r["outcome"] == "failed" and cat_norm.get(cid) == "Normative")
    py_conv_fail = sum(1 for v in data.values() for cid, r in v["results"].items()
                       if r["outcome"] == "failed" and cat_norm.get(cid) == "Conventional")

    sp_norm_fail = int(list(g.query(PREFIXES + """
        SELECT (COUNT(?a) AS ?n) WHERE {
          ?a rdf:type earl:Assertion ; earl:test ?c ; earl:result ?res .
          ?res earl:outcome earl:failed .
          ?c sar:normativity sar:Normative .
        }"""))[0][0])
    sp_conv_fail = int(list(g.query(PREFIXES + """
        SELECT (COUNT(?a) AS ?n) WHERE {
          ?a rdf:type earl:Assertion ; earl:test ?c ; earl:result ?res .
          ?res earl:outcome earl:failed .
          ?c sar:normativity sar:Conventional .
        }"""))[0][0])

    compare("normative failures", py_norm_fail, sp_norm_fail)
    compare("conventional failures", py_conv_fail, sp_conv_fail)
    compare("normative + conventional == all failures",
            py_norm_fail + py_conv_fail, py_out.get("failed", 0))

    # ---- 4. assets and triples -----------------------------------------
    py_assets = len(data)
    sp_assets = int(list(g.query(PREFIXES + """
        SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s rdf:type sar:Snapshot }"""))[0][0])
    compare("assets with a snapshot", py_assets, sp_assets)

    py_triples = sum(v["triples"] for v in data.values() if v["triples"] is not None)
    sp_triples = int(list(g.query(PREFIXES + """
        SELECT (SUM(?t) AS ?n) WHERE { ?s rdf:type sar:Snapshot ; sar:tripleCount ?t }"""))[0][0])
    compare("total triples assessed", py_triples, sp_triples)

    py_parsed = sum(1 for v in data.values() if v["triples"] is not None)
    sp_parsed = int(list(g.query(PREFIXES + """
        SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s sar:tripleCount ?t }"""))[0][0])
    compare("payloads that parsed", py_parsed, sp_parsed)

    # ---- 5. per-check failure counts ------------------------------------
    py_percheck = Counter()
    for v in data.values():
        for cid, r in v["results"].items():
            if r["outcome"] == "failed":
                py_percheck[cid] += 1

    sp_percheck = Counter()
    for row in g.query(PREFIXES + """
        SELECT ?c (COUNT(?a) AS ?n) WHERE {
          ?a rdf:type earl:Assertion ; earl:test ?c ; earl:result ?res .
          ?res earl:outcome earl:failed .
        } GROUP BY ?c"""):
        sp_percheck[str(row[0]).split("#")[-1]] = int(row[1])

    print()
    for cid in sorted(set(py_percheck) | set(sp_percheck)):
        compare(f"failures on SAR-{cid}", py_percheck.get(cid, 0), sp_percheck.get(cid, 0))

    # ---- verdict --------------------------------------------------------
    print()
    if failures:
        print(f"CROSS-CHECK FAILED: {len(failures)} disagreement(s) between the two paths.")
        for f in failures:
            print(f"  - {f}")
        print("\nDo not publish. One of the two computations is wrong.")
        return 1
    print("Both computation paths agree on every headline figure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
