"""RDF namespace definitions for OpenGloss graph."""

from rdflib import Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

# Standard W3C / community vocabularies
ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/3.0/lexinfo#")
VARTRANS = Namespace("http://www.w3.org/ns/lemon/vartrans#")
FRAC = Namespace("http://www.w3.org/ns/lemon/frac#")
LIME = Namespace("http://www.w3.org/ns/lemon/lime#")
WN = Namespace("https://globalwordnet.github.io/schemas/wn#")

# OpenGloss custom namespace
OG = Namespace("https://opengloss.org/ontology#")
OGR = Namespace("https://opengloss.org/resource/")

# All namespace bindings for graph serialization
NS_BINDINGS: dict[str, Namespace] = {
    "og": OG,
    "ogr": OGR,
    "ontolex": ONTOLEX,
    "lexinfo": LEXINFO,
    "vartrans": VARTRANS,
    "frac": FRAC,
    "lime": LIME,
    "wn": WN,
    "skos": SKOS,
    "dcterms": DCTERMS,
    "owl": OWL,
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
}

# Mapping from OpenGloss POS strings to lexinfo URIs
POS_MAP: dict[str, str] = {
    "noun": str(LEXINFO.noun),
    "verb": str(LEXINFO.verb),
    "adjective": str(LEXINFO.adjective),
    "adverb": str(LEXINFO.adverb),
    "preposition": str(LEXINFO.preposition),
    "conjunction": str(LEXINFO.conjunction),
    "pronoun": str(LEXINFO.pronoun),
    "interjection": str(LEXINFO.interjection),
    "determiner": str(LEXINFO.determiner),
    "particle": str(LEXINFO.particle),
}

# Mapping from OpenGloss edge relationship_type to RDF predicates
EDGE_TYPE_MAP: dict[str, str] = {
    "synonym": str(WN.synonym),
    "antonym": str(WN.antonym),
    "hypernym": str(WN.hypernym),
    "hyponym": str(WN.hyponym),
    "collocation": str(OG.collocation),
    "derivation_noun": str(OG.derivationNoun),
    "derivation_verb": str(OG.derivationVerb),
    "derivation_adjective": str(OG.derivationAdjective),
    "derivation_adverb": str(OG.derivationAdverb),
    "inflection": str(OG.inflection),
    "etymology_parent": str(OG.etymologyParent),
    "cognate": str(OG.cognate),
}

# Mapping from inflection field names to lexinfo properties
INFLECTION_MAP: dict[str, str] = {
    "plural": str(LEXINFO.plural),
    "past_tense": str(LEXINFO.pastTense),
    "past_participle": str(LEXINFO.pastParticiple),
    "present_participle": str(LEXINFO.presentParticiple),
    "third_person_singular": str(LEXINFO.thirdPersonSingular),
    "comparative": str(LEXINFO.comparative),
    "superlative": str(LEXINFO.superlative),
}
