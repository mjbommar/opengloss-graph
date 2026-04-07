"""JSON-LD @context definition mapping all 52 OpenGloss fields to RDF URIs.

This context allows the original JSON record structure to serve as valid
JSON-LD without flattening into triples — keeping the output compact.

Fields whose values are references to other nodes (entries, POS URIs, edge
types) are marked with ``@type: @id`` so JSON-LD processors emit IRIs
instead of plain literals.
"""

from __future__ import annotations

# The shared JSON-LD context. Every key in the OpenGlossWordRecord schema
# that carries semantic meaning is mapped to an RDF property or type.
JSONLD_CONTEXT: dict = {
    # --- Namespace prefixes ---
    "og": "https://opengloss.org/ontology#",
    "ogr": "https://opengloss.org/resource/",
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "lexinfo": "http://www.lexinfo.net/ontology/3.0/lexinfo#",
    "vartrans": "http://www.w3.org/ns/lemon/vartrans#",
    "frac": "http://www.w3.org/ns/lemon/frac#",
    "wn": "https://globalwordnet.github.io/schemas/wn#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",

    # --- Field 1: id → node identity ---
    # Handled via @id in each record

    # --- Field 2: word ---
    "word": {"@id": "rdfs:label", "@language": "en"},
    "canonical_form": {"@id": "ontolex:canonicalForm"},
    "written_rep": {"@id": "ontolex:writtenRep", "@language": "en"},

    # --- Fields 3-5: timestamps ---
    "created_at": {"@id": "dcterms:created", "@type": "xsd:dateTime"},
    "updated_at": {"@id": "dcterms:modified", "@type": "xsd:dateTime"},
    "processed_at": {"@id": "og:processedAt", "@type": "xsd:dateTime"},

    # --- Field 6: language ---
    "language": "dcterms:language",

    # --- Field 7: reading level ---
    "reading_level": "og:readingLevel",

    # --- Field 8: tags ---
    "tags": "dcterms:subject",

    # --- Fields 9-10: stopword ---
    "is_stopword": {"@id": "og:isStopword", "@type": "xsd:boolean"},
    "stopword_reason": "og:stopwordReason",

    # --- Field 11-31: entries (POS → senses → morphology) ---
    "entries": {"@id": "og:hasPOSEntry", "@container": "@list"},

    # POS entry fields — pos is an IRI (lexinfo:noun, lexinfo:verb, etc.)
    "pos": {"@id": "lexinfo:partOfSpeech", "@type": "@id"},
    "senses": {"@id": "ontolex:sense", "@container": "@list"},
    "morphology": "og:morphology",
    "collocations": "og:collocation",

    # Sense fields (12-18) — synonyms/antonyms/hypernyms/hyponyms are IRIs
    "sense_index": {"@id": "og:senseIndex", "@type": "xsd:integer"},
    "definition": {"@id": "skos:definition", "@language": "en"},
    "synonyms": {"@id": "wn:synonym", "@type": "@id"},
    "antonyms": {"@id": "wn:antonym", "@type": "@id"},
    "hypernyms": {"@id": "skos:broader", "@type": "@id"},
    "hyponyms": {"@id": "skos:narrower", "@type": "@id"},
    "examples": {"@id": "skos:example", "@language": "en"},

    # Morphology fields (19-30)
    "base_form": "og:baseForm",
    "inflections": "og:inflections",
    "derivations": "og:derivations",

    # Inflection sub-fields (20-26)
    "plural": "lexinfo:plural",
    "past_tense": "lexinfo:pastTense",
    "past_participle": "lexinfo:pastParticiple",
    "present_participle": "lexinfo:presentParticiple",
    "third_person_singular": "lexinfo:thirdPersonSingular",
    "comparative": "lexinfo:comparative",
    "superlative": "lexinfo:superlative",

    # Derivation sub-fields (27-30) — values are entry IRIs
    "noun_forms": {"@id": "og:derivationNoun", "@type": "@id"},
    "verb_forms": {"@id": "og:derivationVerb", "@type": "@id"},
    "adjective_forms": {"@id": "og:derivationAdjective", "@type": "@id"},
    "adverb_forms": {"@id": "og:derivationAdverb", "@type": "@id"},

    # --- Fields 32-41: etymology ---
    "etymology": {"@id": "og:etymologyTrail", "@type": "@id"},
    "etymology_summary": {"@id": "skos:note", "@language": "en"},
    "etymology_cognates": "og:cognate",
    "etymology_segments": {"@id": "og:etymologySegment", "@container": "@list"},
    "etymology_references": "dcterms:references",

    # Etymology segment sub-fields (34-40)
    "order": {"@id": "og:etymologyOrder", "@type": "xsd:integer"},
    # "language" already mapped above via dcterms:language
    "headword": "ontolex:writtenRep",
    "gloss": {"@id": "skos:definition", "@language": "en"},
    "era": "og:era",
    "notes": "rdfs:comment",
    "sources": "dcterms:source",

    # --- Field 42: encyclopedia ---
    "encyclopedia_entry": {"@id": "og:encyclopediaEntry", "@language": "en"},

    # --- Field 43: lexical explanation ---
    "lexical_explanation": {"@id": "og:lexicalExplanation", "@language": "en"},

    # --- Fields 44-45: frequency ---
    "wiki_frequency": {"@id": "og:wikiFrequency", "@type": "xsd:integer"},
    "wiki_frequency_rank": {"@id": "og:wikiFrequencyRank", "@type": "xsd:integer"},

    # --- Fields 46-52: edges ---
    "edges": {"@id": "og:hasEdge", "@container": "@list"},
    "source_word": {"@id": "og:sourceWord", "@type": "@id"},
    "target_word": {"@id": "og:targetWord", "@type": "@id"},
    "relationship_type": {"@id": "og:relationshipType", "@type": "@id"},
    "source_pos": "og:sourcePOS",
    "target_pos": "og:targetPOS",
    # sense_index already mapped above
    "metadata": "og:edgeMetadata",
}


def build_context() -> dict:
    """Return a copy of the JSON-LD context dict."""
    return dict(JSONLD_CONTEXT)
