"""Compact JSON-LD export — wraps OpenGloss records with @context and @id.

Instead of flattening to triples and re-serializing, this preserves the
original nested JSON structure and adds JSON-LD framing so the output is
valid RDF that any JSON-LD processor or SPARQL engine can consume.

Fields that represent references to other nodes (POS, synonyms, edge
targets, etc.) are rewritten as CURIEs so JSON-LD processors emit IRIs.

Output is ~same size as the source JSONL, not 2-3x like Turtle.
"""

from __future__ import annotations

import json
from typing import Any, TextIO
from urllib.parse import quote

from .context import JSONLD_CONTEXT

# Etymology fields that get grouped into an og:EtymologyTrail node
_ETYMOLOGY_TRAIL_FIELDS = {
    "etymology_summary",
    "etymology_cognates",
    "etymology_segments",
    "etymology_references",
}

# Derived fields that are redundant (computable from source fields).
# We strip these to keep the output clean — they add no RDF value.
_DERIVED_FIELDS = {
    "parts_of_speech",
    "num_parts_of_speech",
    "total_senses",
    "sense_count_by_pos",
    "senses",  # flattened v1.0 compat — redundant with entries[].senses
    "all_definitions",
    "all_synonyms",
    "all_antonyms",
    "all_hypernyms",
    "all_hyponyms",
    "all_collocations",
    "all_examples",
    "all_inflections",
    "all_derivations",
    "has_etymology",
    "has_encyclopedia",
    "has_lexical_explanation",
    "total_edges",
    "text",
}

# POS string → CURIE (e.g. "noun" → "lexinfo:noun")
_POS_CURIE: dict[str, str] = {
    "noun": "lexinfo:noun",
    "verb": "lexinfo:verb",
    "adjective": "lexinfo:adjective",
    "adverb": "lexinfo:adverb",
    "preposition": "lexinfo:preposition",
    "conjunction": "lexinfo:conjunction",
    "pronoun": "lexinfo:pronoun",
    "interjection": "lexinfo:interjection",
    "determiner": "lexinfo:determiner",
    "particle": "lexinfo:particle",
}

# Edge relationship_type → CURIE
_EDGE_TYPE_CURIE: dict[str, str] = {
    "synonym": "wn:synonym",
    "antonym": "wn:antonym",
    "hypernym": "wn:hypernym",
    "hyponym": "wn:hyponym",
    "collocation": "og:collocation",
    "derivation_noun": "og:derivationNoun",
    "derivation_verb": "og:derivationVerb",
    "derivation_adjective": "og:derivationAdjective",
    "derivation_adverb": "og:derivationAdverb",
    "inflection": "og:inflection",
    "etymology_parent": "og:etymologyParent",
    "cognate": "og:cognate",
}


def _safe_id(value: str) -> str:
    return quote(value, safe="")


def _word_to_entry_curie(word: str) -> str:
    """Convert a bare word string to an ogr:entry/ CURIE."""
    return f"ogr:entry/{_safe_id(word.lower().replace(' ', '_'))}"


