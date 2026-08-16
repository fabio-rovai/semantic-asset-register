#!/usr/bin/env python3
"""Stage 2: run the SAR check battery over probed snapshots and emit EARL assertions.

Design commitments enforced here:
  * A check that does not apply to an asset's kind yields earl:inapplicable, never earl:failed.
  * A check that cannot be evaluated (timeout, tooling failure) yields earl:cantTell, never a pass.
  * Every failure carries an affected count, a population count and a concrete example IRI.
"""
import csv
import gzip
import io
import json
import pathlib
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS, OWL, SKOS, XSD

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAR = Namespace("https://gov.tesseract.academy/def/sar#")
SARC = Namespace("https://gov.tesseract.academy/def/sar/check#")
EARL = Namespace("http://www.w3.org/ns/earl#")
PROV = Namespace("http://www.w3.org/ns/prov#")
DC11 = Namespace("http://purl.org/dc/elements/1.1/")
SH = Namespace("http://www.w3.org/ns/shacl#")
REG = Namespace("https://gov.tesseract.academy/id/sar/")

ROBOT = ROOT / "tools" / "robot.jar"
JAVA = "/opt/homebrew/opt/openjdk/bin/java"
ROBOT_TIMEOUT = 900

CORE_NS = {
    str(RDF), str(RDFS), str(OWL), str(SKOS), str(DCTERMS), str(DC11),
    str(XSD), "http://www.w3.org/2004/02/skos/core#",
    "http://www.w3.org/ns/prov#", "http://xmlns.com/foaf/0.1/",
}

PASSED, FAILED, CANTTELL, INAPPLICABLE = "passed", "failed", "cantTell", "inapplicable"

RDF_MEDIA = {
    "application/rdf+xml": "xml",
    "text/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/n-triples": "nt",
    "text/n3": "n3",
    "application/ld+json": "json-ld",
    "application/owl+xml": "xml",
}


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def _guess_format(name, media_type, head):
    mt = (media_type or "").split(";")[0].strip().lower()
    if mt in RDF_MEDIA:
        return RDF_MEDIA[mt]
    low = name.lower()
    if low.endswith((".ttl", ".turtle")):
        return "turtle"
    if low.endswith((".rdf", ".owl", ".xml", ".rdfs")):
        return "xml"
    if low.endswith(".nt"):
        return "nt"
    if low.endswith((".jsonld", ".json")):
        return "json-ld"
    sniff = head[:2000].lstrip()
    if sniff.startswith(b"<?xml") or sniff.startswith(b"<rdf:RDF"):
        return "xml"
    if sniff.startswith(b"@prefix") or sniff.startswith(b"@base") or b"@prefix" in head[:2000]:
        return "turtle"
    if sniff.startswith(b"{"):
        return "json-ld"
    return None


