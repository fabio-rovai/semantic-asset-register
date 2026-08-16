"""Unit tests for the SAR check battery.

Each SKOS test builds a minimal graph that is known to violate exactly one
integrity condition, and asserts the battery catches that one and no other.
Run with: python3 -m pytest tests/ -q
"""
import pathlib
import sys

import pytest
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL, RDFS, SKOS, DCTERMS

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "pipeline"))

from assess import (  # noqa: E402
    check_documentation, check_governance, check_skos, check_stability,
    detect_kinds, self_describing, transport_charset,
)

EX = Namespace("http://example.org/v1#")


def base_scheme():
    g = Graph()
    g.add((EX.Scheme, RDF.type, SKOS.ConceptScheme))
    for n in ("A", "B"):
        c = EX[n]
        g.add((c, RDF.type, SKOS.Concept))
        g.add((c, SKOS.prefLabel, Literal(n, lang="en")))
        g.add((c, SKOS.inScheme, EX.Scheme))
    return g


def outcome(res, cid):
    return res[cid]["outcome"]


# ---------------------------------------------------------------- SKOS

def test_clean_scheme_passes_all_skos_conditions():
    g = base_scheme()
    r = check_skos(g, {"SkosScheme"})
    for cid in ("L04", "L05", "L06", "L07", "L08", "L09"):
        assert outcome(r, cid) == "passed", f"{cid} should pass on a clean scheme"


def test_skos_checks_inapplicable_when_no_skos():
    g = Graph()
    g.add((EX.C, RDF.type, OWL.Class))
    r = check_skos(g, detect_kinds(g))
    for cid in ("L04", "L05", "L06", "L07", "L08", "L09"):
        assert outcome(r, cid) == "inapplicable"


def test_s9_concept_and_scheme_disjoint():
    g = base_scheme()
    g.add((EX.A, RDF.type, SKOS.ConceptScheme))  # A is now both
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L04") == "failed"
    assert r["L04"]["affected"] == 1
    assert outcome(r, "L06") == "passed"  # nothing else disturbed


def test_s13_label_properties_disjoint():
    g = base_scheme()
    g.add((EX.A, SKOS.altLabel, Literal("A", lang="en")))  # same literal as prefLabel
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L05") == "failed"
    assert r["L05"]["affected"] == 1


def test_s14_one_preflabel_per_language():
    g = base_scheme()
    g.add((EX.A, SKOS.prefLabel, Literal("Alpha", lang="en")))  # second en label
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L06") == "failed"
    assert r["L06"]["affected"] == 1


def test_s14_allows_one_preflabel_per_distinct_language():
    g = base_scheme()
    g.add((EX.A, SKOS.prefLabel, Literal("Alpha", lang="fr")))
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L06") == "passed"


def test_s27_related_disjoint_with_broader():
    g = base_scheme()
    g.add((EX.A, SKOS.broader, EX.B))
    g.add((EX.A, SKOS.related, EX.B))
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L07") == "failed"


def test_s27_narrower_counts_as_inverse_broader():
    g = base_scheme()
    g.add((EX.B, SKOS.narrower, EX.A))  # implies A broader B
    g.add((EX.A, SKOS.related, EX.B))
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L07") == "failed"


def test_s37_collection_disjoint():
    g = base_scheme()
    g.add((EX.A, RDF.type, SKOS.Collection))
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L08") == "failed"


def test_s46_exactmatch_disjoint_with_broadmatch():
    g = base_scheme()
    g.add((EX.A, SKOS.exactMatch, EX.B))
    g.add((EX.A, SKOS.broadMatch, EX.B))
    r = check_skos(g, {"SkosScheme"})
    assert outcome(r, "L09") == "failed"


# ---------------------------------------------------- documentation

def test_unlabelled_terms_are_counted_not_just_flagged():
    g = base_scheme()
    g.add((EX.C, RDF.type, SKOS.Concept))  # no label
    r = check_documentation(g, {"SkosScheme"}, str(EX))
    assert outcome(r, "D01") == "failed"
    assert r["D01"]["affected"] == 1
    assert r["D01"]["population"] == 3
    assert r["D01"]["example"] == str(EX.C)


def test_definitions_accept_any_recognised_property():
    g = base_scheme()
    g.add((EX.A, SKOS.definition, Literal("a thing")))
    g.add((EX.B, RDFS.comment, Literal("another thing")))
    r = check_documentation(g, {"SkosScheme"}, str(EX))
    assert outcome(r, "D02") == "passed"


# ---------------------------------------------------------- governance

def test_missing_licence_fails():
    r = check_governance(base_scheme())
    assert outcome(r, "G01") == "failed"


def test_licence_detected_from_dcterms():
    g = base_scheme()
    g.add((EX.Scheme, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    r = check_governance(g)
    assert outcome(r, "G01") == "passed"


# ----------------------------------------------------------- stability

def test_stability_inapplicable_without_deprecation():
    r = check_stability(base_scheme(), str(EX))
    assert outcome(r, "S01") == "inapplicable"


def test_deprecated_without_successor_fails():
    g = base_scheme()
    g.add((EX.A, OWL.deprecated, Literal(True)))
    r = check_stability(g, str(EX))
    assert outcome(r, "S01") == "failed"


def test_deprecated_with_replacement_passes():
    g = base_scheme()
    g.add((EX.A, OWL.deprecated, Literal(True)))
    g.add((EX.A, DCTERMS.isReplacedBy, EX.B))
    r = check_stability(g, str(EX))
    assert outcome(r, "S01") == "passed"


# ------------------------------------------------------- encoding

def test_utf8_payload_is_self_describing():
    ok, _ = self_describing("<rdf:RDF>café</rdf:RDF>".encode("utf-8"), "xml")
    assert ok is True


def test_latin1_without_declaration_is_not_self_describing():
    ok, why = self_describing("<rdf:RDF>El Niño</rdf:RDF>".encode("iso-8859-1"), "xml")
    assert ok is False
    assert "no XML encoding declaration" in why


def test_declared_encoding_counts_as_self_describing():
    raw = '<?xml version="1.0" encoding="ISO-8859-1"?><rdf:RDF>El Niño</rdf:RDF>'.encode("iso-8859-1")
    ok, why = self_describing(raw, "xml")
    assert ok is True


def test_transport_charset_parsing():
    assert transport_charset("application/rdf+xml; charset=ISO-8859-1") == "iso-8859-1"
    assert transport_charset("text/turtle") is None


# ------------------------------------------------------ kind detection

def test_kind_detection_can_return_multiple_kinds():
    g = Graph()
    g.add((EX.C, RDF.type, OWL.Class))
    g.add((EX.K, RDF.type, SKOS.Concept))
    assert detect_kinds(g) == {"OwlOntology", "SkosScheme"}


def test_kind_detection_falls_back_to_codelist():
    g = Graph()
    g.add((EX.X, URIRef("http://example.org/p"), Literal("v")))
    assert detect_kinds(g) == {"CodeList"}