def _strip_nulls(d: dict) -> dict:
    """Remove keys with None values and empty lists/dicts from a dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != {}}


def _transform_entries(entries: list[dict], word_id: str) -> list[dict]:
    """Rewrite POS entries so pos and sense relation fields are CURIEs."""
    result = []
    for entry in entries:
        entry = dict(entry)
        # pos → lexinfo CURIE; skip empty POS
        pos_str = entry.get("pos", "")
        if not pos_str:
            continue
        entry["pos"] = _POS_CURIE.get(pos_str, f"lexinfo:{_safe_id(pos_str)}")

        # senses: rewrite synonym/antonym/hypernym/hyponym to entry CURIEs, add @type
        if "senses" in entry:
            entry["senses"] = [_transform_sense(s) for s in entry["senses"]]

        # morphology.derivations: rewrite to entry CURIEs
        if "morphology" in entry and entry["morphology"]:
            entry["morphology"] = _transform_morphology(entry["morphology"])

        result.append(_strip_nulls(entry))
    return result


def _transform_morphology(morphology: dict) -> dict:
    """Rewrite derivation targets from bare words to entry CURIEs."""
    morphology = dict(morphology)
    derivations = morphology.get("derivations")
    if derivations and isinstance(derivations, dict):
        derivations = dict(derivations)
        for field in ("noun_forms", "verb_forms", "adjective_forms", "adverb_forms"):
            if field in derivations and derivations[field]:
                derivations[field] = [_word_to_entry_curie(w) for w in derivations[field]]
        morphology["derivations"] = _strip_nulls(derivations)
    inflections = morphology.get("inflections")
    if inflections and isinstance(inflections, dict):
        morphology["inflections"] = _strip_nulls(dict(inflections))
    return _strip_nulls(morphology)


def _transform_sense(sense: dict) -> dict:
    """Rewrite sense-level relation lists from bare words to entry CURIEs.
    Adds @type so senses parse as ontolex:LexicalSense nodes."""
    sense = dict(sense)
    sense["@type"] = "ontolex:LexicalSense"
    for field in ("synonyms", "antonyms", "hypernyms", "hyponyms"):
        if field in sense and sense[field]:
            sense[field] = [_word_to_entry_curie(w) for w in sense[field]]
    return _strip_nulls(sense)


def _transform_edges(edges: list[dict]) -> list[dict]:
    """Rewrite edge source_word, target_word, and relationship_type to CURIEs.
    Adds @type so edges parse as og:LexicalRelation nodes.
    Serializes metadata as a JSON string (inner keys have no context mappings)."""
    result = []
    for edge in edges:
        edge = dict(edge)
        edge["@type"] = "og:LexicalRelation"
        if "source_word" in edge:
            edge["source_word"] = _word_to_entry_curie(edge["source_word"])
        if "target_word" in edge:
            edge["target_word"] = _word_to_entry_curie(edge["target_word"])
        if "relationship_type" in edge:
            rt = edge["relationship_type"]
            edge["relationship_type"] = _EDGE_TYPE_CURIE.get(rt, f"og:{_safe_id(rt)}")
        # Serialize metadata as JSON string so inner keys aren't lost
        meta = edge.get("metadata")
        if meta and isinstance(meta, dict):
            cleaned = {k: v for k, v in meta.items() if v is not None}
            edge["metadata"] = json.dumps(cleaned, ensure_ascii=False) if cleaned else None
        result.append(_strip_nulls(edge))
    return result


def _transform_etymology_segments(segments: list[dict]) -> list[dict]:
    """Add @type to etymology segments so they parse as og:EtymologySegment nodes."""
    result = []
    for seg in segments:
        seg = dict(seg)
        seg["@type"] = "og:EtymologySegment"
        result.append(_strip_nulls(seg))
    return result


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a single OpenGlossWordRecord dict to a compact JSON-LD node.

    Adds @type and @id, strips derived fields, and rewrites reference fields
    (POS, synonyms, edge targets, etc.) as CURIEs so the output is valid
    JSON-LD with proper IRI semantics.
    """
    word_id = record.get("id") or record["word"].lower().replace(" ", "_")
    safe_wid = _safe_id(word_id)

    node: dict[str, Any] = {
        "@id": f"ogr:entry/{safe_wid}",
        "@type": "ontolex:LexicalEntry",
    }

    # Canonical form — matches triples path's ontolex:canonicalForm BNode
    word = record.get("word", "")
    if word:
        node["canonical_form"] = {
            "@type": "ontolex:Form",
            "written_rep": word,
        }

    for key, value in record.items():
        if key == "id":
            continue  # already used for @id
        if key in _DERIVED_FIELDS:
            continue
        if key in _ETYMOLOGY_TRAIL_FIELDS:
            continue  # grouped into trail node below
        if value is None:
            continue
        if value == "" or value == [] or value == {}:
            continue

        # Rewrite fields that must be IRIs or need @type
        if key == "entries":
            node[key] = _transform_entries(value, safe_wid)
        elif key == "edges":
            node[key] = _transform_edges(value)
        else:
            node[key] = value

    # Group etymology fields into a typed og:EtymologyTrail node
    trail: dict[str, Any] = {}
    for field in _ETYMOLOGY_TRAIL_FIELDS:
        val = record.get(field)
        if val is not None and val != "" and val != []:
            if field == "etymology_segments":
                trail[field] = _transform_etymology_segments(val)
            else:
                trail[field] = val
    if trail:
        trail["@type"] = "og:EtymologyTrail"
        trail["@id"] = f"ogr:etymology/{safe_wid}"
        node["etymology"] = trail

    return node


def write_compact_jsonld(
    records,
    out: TextIO,
    *,
    progress_fn=None,
) -> int:
    """Stream compact JSON-LD to a file handle.

    Writes a single JSON-LD document with @context at the top and @graph
    containing all record nodes.

    Args:
        records: Iterable of OpenGlossWordRecord dicts (pre-sliced by caller).
        out: Writable text stream.
        progress_fn: Optional callback(count) for progress reporting.

    Returns:
        Number of records written.
    """
    # Write opening structure
    out.write('{\n')
    out.write(f'  "@context": {json.dumps(JSONLD_CONTEXT, indent=4, ensure_ascii=False)},\n')
    out.write('  "@graph": [\n')

    count = 0
    for record in records:
        node = compact_record(record)

        prefix = "    " if count == 0 else ",\n    "
        out.write(prefix)
        out.write(json.dumps(node, ensure_ascii=False))

        count += 1
        if progress_fn and count % 10_000 == 0:
            progress_fn(count)

    out.write('\n  ]\n}\n')
    return count
