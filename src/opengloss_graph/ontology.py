"""OWL ontology for OpenGloss custom properties not covered by standard vocabs."""

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from .namespaces import OG, ONTOLEX, NS_BINDINGS


def build_ontology() -> Graph:
    """Return an RDF graph containing the og: OWL ontology."""
    g = Graph()
    for prefix, ns in NS_BINDINGS.items():
        g.bind(prefix, ns)

    ont = OG[""]
    g.add((ont, RDF.type, OWL.Ontology))
    g.add((ont, RDFS.label, Literal("OpenGloss Ontology")))
    g.add((ont, RDFS.comment, Literal(
        "Custom properties for the OpenGloss v1.1 dictionary RDF export. "
        "Extends Ontolex-Lemon, SKOS, lexinfo, FrAC, and Global WordNet."
    )))
    g.add((ont, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    g.add((ont, OWL.imports, URIRef("http://www.w3.org/ns/lemon/ontolex")))

    # --- Custom datatype properties ---
    _dp = _datatype_property_adder(g)

    # Entry-level datatype properties
    _dp(OG.readingLevel, "readingLevel",
        "Target reading level (K, 1-12, BS, PhD, middle_school, etc.)",
        ONTOLEX.LexicalEntry, XSD.string)
    _dp(OG.isStopword, "isStopword",
        "Whether this entry is classified as a stopword.",
        ONTOLEX.LexicalEntry, XSD.boolean)
    _dp(OG.stopwordReason, "stopwordReason",
        "Reason for the stopword classification.",
        ONTOLEX.LexicalEntry, XSD.string)
    _dp(OG.processedAt, "processedAt",
        "Timestamp when the entry was last processed.",
        ONTOLEX.LexicalEntry, XSD.dateTime)
    _dp(OG.encyclopediaEntry, "encyclopediaEntry",
        "Encyclopedic prose description of the word.",
        ONTOLEX.LexicalEntry, XSD.string)
    _dp(OG.lexicalExplanation, "lexicalExplanation",
        "Prose explanation of lexical relationships.",
        ONTOLEX.LexicalEntry, XSD.string)
    _dp(OG.wikiFrequency, "wikiFrequency",
        "Raw occurrence count from Wikipedia.",
        ONTOLEX.LexicalEntry, XSD.integer)
    _dp(OG.wikiFrequencyRank, "wikiFrequencyRank",
        "Frequency rank (1 = most common).",
        ONTOLEX.LexicalEntry, XSD.integer)
    _dp(OG.baseForm, "baseForm",
        "Morphological base form for a given POS.",
        ONTOLEX.LexicalEntry, XSD.string)
    # Sense-level datatype properties
    _dp(OG.senseIndex, "senseIndex",
        "Zero-based index of a sense within its POS entry.",
        None, XSD.integer)

    # Etymology segment properties
    _dp(OG.etymologyOrder, "etymologyOrder",
        "Position in the etymology chain (0 = earliest).",
        OG.EtymologySegment, XSD.integer)
    _dp(OG.era, "era",
        "Historical time period for an etymology segment.",
        OG.EtymologySegment, XSD.string)

    # Edge properties (flat triples path uses reified og:LexicalRelation nodes;
    # compact JSON-LD path uses these as direct properties on edge objects)
    _dp(OG.sourcePOS, "sourcePOS",
        "Part of speech of the source word in a lexical relation.",
        None, XSD.string)
    _dp(OG.targetPOS, "targetPOS",
        "Part of speech of the target word in a lexical relation.",
        None, XSD.string)

    # --- Custom object properties ---
    _op = _object_property_adder(g)

    # Structural properties (used by compact JSON-LD)
    _op(OG.hasPOSEntry, "hasPOSEntry",
        "Links a lexical entry to a part-of-speech entry container.",
        ONTOLEX.LexicalEntry, None)
    _op(OG.hasEdge, "hasEdge",
        "Links a lexical entry to a semantic edge record.",
        ONTOLEX.LexicalEntry, None)
    _op(OG.morphology, "morphology",
        "Links a POS entry to its morphology record.",
        None, None)
    _op(OG.inflections, "inflections",
        "Links a morphology record to its inflection data.",
        None, None)
    _op(OG.derivations, "derivations",
        "Links a morphology record to its derivation data.",
        None, None)

    # Edge reference properties
    _op(OG.sourceWord, "sourceWord",
        "Source entry of a semantic edge.",
        None, ONTOLEX.LexicalEntry)
    _op(OG.targetWord, "targetWord",
        "Target entry of a semantic edge.",
        None, ONTOLEX.LexicalEntry)
    _op(OG.relationshipType, "relationshipType",
        "The semantic relationship type of an edge (IRI).",
        None, None)
    _dp(OG.edgeMetadata, "edgeMetadata",
        "Arbitrary metadata attached to a semantic edge.",
        None, None)

    # Etymology properties
    _op(OG.etymologyTrail, "etymologyTrail",
        "Links a lexical entry to its etymology record.",
        ONTOLEX.LexicalEntry, OG.EtymologyTrail)
    _op(OG.etymologySegment, "etymologySegment",
        "Links an etymology trail to one of its historical segments.",
        OG.EtymologyTrail, OG.EtymologySegment)

    # Flat triples path: reified relation properties
    _op(OG.sourceEntry, "sourceEntry",
        "Source lexical entry of a reified relation.",
        OG.LexicalRelation, ONTOLEX.LexicalEntry)
    _op(OG.targetEntry, "targetEntry",
        "Target lexical entry of a reified relation.",
        OG.LexicalRelation, ONTOLEX.LexicalEntry)
    _op(OG.relationCategory, "relationCategory",
        "The type/category of a reified lexical relation.",
        OG.LexicalRelation, None)

    # Semantic relationship object properties (used as direct predicates)
    for prop_name, desc in [
        ("derivationNoun", "Derivational relation to a noun form."),
        ("derivationVerb", "Derivational relation to a verb form."),
        ("derivationAdjective", "Derivational relation to an adjective form."),
        ("derivationAdverb", "Derivational relation to an adverb form."),
        ("inflection", "Inflectional relation to a word form."),
        ("etymologyParent", "Etymological parent relation."),
    ]:
        uri = OG[prop_name]
        g.add((uri, RDF.type, OWL.ObjectProperty))
        g.add((uri, RDFS.label, Literal(prop_name)))
        g.add((uri, RDFS.comment, Literal(desc)))

    # Properties used as both literals (compact) and IRIs (triples edge links).
    # Declared as rdf:Property to avoid OWL DL DatatypeProperty/ObjectProperty conflict.
    for prop_name, desc in [
        ("collocation", "A collocated word or phrase (literal or entry IRI)."),
        ("cognate", "A cognate word in another language (literal or entry IRI)."),
    ]:
        uri = OG[prop_name]
        g.add((uri, RDF.type, RDF.Property))
        g.add((uri, RDFS.label, Literal(prop_name)))
        g.add((uri, RDFS.comment, Literal(desc)))

    # --- Custom classes ---
    for cls_name, desc in [
        ("EtymologyTrail", "Container for the full etymology of a lexical entry."),
        ("EtymologySegment", "A single step in the historical etymology chain."),
        ("LexicalRelation", "Reified lexical relation edge with metadata."),
    ]:
        uri = OG[cls_name]
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(cls_name)))
        g.add((uri, RDFS.comment, Literal(desc)))

    return g


def _datatype_property_adder(g: Graph):
    def add(uri, label, comment, domain, range_):
        g.add((uri, RDF.type, OWL.DatatypeProperty))
        g.add((uri, RDFS.label, Literal(label)))
        g.add((uri, RDFS.comment, Literal(comment)))
        if domain:
            g.add((uri, RDFS.domain, domain))
        if range_:
            g.add((uri, RDFS.range, range_))
    return add


def _object_property_adder(g: Graph):
    def add(uri, label, comment, domain, range_):
        g.add((uri, RDF.type, OWL.ObjectProperty))
        g.add((uri, RDFS.label, Literal(label)))
        g.add((uri, RDFS.comment, Literal(comment)))
        if domain:
            g.add((uri, RDFS.domain, domain))
        if range_:
            g.add((uri, RDFS.range, range_))
    return add
