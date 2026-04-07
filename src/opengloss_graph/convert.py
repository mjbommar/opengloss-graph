"""Convert OpenGloss v1.1 JSONL records to an RDF graph.

Covers all 52 source fields from OpenGlossWordRecord:
  1  id                                    → URI identity
  2  word                                  → ontolex:writtenRep on canonical form
  3  created_at                            → dcterms:created
  4  updated_at                            → dcterms:modified
  5  processed_at                          → og:processedAt
  6  language                              → dcterms:language + @lang tags
  7  reading_level                         → og:readingLevel
  8  tags                                  → dcterms:subject
  9  is_stopword                           → og:isStopword
  10 stopword_reason                       → og:stopwordReason
  11 entries[].pos                         → lexinfo:partOfSpeech
  12 entries[].senses[].sense_index        → og:senseIndex + encoded in sense URI
  13 entries[].senses[].definition         → skos:definition
  14 entries[].senses[].synonyms           → wn:synonym links
  15 entries[].senses[].antonyms           → wn:antonym links
  16 entries[].senses[].hypernyms          → skos:broader
  17 entries[].senses[].hyponyms           → skos:narrower
  18 entries[].senses[].examples           → skos:example
  19 entries[].morphology.base_form        → og:baseForm
  20 entries[].morphology.inflections.plural           → otherForm + lexinfo
  21 entries[].morphology.inflections.past_tense       → otherForm + lexinfo
  22 entries[].morphology.inflections.past_participle  → otherForm + lexinfo
  23 entries[].morphology.inflections.present_participle → otherForm + lexinfo
  24 entries[].morphology.inflections.third_person_singular → otherForm + lexinfo
  25 entries[].morphology.inflections.comparative      → otherForm + lexinfo
  26 entries[].morphology.inflections.superlative      → otherForm + lexinfo
  27 entries[].morphology.derivations.noun_forms       → vartrans + lexinfo:noun
  28 entries[].morphology.derivations.verb_forms       → vartrans + lexinfo:verb
  29 entries[].morphology.derivations.adjective_forms  → vartrans + lexinfo:adjective
  30 entries[].morphology.derivations.adverb_forms     → vartrans + lexinfo:adverb
  31 entries[].collocations                → og:collocation literal
  32 etymology_summary                     → skos:note on etymology node
  33 etymology_cognates                    → og:cognate literals
  34 etymology_segments[].order            → og:etymologyOrder
  35 etymology_segments[].language         → dcterms:language on segment
  36 etymology_segments[].headword         → ontolex:writtenRep on segment
  37 etymology_segments[].gloss            → skos:definition on segment
  38 etymology_segments[].era              → og:era on segment
  39 etymology_segments[].notes            → rdfs:comment on segment
  40 etymology_segments[].sources          → dcterms:source on segment
  41 etymology_references                  → dcterms:references on etymology node
  42 encyclopedia_entry                    → og:encyclopediaEntry
  43 lexical_explanation                   → og:lexicalExplanation
  44 wiki_frequency                        → og:wikiFrequency
  45 wiki_frequency_rank                   → og:wikiFrequencyRank
  46 edges[].source_word                   → og:sourceEntry on reified relation
  47 edges[].target_word                   → og:targetEntry on reified relation
  48 edges[].relationship_type             → og:relationCategory
  49 edges[].source_pos                    → og:sourcePOS
  50 edges[].target_pos                    → og:targetPOS
  51 edges[].sense_index                   → og:senseIndex
  52 edges[].metadata                      → key/value properties on reified relation
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS, XSD

from .namespaces import (
    EDGE_TYPE_MAP,
    INFLECTION_MAP,
    LEXINFO,
    OG,
    OGR,
    ONTOLEX,
    POS_MAP,
    VARTRANS,
    WN,
    NS_BINDINGS,
)


def _safe_id(value: str) -> str:
    """URL-encode an id for use in a URI path segment."""
    return quote(value, safe="")


def _entry_uri(word_id: str) -> URIRef:
    return OGR[f"entry/{_safe_id(word_id)}"]


def _sense_uri(word_id: str, pos: str, sense_idx: int) -> URIRef:
    return OGR[f"sense/{_safe_id(word_id)}_{_safe_id(pos)}_{sense_idx}"]


def _form_uri(word_id: str, pos: str, form_type: str, value: str) -> URIRef:
    h = hashlib.md5(f"{word_id}:{pos}:{form_type}:{value}".encode()).hexdigest()[:12]
    return OGR[f"form/{_safe_id(word_id)}_{_safe_id(pos)}_{_safe_id(form_type)}_{h}"]


def _etymology_uri(word_id: str) -> URIRef:
    return OGR[f"etymology/{_safe_id(word_id)}"]


def _etymology_segment_uri(word_id: str, order: int) -> URIRef:
    return OGR[f"etymology-segment/{_safe_id(word_id)}_{order}"]


def _edge_uri(source: str, target: str, rel_type: str, sense_idx: int | None) -> URIRef:
    key = f"{source}:{target}:{rel_type}:{sense_idx}"
    h = hashlib.md5(key.encode()).hexdigest()[:16]
    return OGR[f"edge/{h}"]


def _derivation_uri(word_id: str, pos: str, target_pos: str, value: str) -> URIRef:
    h = hashlib.md5(f"{word_id}:{pos}:{target_pos}:{value}".encode()).hexdigest()[:12]
    return OGR[f"derivation/{_safe_id(word_id)}_{h}"]


def convert_record(g: Graph, record: dict[str, Any], lang: str = "en") -> None:
    """Add all triples for a single OpenGlossWordRecord to the graph.

    Args:
        g: The target RDF graph.
        record: A dict matching the OpenGlossWordRecord schema.
        lang: Default language tag (overridden by record['language'] if present).
    """
    word_id = record.get("id") or record["word"].lower().replace(" ", "_")
    word = record["word"]
    lang = record.get("language") or lang
    entry = _entry_uri(word_id)

    # --- Field 1-2: identity ---
    g.add((entry, RDF.type, ONTOLEX.LexicalEntry))
    g.add((entry, RDFS.label, Literal(word, lang=lang)))

    # Canonical form node (written rep) — field 2
    canon = BNode()
    g.add((entry, ONTOLEX.canonicalForm, canon))
    g.add((canon, RDF.type, ONTOLEX.Form))
    g.add((canon, ONTOLEX.writtenRep, Literal(word, lang=lang)))

    # --- Fields 3-5: timestamps ---
    if record.get("created_at"):
        g.add((entry, DCTERMS.created, Literal(record["created_at"], datatype=XSD.dateTime)))
    if record.get("updated_at"):
        g.add((entry, DCTERMS.modified, Literal(record["updated_at"], datatype=XSD.dateTime)))
    if record.get("processed_at"):
        g.add((entry, OG.processedAt, Literal(record["processed_at"], datatype=XSD.dateTime)))

    # --- Field 6: language ---
    g.add((entry, DCTERMS.language, Literal(lang)))

    # --- Field 7: reading level ---
    if record.get("reading_level"):
        g.add((entry, OG.readingLevel, Literal(record["reading_level"])))

    # --- Field 8: tags ---
    for tag in record.get("tags") or []:
        g.add((entry, DCTERMS.subject, Literal(tag)))

    # --- Fields 9-10: stopword ---
    g.add((entry, OG.isStopword, Literal(record.get("is_stopword", False), datatype=XSD.boolean)))
    if record.get("stopword_reason"):
        g.add((entry, OG.stopwordReason, Literal(record["stopword_reason"])))

    # --- Fields 11-31: entries (POS → senses → morphology) ---
    for pos_entry in record.get("entries") or []:
        pos_str = pos_entry.get("pos", "")
        pos_uri = URIRef(POS_MAP.get(pos_str, str(LEXINFO[_safe_id(pos_str)])))

        # Field 11: part of speech
        g.add((entry, LEXINFO.partOfSpeech, pos_uri))

        # Fields 12-18: senses
        for sense in pos_entry.get("senses") or []:
            sense_idx = sense.get("sense_index", 0)
            sense_node = _sense_uri(word_id, pos_str, sense_idx)

            g.add((sense_node, RDF.type, ONTOLEX.LexicalSense))
            g.add((entry, ONTOLEX.sense, sense_node))

            # Field 12: sense index
            g.add((sense_node, OG.senseIndex, Literal(sense_idx, datatype=XSD.integer)))

            # Field 13: definition
            if sense.get("definition"):
                g.add((sense_node, SKOS.definition, Literal(sense["definition"], lang=lang)))

            # Field 14: synonyms
            for syn in sense.get("synonyms") or []:
                target = _entry_uri(syn.lower().replace(" ", "_"))
                g.add((sense_node, WN.synonym, target))

            # Field 15: antonyms
            for ant in sense.get("antonyms") or []:
                target = _entry_uri(ant.lower().replace(" ", "_"))
                g.add((sense_node, WN.antonym, target))

            # Field 16: hypernyms
            for hyp in sense.get("hypernyms") or []:
                target = _entry_uri(hyp.lower().replace(" ", "_"))
                g.add((sense_node, SKOS.broader, target))

            # Field 17: hyponyms
            for hyp in sense.get("hyponyms") or []:
                target = _entry_uri(hyp.lower().replace(" ", "_"))
                g.add((sense_node, SKOS.narrower, target))

            # Field 18: examples
            for ex in sense.get("examples") or []:
                g.add((sense_node, SKOS.example, Literal(ex, lang=lang)))

        # Fields 19-30: morphology
        morphology = pos_entry.get("morphology") or {}

        # Field 19: base form (recorded as a literal; the entry-level
        # canonicalForm BNode already carries the writtenRep for the word)
        base_form = morphology.get("base_form", "")
        if base_form:
            g.add((entry, OG.baseForm, Literal(base_form, lang=lang)))

        # Fields 20-26: inflections
        inflections = morphology.get("inflections") or {}
        for field_name, lexinfo_uri_str in INFLECTION_MAP.items():
            for form_val in inflections.get(field_name) or []:
                form_node = _form_uri(word_id, pos_str, field_name, form_val)
                g.add((form_node, RDF.type, ONTOLEX.Form))
                g.add((form_node, ONTOLEX.writtenRep, Literal(form_val, lang=lang)))
                g.add((form_node, LEXINFO.morphologicalFeature, URIRef(lexinfo_uri_str)))
                g.add((entry, ONTOLEX.otherForm, form_node))

        # Fields 27-30: derivations
        derivations = morphology.get("derivations") or {}
        derivation_pos_map = {
            "noun_forms": LEXINFO.noun,
            "verb_forms": LEXINFO.verb,
            "adjective_forms": LEXINFO.adjective,
            "adverb_forms": LEXINFO.adverb,
        }
        for field_name, target_pos_uri in derivation_pos_map.items():
            for deriv_val in derivations.get(field_name) or []:
                deriv_entry = _entry_uri(deriv_val.lower().replace(" ", "_"))
                rel_node = _derivation_uri(word_id, pos_str, field_name, deriv_val)
                g.add((rel_node, RDF.type, VARTRANS.LexicalRelation))
                g.add((rel_node, VARTRANS.source, entry))
                g.add((rel_node, VARTRANS.target, deriv_entry))
                g.add((rel_node, VARTRANS.category, target_pos_uri))

        # Field 31: collocations
        for colloc in pos_entry.get("collocations") or []:
            g.add((entry, OG.collocation, Literal(colloc, lang=lang)))

    # --- Fields 32-41: etymology ---
    has_etymology = (
        record.get("etymology_summary")
        or record.get("etymology_segments")
        or record.get("etymology_cognates")
        or record.get("etymology_references")
    )
    if has_etymology:
        etym_node = _etymology_uri(word_id)
        g.add((etym_node, RDF.type, OG.EtymologyTrail))
        g.add((entry, OG.etymologyTrail, etym_node))

        # Field 32: summary
        if record.get("etymology_summary"):
            g.add((etym_node, SKOS.note, Literal(record["etymology_summary"], lang=lang)))

        # Field 33: cognates
        for cog in record.get("etymology_cognates") or []:
            g.add((etym_node, OG.cognate, Literal(cog)))

        # Fields 34-40: segments
        for seg in record.get("etymology_segments") or []:
            order = seg.get("order", 0)
            seg_node = _etymology_segment_uri(word_id, order)
            g.add((seg_node, RDF.type, OG.EtymologySegment))
            g.add((etym_node, OG.etymologySegment, seg_node))

            # Field 34: order
            g.add((seg_node, OG.etymologyOrder, Literal(order, datatype=XSD.integer)))

            # Field 35: language
            if seg.get("language"):
                g.add((seg_node, DCTERMS.language, Literal(seg["language"])))

            # Field 36: headword
            if seg.get("headword"):
                g.add((seg_node, ONTOLEX.writtenRep, Literal(seg["headword"])))

            # Field 37: gloss
            if seg.get("gloss"):
                g.add((seg_node, SKOS.definition, Literal(seg["gloss"], lang="en")))

            # Field 38: era
            if seg.get("era"):
                g.add((seg_node, OG.era, Literal(seg["era"])))

            # Field 39: notes
            if seg.get("notes"):
                g.add((seg_node, RDFS.comment, Literal(seg["notes"])))

            # Field 40: sources
            for src in seg.get("sources") or []:
                g.add((seg_node, DCTERMS.source, Literal(src)))

        # Field 41: etymology references
        for ref in record.get("etymology_references") or []:
            g.add((etym_node, DCTERMS.references, Literal(ref)))

    # --- Field 42: encyclopedia entry ---
    if record.get("encyclopedia_entry"):
        g.add((entry, OG.encyclopediaEntry, Literal(record["encyclopedia_entry"], lang=lang)))

    # --- Field 43: lexical explanation ---
    if record.get("lexical_explanation"):
        g.add((entry, OG.lexicalExplanation, Literal(record["lexical_explanation"], lang=lang)))

    # --- Fields 44-45: frequency ---
    wiki_freq = record.get("wiki_frequency", 0)
    if wiki_freq:
        g.add((entry, OG.wikiFrequency, Literal(wiki_freq, datatype=XSD.integer)))
    wiki_rank = record.get("wiki_frequency_rank")
    if wiki_rank is not None:
        g.add((entry, OG.wikiFrequencyRank, Literal(wiki_rank, datatype=XSD.integer)))

    # --- Fields 46-52: edges (reified relations) ---
    for edge in record.get("edges") or []:
        source_word = edge.get("source_word", "")
        target_word = edge.get("target_word", "")
        rel_type = edge.get("relationship_type", "related")
        sense_idx = edge.get("sense_index")

        edge_node = _edge_uri(source_word, target_word, rel_type, sense_idx)
        g.add((edge_node, RDF.type, OG.LexicalRelation))

        # Field 46: source
        source_entry = _entry_uri(source_word.lower().replace(" ", "_"))
        g.add((edge_node, OG.sourceEntry, source_entry))

        # Field 47: target
        target_entry = _entry_uri(target_word.lower().replace(" ", "_"))
        g.add((edge_node, OG.targetEntry, target_entry))

        # Field 48: relationship type
        rel_pred = EDGE_TYPE_MAP.get(rel_type)
        if rel_pred:
            g.add((edge_node, OG.relationCategory, URIRef(rel_pred)))
        else:
            g.add((edge_node, OG.relationCategory, Literal(rel_type)))

        # Also add a direct triple between source and target for queryability
        if rel_pred:
            g.add((source_entry, URIRef(rel_pred), target_entry))

        # Field 49: source POS
        if edge.get("source_pos"):
            g.add((edge_node, OG.sourcePOS, Literal(edge["source_pos"])))

        # Field 50: target POS
        if edge.get("target_pos"):
            g.add((edge_node, OG.targetPOS, Literal(edge["target_pos"])))

        # Field 51: sense index
        if sense_idx is not None:
            g.add((edge_node, OG.senseIndex, Literal(sense_idx, datatype=XSD.integer)))

        # Field 52: metadata dict
        edge_meta = edge.get("metadata")
        if edge_meta and isinstance(edge_meta, dict):
            for mk, mv in edge_meta.items():
                if mv is None:
                    continue
                # Mint a property under og: for each metadata key
                prop = OG[f"edgeMeta_{_safe_id(mk)}"]
                if isinstance(mv, bool):
                    g.add((edge_node, prop, Literal(mv, datatype=XSD.boolean)))
                elif isinstance(mv, int):
                    g.add((edge_node, prop, Literal(mv, datatype=XSD.integer)))
                elif isinstance(mv, float):
                    g.add((edge_node, prop, Literal(mv, datatype=XSD.double)))
                elif isinstance(mv, (dict, list)):
                    g.add((edge_node, prop, Literal(json.dumps(mv), datatype=XSD.string)))
                else:
                    g.add((edge_node, prop, Literal(str(mv))))


def new_graph() -> Graph:
    """Create a new graph with all namespace bindings."""
    g = Graph()
    for prefix, ns in NS_BINDINGS.items():
        g.bind(prefix, ns)
    return g