def extract_payload(rec):
    """Return (bytes, name, note) for the RDF payload, unwrapping zip/gzip."""
    p = rec.get("snapshot_path")
    if not p:
        return None, None, "no snapshot stored"
    raw = (ROOT / p).read_bytes()
    name = rec["id"]

    if raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw), name + ".gz-inner", "gzip decompressed"
        except Exception as e:  # noqa: BLE001
            return None, None, f"gzip failure: {e}"

    if raw[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
            members = [m for m in zf.namelist() if not m.endswith("/")]
            # pick the largest member that looks like RDF
            cands = sorted(members, key=lambda m: zf.getinfo(m).file_size, reverse=True)
            for m in cands:
                if m.lower().endswith((".ttl", ".rdf", ".owl", ".nt", ".xml", ".jsonld")):
                    return zf.read(m), m, f"zip member {m} of {len(members)}"
            if cands:
                return zf.read(cands[0]), cands[0], f"zip member {cands[0]} (extension not RDF-like)"
            return None, None, "empty zip"
        except Exception as e:  # noqa: BLE001
            return None, None, f"zip failure: {e}"

    return raw, name, None


def transport_charset(media_type):
    m = re.search(r"charset=([\w-]+)", media_type or "", re.I)
    return m.group(1).lower() if m else None


def self_describing(data, fmt):
    """Can this payload be decoded without help from the transport layer?

    Returns (bool, explanation). An XML entity qualifies if it is valid UTF-8 or
    carries its own encoding declaration; XML 1.0 section 4.3.3 permits an
    external protocol to supply the encoding, which is why failing this is graded
    conventional rather than normative.
    """
    if fmt not in ("xml", "turtle", "nt", "json-ld", "n3"):
        return True, None
    try:
        data.decode("utf-8")
        return True, None
    except UnicodeDecodeError as e:
        if fmt == "xml":
            head = data[:200]
            m = re.search(rb'<\?xml[^>]*encoding\s*=\s*["\']([\w-]+)["\']', head, re.I)
            if m:
                return True, f"declares encoding {m.group(1).decode('ascii', 'replace')}"
            ctx = data[max(0, e.start - 20):e.start + 20]
            return False, ("not valid UTF-8 and carries no XML encoding declaration; "
                           f"first bad byte 0x{data[e.start]:02x} at offset {e.start} "
                           f"in {ctx.decode('latin-1')!r}")
        return False, f"not valid UTF-8 at offset {e.start}"


def load_graph(rec):
    data, name, note = extract_payload(rec)
    if data is None:
        return None, None, note, None
    fmt = _guess_format(name or "", rec["download"].get("media_type"), data)
    if fmt is None:
        return None, None, f"could not determine serialisation ({note or ''})".strip(), None

    ok_self, self_note = self_describing(data, fmt)

    # A correct HTTP client honours the charset parameter, so the audit does too.
    # Any recoding is recorded, because it is the difference between an artefact
    # that survives being saved to disk and one that does not.
    payload = data
    cs = transport_charset(rec["download"].get("media_type"))
    if not ok_self and cs and cs not in ("utf-8", "utf8"):
        try:
            payload = data.decode(cs).encode("utf-8")
            note = (note + "; " if note else "") + f"recoded from transport charset {cs}"
        except Exception:  # noqa: BLE001
            pass

    g = Graph()
    try:
        g.parse(data=payload, format=fmt)
        return g, fmt, note, (ok_self, self_note)
    except Exception as e:  # noqa: BLE001
        alt = "xml" if fmt == "turtle" else "turtle"
        try:
            g2 = Graph()
            g2.parse(data=payload, format=alt)
            return g2, alt, f"declared/guessed {fmt} but parsed as {alt}", (ok_self, self_note)
        except Exception:
            return None, fmt, f"parse error as {fmt}: {str(e)[:200]}", (ok_self, self_note)


# --------------------------------------------------------------------------
# kind detection
# --------------------------------------------------------------------------

def detect_kinds(g):
    kinds = set()
    if (None, RDF.type, SKOS.Concept) in g or (None, RDF.type, SKOS.ConceptScheme) in g:
        kinds.add("SkosScheme")
    if (None, RDF.type, OWL.Class) in g or (None, RDF.type, OWL.ObjectProperty) in g \
            or (None, RDF.type, OWL.DatatypeProperty) in g or (None, RDF.type, OWL.Ontology) in g:
        kinds.add("OwlOntology")
    if (None, RDF.type, RDFS.Class) in g or (None, RDF.type, RDF.Property) in g:
        kinds.add("RdfsVocabulary")
    if (None, RDF.type, SH.NodeShape) in g or (None, RDF.type, SH.PropertyShape) in g:
        kinds.add("ShapeGraph")
    if not kinds:
        kinds.add("CodeList")
    return kinds


def minted_terms(g, namespace):
    """Terms declared by this asset in its own namespace."""
    if not namespace:
        return set()
    ns = str(namespace)
    decl_types = [OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
                  RDFS.Class, RDF.Property, SKOS.Concept]
    out = set()
    for t in decl_types:
        for s in g.subjects(RDF.type, t):
            if isinstance(s, URIRef) and str(s).startswith(ns):
                out.add(s)
    return out


def external_terms(g, own_ns):
    """External vocabulary terms this asset actually depends on.

    Only URIs used in predicate position, or as the object of rdf:type, count as
    dependencies: those are the terms a consumer must be able to look up in order
    to interpret the graph. Earlier versions of this check probed namespace
    prefixes derived by truncating term URIs, which produced false failures
    against strings no publisher ever minted (for example
    http://id.loc.gov/vocabulary/ 404s while every real sub-namespace under it
    resolves). Probing the referenced term itself is both more meaningful and
    fairer.
    """
    own = str(own_ns) if own_ns else "\x00"
    terms = set()
    for s, p, o in g:
        for term in (p,) + ((o,) if p == RDF.type else ()):
            if not isinstance(term, URIRef):
                continue
            u = str(term)
            if not u.startswith(("http://", "https://")):
                continue
            if u.startswith(own):
                continue
            if any(u.startswith(c) for c in CORE_NS):
                continue
            terms.add(u)
    return terms


def external_namespaces(g, own_ns):
    ns = set()
    own = str(own_ns) if own_ns else "\x00"
    for s, p, o in g:
        for term in (s, p, o):
            if isinstance(term, URIRef):
                u = str(term)
                m = re.match(r"^(.*[#/])[^#/]*$", u)
                if not m:
                    continue
                base = m.group(1)
                if base.startswith(own):
                    continue
                if base in CORE_NS or base.rstrip("#/") + "#" in CORE_NS:
                    continue
                ns.add(base)
    return ns


# --------------------------------------------------------------------------
# check implementations
# --------------------------------------------------------------------------

def res(outcome, affected=None, population=None, example=None, info=None):
    return {"outcome": outcome, "affected": affected, "population": population,
            "example": example, "info": info}


def is_federal_domain(url):
    m = re.match(r"https?://([^/]+)", url or "")
    if not m:
        return False
    host = m.group(1).lower().split(":")[0]
    return host.endswith(".gov") or host.endswith(".mil")


def check_retrievability(rec):
    out = {}
    d = rec["download"]
    st = d.get("http_status")
    out["R01"] = res(PASSED if st == 200 else FAILED, info=f"HTTP {st}")

    n = rec.get("namespace_rdf")
    if not n:
        out["R02"] = res(INAPPLICABLE, info="no namespace declared")
        out["R03"] = res(INAPPLICABLE, info="no namespace declared")
    else:
        nst = n.get("http_status")
        out["R02"] = res(PASSED if nst and 200 <= nst < 300 else FAILED, info=f"HTTP {nst}")
        mt = (n.get("media_type") or "").split(";")[0].strip().lower()
        if not nst or nst >= 300:
            out["R03"] = res(FAILED, info=f"namespace returned HTTP {nst}")
        elif mt in RDF_MEDIA:
            out["R03"] = res(PASSED, info=f"served {mt} under an RDF Accept header")
        else:
            out["R03"] = res(FAILED, info=f"served {mt or 'unknown'} under an RDF Accept header")

    # SAR-R04 applies only on federal domains, per the scope of OMB M-15-13
    url = d.get("requested_url") or ""
    if rec.get("federal_domain") is False or not is_federal_domain(url):
        out["R04"] = res(INAPPLICABLE, info="not published on a .gov or .mil domain")
    else:
        h = rec.get("http_variant")
        if not url.startswith("https://"):
            out["R04"] = res(FAILED, info="advertised URL is not HTTPS")
        elif not h:
            out["R04"] = res(CANTTELL, info="HTTP variant not tested")
        elif h.get("http_status") is None:
            out["R04"] = res(PASSED, info="plain HTTP refused, so no insecure service is offered")
        elif (h.get("final_url") or "").startswith("https://"):
            out["R04"] = res(PASSED, info="plain HTTP redirects to HTTPS")
        else:
            out["R04"] = res(FAILED, info=f"content served over plain HTTP at {h.get('final_url')}")
    return out


def check_parse(rec, g, fmt, note, selfdesc):
    out = {}
    if selfdesc is None:
        out["P03"] = res(CANTTELL, info="payload not retrieved")
    else:
        ok, why = selfdesc
        out["P03"] = res(PASSED if ok else FAILED, info=why)

    if g is None:
        out["P01"] = res(FAILED, info=note or "did not parse")
        out["P02"] = res(CANTTELL, info="serialisation undetermined because parsing failed")
        return out
    out["P01"] = res(PASSED, population=len(g), info=f"parsed {len(g)} triples as {fmt}")

    # A transport-level finding is only attributable to the publisher if the
    # publisher controls the transport. When an asset is retrieved from a code
    # hosting mirror, the Content-Type is the mirror's choice.
    if rec.get("retrieval_via_mirror"):
        out["P02"] = res(INAPPLICABLE, info=rec.get("mirror_note")
                         or "retrieved from a mirror that controls the Content-Type")
        return out

    declared = (rec["download"].get("media_type") or "").split(";")[0].strip().lower()
    if declared in RDF_MEDIA:
        expected = RDF_MEDIA[declared]
        ok = (expected == fmt)
        out["P02"] = res(PASSED if ok else FAILED,
                         info=f"declared {declared} ({expected}), parsed as {fmt}")
    elif declared in ("application/zip", "application/gzip", "application/x-gzip"):
        out["P02"] = res(INAPPLICABLE, info=f"delivered as archive ({declared})")
    else:
        out["P02"] = res(FAILED, info=f"declared {declared or 'nothing'}, which is not an RDF media type; parsed as {fmt}")
    return out


def _sample(items):
    for i in items:
        return str(i)
    return None


def check_skos(g, kinds):
    """SKOS integrity conditions S9, S13, S14, S27, S37, S46."""
    out = {}
    if "SkosScheme" not in kinds:
        for c in ("L04", "L05", "L06", "L07", "L08", "L09"):
            out[c] = res(INAPPLICABLE, info="asset declares no SKOS concepts or schemes")
        return out

    concepts = set(g.subjects(RDF.type, SKOS.Concept))
    schemes = set(g.subjects(RDF.type, SKOS.ConceptScheme))
    colls = set(g.subjects(RDF.type, SKOS.Collection)) | set(g.subjects(RDF.type, SKOS.OrderedCollection))

    # S9
    both = concepts & schemes
    out["L04"] = res(FAILED if both else PASSED, len(both), len(concepts | schemes), _sample(both),
                     "S9: skos:ConceptScheme is disjoint with skos:Concept")

    # S13 pairwise label disjointness
    viol13 = set()
    pref = defaultdict(set)
    for s, o in g.subject_objects(SKOS.prefLabel):
        pref[s].add(o)
    for prop in (SKOS.altLabel, SKOS.hiddenLabel):
        for s, o in g.subject_objects(prop):
            if o in pref.get(s, ()):
                viol13.add(s)
    for s in set(g.subjects(SKOS.altLabel, None)):
        alts = set(g.objects(s, SKOS.altLabel))
        hids = set(g.objects(s, SKOS.hiddenLabel))
        if alts & hids:
            viol13.add(s)
    out["L05"] = res(FAILED if viol13 else PASSED, len(viol13), len(concepts) or len(pref),
                     _sample(viol13), "S13: prefLabel, altLabel and hiddenLabel are pairwise disjoint")

    # S14 one prefLabel per language
    viol14 = set()
    for s, labels in pref.items():
        seen = defaultdict(int)
        for l in labels:
            if isinstance(l, Literal):
                seen[l.language] += 1
        if any(v > 1 for v in seen.values()):
            viol14.add(s)
    out["L06"] = res(FAILED if viol14 else PASSED, len(viol14), len(pref), _sample(viol14),
                     "S14: no more than one prefLabel per language tag")

    # S27 related disjoint with broaderTransitive
    broader = set()
    for p in (SKOS.broader, SKOS.broaderTransitive):
        broader |= set(g.subject_objects(p))
    # broaderTransitive closure via narrower inverse as asserted
    for s, o in g.subject_objects(SKOS.narrower):
        broader.add((o, s))
    related = set(g.subject_objects(SKOS.related))
    related |= {(o, s) for s, o in g.subject_objects(SKOS.related)}  # symmetric
    v27 = {pair for pair in related if pair in broader}
    out["L07"] = res(FAILED if v27 else PASSED, len(v27), len(related) // 2 or 0,
                     _sample([p[0] for p in v27]),
                     "S27: skos:related is disjoint with skos:broaderTransitive")

    # S37 Collection disjoint with Concept and ConceptScheme
    v37 = colls & (concepts | schemes)
    out["L08"] = res(FAILED if v37 else PASSED, len(v37), len(colls), _sample(v37),
                     "S37: skos:Collection is disjoint with skos:Concept and skos:ConceptScheme")

    # S46 exactMatch disjoint with broadMatch and relatedMatch
    exact = set(g.subject_objects(SKOS.exactMatch))
    exact |= {(o, s) for s, o in exact}
    other = set(g.subject_objects(SKOS.broadMatch)) | set(g.subject_objects(SKOS.relatedMatch)) \
        | {(o, s) for s, o in g.subject_objects(SKOS.narrowMatch)}
    v46 = {p for p in exact if p in other}
    out["L09"] = res(FAILED if v46 else PASSED, len(v46), len(exact) // 2 or 0,
                     _sample([p[0] for p in v46]),
                     "S46: skos:exactMatch is disjoint with skos:broadMatch and skos:relatedMatch")
    return out


def check_documentation(g, kinds, ns):
    out = {}
    terms = minted_terms(g, ns)
    if not terms:
        out["D01"] = res(CANTTELL, info="no terms found in the asset's declared namespace")
        out["D02"] = res(CANTTELL, info="no terms found in the asset's declared namespace")
    else:
        unlabelled = {t for t in terms
                      if not list(g.objects(t, RDFS.label)) and not list(g.objects(t, SKOS.prefLabel))}
        out["D01"] = res(FAILED if unlabelled else PASSED, len(unlabelled), len(terms),
                         _sample(unlabelled))
        defprops = [SKOS.definition, RDFS.comment, DCTERMS.description, SKOS.scopeNote,
                    URIRef("http://purl.obolibrary.org/obo/IAO_0000115")]
        undefined = {t for t in terms if not any(list(g.objects(t, p)) for p in defprops)}
        out["D02"] = res(FAILED if undefined else PASSED, len(undefined), len(terms),
                         _sample(undefined))

    # D03 asset-level title and description
    roots = set(g.subjects(RDF.type, OWL.Ontology)) | set(g.subjects(RDF.type, SKOS.ConceptScheme))
    if not roots:
        out["D03"] = res(FAILED, info="no owl:Ontology or skos:ConceptScheme resource declared")
    else:
        titled = {r for r in roots
                  if list(g.objects(r, DCTERMS.title)) or list(g.objects(r, DC11.title))
                  or list(g.objects(r, RDFS.label)) or list(g.objects(r, SKOS.prefLabel))}
        described = {r for r in roots
                     if list(g.objects(r, DCTERMS.description)) or list(g.objects(r, DC11.description))
                     or list(g.objects(r, RDFS.comment))}
        good = titled & described
        out["D03"] = res(PASSED if good else FAILED, len(roots) - len(good), len(roots),
                         _sample(roots - good),
                         f"{len(titled)}/{len(roots)} titled, {len(described)}/{len(roots)} described")
    return out


def check_governance(g):
    out = {}
    roots = set(g.subjects(RDF.type, OWL.Ontology)) | set(g.subjects(RDF.type, SKOS.ConceptScheme))
    lic_props = [DCTERMS.license, DC11.rights, DCTERMS.rights,
                 URIRef("http://creativecommons.org/ns#license"),
                 URIRef("http://schema.org/license")]
    has_lic = any((None, p, None) in g for p in lic_props)
    out["G01"] = res(PASSED if has_lic else FAILED,
                     info="licence or rights statement present" if has_lic
                     else "no dcterms:license, dcterms:rights, dc:rights or cc:license triple anywhere in the payload")

    ver_props = [OWL.versionIRI, OWL.versionInfo, DCTERMS.hasVersion,
                 DCTERMS.issued, DCTERMS.modified, DCTERMS.created,
                 URIRef("http://purl.org/pav/version")]
    has_ver = any((None, p, None) in g for p in ver_props)
    out["G02"] = res(PASSED if has_ver else FAILED,
                     info="version or dated metadata present" if has_ver
                     else "no owl:versionIRI, owl:versionInfo or dated metadata")

    pub_props = [DCTERMS.publisher, DCTERMS.creator, DC11.publisher, DC11.creator,
                 URIRef("http://xmlns.com/foaf/0.1/maker")]
    has_pub = any((None, p, None) in g for p in pub_props)
    out["G03"] = res(PASSED if has_pub else FAILED,
                     info="publisher or creator present" if has_pub
                     else "no publisher or creator named in the payload")
    if not roots and not has_lic:
        out["G01"]["info"] += "; note the asset declares no ontology or scheme resource to carry it"
    return out


def check_stability(g, ns):
    out = {}
    deprecated = set(g.subjects(OWL.deprecated, Literal(True)))
    deprecated |= set(g.subjects(RDF.type, OWL.DeprecatedClass))
    deprecated |= set(g.subjects(RDF.type, OWL.DeprecatedProperty))
    for s, o in g.subject_objects(URIRef("http://www.w3.org/2004/02/skos/core#historyNote")):
        pass
    if not deprecated:
        out["S01"] = res(INAPPLICABLE, info="no deprecated terms declared")
        out["S02"] = res(INAPPLICABLE, info="no deprecated terms declared")
        return out

    succ_props = [DCTERMS.isReplacedBy, URIRef("http://purl.obolibrary.org/obo/IAO_0100001"),
                  SKOS.changeNote, SKOS.historyNote, RDFS.comment,
                  URIRef("http://www.w3.org/2002/07/owl#deprecatedBy")]
    orphan = {t for t in deprecated if not any(list(g.objects(t, p)) for p in succ_props)}
    out["S01"] = res(FAILED if orphan else PASSED, len(orphan), len(deprecated), _sample(orphan))

    live_refs = set()
    for s, p, o in g:
        if o in deprecated and s not in deprecated and p not in (RDF.type,):
            live_refs.add(s)
    out["S02"] = res(FAILED if live_refs else PASSED, len(live_refs), len(deprecated),
                     _sample(live_refs))
    return out


SAMPLE_PER_ASSET = 25


def check_interop(g, ns, ns_cache):
    out = {}
    ext_all = external_namespaces(g, ns)
    malformed = sorted(n for n in ext_all if not n.startswith(("http://", "https://")))

    terms = sorted(external_terms(g, ns))
    out["I01"] = res(PASSED if terms else FAILED, len(terms), None,
                     terms[0] if terms else None,
                     f"{len(terms)} distinct external vocabulary terms referenced")
    if not terms:
        out["I02"] = res(INAPPLICABLE, info="no external vocabulary terms to resolve")
        out["_malformed_ns"] = malformed
        return out

    # Deterministic sample: probing every term against live infrastructure is
    # neither polite nor necessary. Sorted order makes the sample reproducible.
    if len(terms) > SAMPLE_PER_ASSET:
        step = len(terms) / SAMPLE_PER_ASSET
        sample = [terms[int(i * step)] for i in range(SAMPLE_PER_ASSET)]
        sampled_note = f" (deterministic sample of {len(sample)} from {len(terms)})"
    else:
        sample = terms
        sampled_note = ""

    dead = []
    for t in sample:
        if t not in ns_cache:
            ns_cache[t] = probe_namespace(t)
        if not ns_cache[t]:
            dead.append(t)

    info = f"{len(dead)} of {len(sample)} referenced external terms did not resolve{sampled_note}"
    if malformed:
        info += (f"; {len(malformed)} referenced namespace(s) are not absolute HTTP URIs, "
                 f"e.g. {malformed[0]}")
    out["I02"] = res(FAILED if dead else PASSED, len(dead), len(sample),
                     dead[0] if dead else None, info)
    out["_ext_detail"] = {t: ns_cache[t] for t in sample}
    out["_malformed_ns"] = malformed
    return out


def probe_namespace(url):
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, headers={
        "User-Agent": "SemanticAssetRegister/0.1 (+https://gov.tesseract.academy/def/sar)",
        "Accept": "text/turtle, application/rdf+xml, */*;q=0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return 200 <= r.status < 300
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------
# OWL checks via ROBOT
# --------------------------------------------------------------------------

def run_robot(args, timeout=ROBOT_TIMEOUT):
    try:
        p = subprocess.run([JAVA, "-Xmx6g", "-jar", str(ROBOT)] + args,
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout after {timeout}s"
    except Exception as e:  # noqa: BLE001
        return None, "", f"{type(e).__name__}: {e}"


def check_owl(rec, g, kinds, workdir):
    out = {}
    if "OwlOntology" not in kinds:
        for c in ("L01", "L02", "L03"):
            out[c] = res(INAPPLICABLE, info="asset is not an OWL ontology")
        return out

    tmp = workdir / f"{rec['id']}.ttl"
    try:
        g.serialize(destination=str(tmp), format="turtle")
    except Exception as e:  # noqa: BLE001
        for c in ("L01", "L02", "L03"):
            out[c] = res(CANTTELL, info=f"could not serialise for reasoning: {e}")
        return out

    rc, so, se = run_robot(["validate-profile", "--profile", "DL", "--input", str(tmp)])
    if rc is None:
        out["L01"] = res(CANTTELL, info=f"profile validation did not complete: {se[:200]}")
    else:
        blob = (so or "") + (se or "")
        if "Ontology is in profile" in blob or rc == 0:
            out["L01"] = res(PASSED, info="within OWL 2 DL")
        else:
            n = blob.count("violation") + blob.count("Violation")
            first = next((l.strip() for l in blob.splitlines()
                          if l.strip() and "iolation" in l), blob.strip()[:200])
            out["L01"] = res(FAILED, affected=n or None, info=f"outside OWL 2 DL: {first[:220]}")

    rc, so, se = run_robot(["reason", "--reasoner", "ELK", "--input", str(tmp),
                            "--output", str(workdir / f"{rec['id']}-reasoned.owl")])
    blob = (so or "") + (se or "")
    if rc is None:
        out["L02"] = res(CANTTELL, info=f"reasoning did not complete: {se[:200]}")
        out["L03"] = res(CANTTELL, info="reasoning did not complete")
    elif rc == 0:
        out["L02"] = res(PASSED, info="ELK found the ontology consistent")
        out["L03"] = res(PASSED, info="ELK reported no unsatisfiable classes")
    else:
        low = blob.lower()
        if "inconsistent" in low:
            out["L02"] = res(FAILED, info="reasoner reports the ontology is inconsistent")
            out["L03"] = res(CANTTELL, info="not evaluable while the ontology is inconsistent")
        elif "unsatisfiable" in low:
            m = re.search(r"(\d+)\s+unsatisfiable", low)
            out["L02"] = res(PASSED, info="consistent, but with unsatisfiable classes")
            out["L03"] = res(FAILED, affected=int(m.group(1)) if m else None,
                             info="reasoner reports unsatisfiable classes")
        else:
            note = next((l.strip() for l in blob.splitlines() if l.strip()), "")[:220]
            out["L02"] = res(CANTTELL, info=f"reasoner exited {rc}: {note}")
            out["L03"] = res(CANTTELL, info=f"reasoner exited {rc}")
    return out


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    probes = json.loads((ROOT / "results" / "probe_results.json").read_text())
    seed = json.loads((ROOT / "data" / "seed_assets.json").read_text())
    fed_flags = {a["id"]: a.get("federal_domain", True) for a in seed["assets"]}
    mirror = {a["id"]: (a.get("retrieval_via_mirror", False), a.get("mirror_note"))
              for a in seed["assets"]}

    workdir = ROOT / "data" / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    ns_cache = {}
    all_rows = []
    per_asset = {}

    for rec in probes:
        rec["federal_domain"] = fed_flags.get(rec["id"], True)
        rec["retrieval_via_mirror"], rec["mirror_note"] = mirror.get(rec["id"], (False, None))
        print(f"[assess] {rec['id']}", flush=True)
        g, fmt, note, selfdesc = load_graph(rec)
        kinds = detect_kinds(g) if g is not None else set()
        ns = rec.get("namespace")

        results = {}
        results.update(check_retrievability(rec))
        results.update(check_parse(rec, g, fmt, note, selfdesc))
        if g is not None:
            results.update(check_skos(g, kinds))
            results.update(check_documentation(g, kinds, ns))
            results.update(check_governance(g))
            results.update(check_stability(g, ns))
            results.update(check_interop(g, ns, ns_cache))
            results.update(check_owl(rec, g, kinds, workdir))
        else:
            for c in ("L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09",
                      "D01", "D02", "D03", "G01", "G02", "G03", "S01", "S02", "I01", "I02"):
                results[c] = res(CANTTELL, info="payload did not parse")

        ext_detail = results.pop("_ext_detail", None)
        malformed_ns = results.pop("_malformed_ns", None)
        per_asset[rec["id"]] = {
            "id": rec["id"], "agency": rec["agency"], "name": rec["name"],
            "namespace": ns, "kinds": sorted(kinds), "format": fmt,
            "triples": len(g) if g is not None else None,
            "note": note, "results": results, "external_namespaces": ext_detail,
            "malformed_namespace_refs": malformed_ns,
        }
        for cid, r in results.items():
            all_rows.append({
                "asset": rec["id"], "agency": rec["agency"], "check": "SAR-" + cid,
                "outcome": r["outcome"], "affected": r["affected"],
                "population": r["population"], "example": r["example"], "info": r["info"],
            })

    (ROOT / "results" / "assessment.json").write_text(json.dumps(per_asset, indent=2))
    with open(ROOT / "results" / "assessment.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["asset", "agency", "check", "outcome",
                                          "affected", "population", "example", "info"])
        w.writeheader()
        w.writerows(all_rows)

    emit_earl(per_asset, probes)

    tally = defaultdict(int)
    for r in all_rows:
        tally[r["outcome"]] += 1
    print("\n[assess] outcomes:", dict(tally))
    print(f"[assess] wrote results/assessment.json, results/assessment.csv, results/findings.ttl")


def emit_earl(per_asset, probes):
    pmap = {p["id"]: p for p in probes}
    g = Graph()
    g.bind("sar", SAR); g.bind("sarc", SARC); g.bind("earl", EARL)
    g.bind("prov", PROV); g.bind("dcterms", DCTERMS); g.bind("reg", REG)

    runner = REG["assertor/sar-0.1.0"]
    g.add((runner, RDF.type, EARL.Software))
    g.add((runner, RDF.type, EARL.Assertor))
    g.add((runner, DCTERMS.title, Literal("Semantic Asset Register check runner 0.1.0")))

    for aid, a in per_asset.items():
        asset = REG[f"asset/{aid}"]
        snap = REG[f"snapshot/{aid}/{datetime.now(timezone.utc).date().isoformat()}"]
        p = pmap[aid]
        d = p["download"]

        g.add((asset, RDF.type, SAR.SemanticAsset))
        g.add((asset, DCTERMS.title, Literal(a["name"])))
        g.add((asset, DCTERMS.publisher, Literal(a["agency"])))
        if a["namespace"]:
            g.add((asset, SAR.namespaceUri, Literal(a["namespace"], datatype=XSD.anyURI)))
        for k in a["kinds"]:
            g.add((asset, SAR.assetKind, SAR[k]))

        g.add((snap, RDF.type, SAR.Snapshot))
        g.add((snap, SAR.snapshotOf, asset))
        g.add((snap, SAR.retrievedFrom, Literal(d.get("requested_url") or "", datatype=XSD.anyURI)))
        if d.get("final_url"):
            g.add((snap, SAR.finalUrl, Literal(d["final_url"], datatype=XSD.anyURI)))
        g.add((snap, SAR.retrievedAt, Literal(p["retrieved_at"], datatype=XSD.dateTime)))
        if d.get("http_status") is not None:
            g.add((snap, SAR.httpStatus, Literal(d["http_status"], datatype=XSD.integer)))
        if d.get("media_type"):
            g.add((snap, SAR.mediaType, Literal(d["media_type"])))
        if d.get("byte_size") is not None:
            g.add((snap, SAR.byteSize, Literal(d["byte_size"], datatype=XSD.integer)))
        if d.get("sha256"):
            g.add((snap, SAR.sha256, Literal(d["sha256"])))
        if a["triples"] is not None:
            g.add((snap, SAR.tripleCount, Literal(a["triples"], datatype=XSD.integer)))

        for cid, r in a["results"].items():
            node = REG[f"assertion/{aid}/{cid}"]
            rnode = REG[f"result/{aid}/{cid}"]
            g.add((node, RDF.type, EARL.Assertion))
            g.add((node, EARL.assertedBy, runner))
            g.add((node, EARL.subject, snap))
            g.add((node, EARL.test, SARC[cid]))
            g.add((node, EARL.mode, EARL.automatic))
            g.add((node, EARL.result, rnode))
            g.add((rnode, RDF.type, EARL.TestResult))
            g.add((rnode, EARL.outcome, EARL[r["outcome"]]))
            if r.get("affected") is not None:
                g.add((rnode, SAR.affectedCount, Literal(r["affected"], datatype=XSD.integer)))
            if r.get("population") is not None:
                g.add((rnode, SAR.populationCount, Literal(r["population"], datatype=XSD.integer)))
            if r.get("example"):
                g.add((rnode, SAR.exampleTerm, Literal(r["example"], datatype=XSD.anyURI)))
            if r.get("info"):
                g.add((rnode, EARL.info, Literal(r["info"])))

    g.serialize(destination=str(ROOT / "results" / "findings.ttl"), format="turtle")
    print(f"[assess] findings graph: {len(g)} triples")


if __name__ == "__main__":
    sys.exit(main())
