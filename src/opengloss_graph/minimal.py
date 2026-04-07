"""Minimal word-to-word relation graph — just direct triples, no metadata.

Emits only:
  - Semantic relations: synonym, antonym, hypernym, hyponym
  - Morphological: inflections (plural, past_tense, etc.), derivations
  - Collocations
  - rdfs:label for each entry that appears as a subject

No reification, no etymology, no encyclopedia, no frequency, no senses.
Output is streamable N-Triples.
"""

from __future__ import annotations

from typing import Any, TextIO
from urllib.parse import quote

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

from .namespaces import (
    EDGE_TYPE_MAP,
    INFLECTION_MAP,
    LEXINFO,
    OG,
    OGR,
    ONTOLEX,
    WN,
    NS_BINDINGS,
)


def _safe_id(value: str) -> str:
    return quote(value, safe="")


def _entry_uri(word: str) -> URIRef:
    return OGR[f"entry/{_safe_id(word.lower().replace(' ', '_'))}"]


# Derivation field → RDF predicate
_DERIVATION_MAP: dict[str, URIRef] = {
    "noun_forms": OG.derivationNoun,
    "verb_forms": OG.derivationVerb,
    "adjective_forms": OG.derivationAdjective,
    "adverb_forms": OG.derivationAdverb,
}


def convert_minimal(g: Graph, record: dict[str, Any]) -> None:
    """Add only word-to-word relation triples for a single record."""
    word = record["word"]
    lang = record.get("language") or "en"
    entry = _entry_uri(word)

    # Label
    g.add((entry, RDF.type, ONTOLEX.LexicalEntry))
    g.add((entry, RDFS.label, Literal(word, lang=lang)))

    # POS
    for pos_entry in record.get("entries") or []:
        pos_str = pos_entry.get("pos", "")
        if pos_str:
            from .namespaces import POS_MAP
            pos_uri = URIRef(POS_MAP.get(pos_str, str(LEXINFO[_safe_id(pos_str)])))
            g.add((entry, LEXINFO.partOfSpeech, pos_uri))

        # Sense-level relations
        for sense in pos_entry.get("senses") or []:
            for syn in sense.get("synonyms") or []:
                g.add((entry, WN.synonym, _entry_uri(syn)))
            for ant in sense.get("antonyms") or []:
                g.add((entry, WN.antonym, _entry_uri(ant)))
            for hyp in sense.get("hypernyms") or []:
                g.add((entry, SKOS.broader, _entry_uri(hyp)))
            for hyp in sense.get("hyponyms") or []:
                g.add((entry, SKOS.narrower, _entry_uri(hyp)))

        # Morphology — inflections
        morphology = pos_entry.get("morphology") or {}
        inflections = morphology.get("inflections") or {}
        for field_name, pred_str in INFLECTION_MAP.items():
            for form_val in inflections.get(field_name) or []:
                g.add((entry, URIRef(pred_str), _entry_uri(form_val)))

        # Morphology — derivations
        derivations = morphology.get("derivations") or {}
        for field_name, pred in _DERIVATION_MAP.items():
            for deriv_val in derivations.get(field_name) or []:
                g.add((entry, pred, _entry_uri(deriv_val)))

        # Collocations
        for colloc in pos_entry.get("collocations") or []:
            g.add((entry, OG.collocation, _entry_uri(colloc)))


def new_minimal_graph() -> Graph:
    """Create a graph with only the namespaces used by minimal output."""
    g = Graph()
    for prefix, ns in NS_BINDINGS.items():
        g.bind(prefix, ns)
    return g
