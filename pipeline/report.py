#!/usr/bin/env python3
"""Stage 3: turn assessment results into the published scorecard.

Every number in docs/SCORECARD.md is computed here from results/assessment.json.
Nothing in the scorecard is written by hand.
"""
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone

from rdflib import Graph, Namespace, RDF

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = Namespace("https://gov.tesseract.academy/def/sar#")
EARL = Namespace("http://www.w3.org/ns/earl#")

ORDER = ["R01", "R02", "R03", "R04", "P01", "P02", "P03",
         "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09",
         "D01", "D02", "D03", "G01", "G02", "G03", "S01", "S02", "I01", "I02"]

MARK = {"passed": "pass", "failed": "FAIL", "cantTell": "?", "inapplicable": "n/a"}


def load_catalogue():
    g = Graph()
    g.parse(ROOT / "ontology" / "checks.ttl", format="turtle")
    g.parse(ROOT / "ontology" / "sar.ttl", format="turtle")
    meta = {}
    for c in g.subjects(RDF.type, EARL.TestCase):
        cid = str(c).split("#")[-1]
        norm = next(g.objects(c, SAR.normativity), None)
        sev = next(g.objects(c, SAR.severity), None)
        dim = next(g.objects(c, SAR.dimension), None)
        label = next(g.objects(c, Namespace("http://www.w3.org/2004/02/skos/core#").prefLabel), None)
        meta[cid] = {
            "normativity": str(norm).split("#")[-1] if norm else None,
            "severity": str(sev).split("#")[-1] if sev else None,
            "dimension": str(dim).split("#")[-1] if dim else None,
            "label": str(label) if label else cid,
        }
    return meta


def main():
    a = json.loads((ROOT / "results" / "assessment.json").read_text())
    seed = json.loads((ROOT / "data" / "seed_assets.json").read_text())
    cat = load_catalogue()
    today = datetime.now(timezone.utc).date().isoformat()

    lines = []
    w = lines.append

    w("# US Federal Semantic Asset Scorecard")
    w("")
    w(f"Generated {today} by `pipeline/report.py` from `results/assessment.json`. "
      "Every figure below is computed, not written by hand. Re-run the pipeline to regenerate it.")
    w("")

    # ---- headline -------------------------------------------------------
    oc = Counter()
    norm_fail = Counter()
    conv_fail = Counter()
    for aid, v in a.items():
        for cid, r in v["results"].items():
            oc[r["outcome"]] += 1
            if r["outcome"] == "failed":
                if cat.get(cid, {}).get("normativity") == "Normative":
                    norm_fail[cid] += 1
                else:
                    conv_fail[cid] += 1
    total = sum(oc.values())

    parsed = [v for v in a.values() if v["triples"] is not None]
    triples = sum(v["triples"] for v in parsed)

    w("## Headline")
    w("")
    w(f"- **{len(a)} assets** assessed across **{len({v['agency'] for v in a.values()})} publishers**, "
      f"totalling **{triples:,} triples**.")
    w(f"- **{len(parsed)} of {len(a)}** payloads parsed.")
    w(f"- **{total} check results**: {oc['passed']} passed, {oc['failed']} failed, "
      f"{oc['inapplicable']} inapplicable, {oc['cantTell']} could not be determined.")
    w(f"- Of the failures, **{sum(norm_fail.values())} are normative** "
      f"(a published specification was violated) and **{sum(conv_fail.values())} are conventional** "
      "(a community practice was not followed, which the publisher never agreed to).")
    w("")
    w("The split matters more than the totals. A conventional failure is not a defect; it is a "
      "difference. Only the normative column describes something that is wrong by the standard's "
      "own terms.")
    w("")

    # ---- normative failures --------------------------------------------
    w("## Normative failures, by check")
    w("")
    w("| Check | What it tests | Authority | Assets failing |")
    w("|---|---|---|---:|")
    for cid in ORDER:
        m = cat.get(cid)
        if not m or m["normativity"] != "Normative":
            continue
        n = norm_fail.get(cid, 0)
        w(f"| SAR-{cid} | {m['label']} | {m['dimension']} | {n} |")
    w("")

    # ---- conventional ---------------------------------------------------
    w("## Conventional findings, by check")
    w("")
    w("| Check | What it tests | Assets differing |")
    w("|---|---|---:|")
    for cid in ORDER:
        m = cat.get(cid)
        if not m or m["normativity"] != "Conventional":
            continue
        w(f"| SAR-{cid} | {m['label']} | {conv_fail.get(cid, 0)} |")
    w("")

    # ---- per asset ------------------------------------------------------
    w("## Per asset")
    w("")
    hdr = "| Asset | Publisher | Kinds | Triples | " + " | ".join("R" + c if False else c for c in ORDER) + " |"
    w(hdr)
    w("|---|---|---|---:|" + "---|" * len(ORDER))
    for aid, v in sorted(a.items(), key=lambda kv: (kv[1]["agency"], kv[0])):
        cells = []
        for cid in ORDER:
            r = v["results"].get(cid)
            cells.append(MARK.get(r["outcome"], "?") if r else "")
        tri = f"{v['triples']:,}" if v["triples"] is not None else "did not parse"
        kinds = ", ".join(k.replace("Ontology", "").replace("Scheme", "") for k in v["kinds"]) or "-"
        w(f"| `{aid}` | {v['agency']} | {kinds} | {tri} | " + " | ".join(cells) + " |")
    w("")
    w("Legend: `pass` passed, `FAIL` failed, `n/a` inapplicable to this asset kind, "
      "`?` could not be determined.")
    w("")

    # ---- agency rollup --------------------------------------------------
    w("## By publisher")
    w("")
    ag = defaultdict(lambda: Counter())
    agn = defaultdict(int)
    for v in a.values():
        agn[v["agency"]] += 1
        for cid, r in v["results"].items():
            ag[v["agency"]][r["outcome"]] += 1
            if r["outcome"] == "failed" and cat.get(cid, {}).get("normativity") == "Normative":
                ag[v["agency"]]["normative_failed"] += 1
    w("| Publisher | Assets | Passed | Failed | of which normative | Inapplicable | Undetermined |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for agency in sorted(ag, key=lambda x: -ag[x]["normative_failed"]):
        c = ag[agency]
        w(f"| {agency} | {agn[agency]} | {c['passed']} | {c['failed']} | {c['normative_failed']} "
          f"| {c['inapplicable']} | {c['cantTell']} |")
    w("")

    # ---- not RDF --------------------------------------------------------
    if seed.get("sought_but_not_rdf"):
        w("## Sought but not available as RDF")
        w("")
        w("A register that lists only what worked is not a register of the estate.")
        w("")
        for s in seed["sought_but_not_rdf"]:
            w(f"- **{s['name']}** ({s['agency']}, checked {s['checked']}): {s['finding']}")
        w("")

    out = ROOT / "docs" / "SCORECARD.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(lines)} lines)")
    print(f"normative failures: {sum(norm_fail.values())}, conventional: {sum(conv_fail.values())}")


if __name__ == "__main__":
    main()
