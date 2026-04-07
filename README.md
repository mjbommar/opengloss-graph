# OpenGloss Graph

RDF/SKOS/OWL export of the [OpenGloss](https://arxiv.org/abs/2511.18622) synthetic encyclopedic dictionary and semantic knowledge graph, using the W3C [Ontolex-Lemon](https://www.w3.org/2016/05/ontolex/) vocabulary.

This project converts the [OpenGloss v1.1 Dictionary](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-dictionary) (150,637 lexemes, 506K+ senses, 7.7M semantic edges) into standards-compliant Linked Data that can be consumed by any RDF toolchain, SPARQL engine, or JSON-LD processor.

## Download

The latest release is available as a compressed JSON-LD file from [GitHub Releases](https://github.com/mjbommar/opengloss-graph/releases):

| File | Size | Description |
|------|------|-------------|
| `opengloss.jsonld.gz` | ~500 MB | Full graph (150,637 entries). Decompress with `gzip -d`. |
| `opengloss-ontology.ttl` | ~8 KB | OWL ontology for custom `og:` properties |
| `opengloss-context.jsonld` | ~3 KB | Standalone JSON-LD `@context` for reuse |

No special libraries required — the JSON-LD file is standard JSON that any language can parse.

## Background

[OpenGloss](https://arxiv.org/abs/2511.18622) is a synthetic encyclopedic dictionary and semantic knowledge graph for English. I generated it using a multi-agent procedural pipeline with schema-validated LLM outputs in under one week for under $1,000. The dataset is licensed [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Key statistics:

- **150,637 lexemes** across 10 parts of speech
- **506K+ sense definitions** (3.58 senses/lexeme average)
- **7.7M semantic edges** (synonymy, antonymy, hypernymy, hyponymy, collocations, inflections, derivations, etymology)
- **1M+ usage examples**, **3M+ collocations**
- **60M words** of encyclopedic content (99.7% coverage)
- **Etymology trails** for 97.5% of entries with language, era, and source citations

### Related Resources

| Resource | Link |
|----------|------|
| Paper | [arXiv:2511.18622](https://arxiv.org/abs/2511.18622) |
| Dictionary (word-level) | [mjbommar/opengloss-v1.1-dictionary](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-dictionary) |
| Definitions (sense-level) | [mjbommar/opengloss-v1.1-definitions](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-definitions) |
| Contrastive examples | [mjbommar/opengloss-v1.1-contrastive-examples](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-contrastive-examples) |
| Encyclopedia variants | [mjbommar/opengloss-v1.1-encyclopedia-variants](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-encyclopedia-variants) |
| Query examples | [mjbommar/opengloss-v1.1-query-examples](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-query-examples) |
| OGBert embedding model | [mjbommar/ogbert-110m-sentence](https://huggingface.co/mjbommar/ogbert-110m-sentence) |
| Rust tools | [mjbommar/opengloss-rs](https://github.com/mjbommar/opengloss-rs) |
| Web explorer | [opengloss.com](https://opengloss.com/) |

## Vocabularies

The graph uses standard W3C and community vocabularies wherever possible, with a small custom ontology (`og:`) for properties specific to OpenGloss.

| Prefix | Namespace | Purpose |
|--------|-----------|---------|
| `ontolex:` | `http://www.w3.org/ns/lemon/ontolex#` | Lexical entries, senses, forms |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | Definitions, examples, broader/narrower |
| `lexinfo:` | `http://www.lexinfo.net/ontology/3.0/lexinfo#` | Parts of speech, morphological features |
| `vartrans:` | `http://www.w3.org/ns/lemon/vartrans#` | Derivational relations |
| `wn:` | `https://globalwordnet.github.io/schemas/wn#` | Synonym, antonym |
| `dcterms:` | `http://purl.org/dc/terms/` | Timestamps, language, subjects, sources |
| `rdfs:` | `http://www.w3.org/2000/01/rdf-schema#` | Labels, comments |
| `og:` | `https://opengloss.org/ontology#` | Custom properties (see below) |

### Custom Ontology (`og:`)

Properties not covered by standard vocabularies:

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `og:readingLevel` | LexicalEntry | xsd:string | Target reading level (K, 1-12, BS, PhD) |
| `og:isStopword` | LexicalEntry | xsd:boolean | Stopword classification |
| `og:stopwordReason` | LexicalEntry | xsd:string | Reason for classification |
| `og:processedAt` | LexicalEntry | xsd:dateTime | Processing timestamp |
| `og:encyclopediaEntry` | LexicalEntry | xsd:string | Encyclopedic prose description |
| `og:lexicalExplanation` | LexicalEntry | xsd:string | Prose explanation of lexical relationships |
| `og:wikiFrequency` | LexicalEntry | xsd:integer | Wikipedia occurrence count |
| `og:wikiFrequencyRank` | LexicalEntry | xsd:integer | Frequency rank (1 = most common) |
| `og:baseForm` | LexicalEntry | xsd:string | Morphological base form for a given POS |
| `og:senseIndex` | — | xsd:integer | Zero-based index of a sense within its POS entry |
| `og:era` | EtymologySegment | xsd:string | Historical time period |
| `og:etymologyOrder` | EtymologySegment | xsd:integer | Position in etymology chain (0 = earliest) |
| `og:cognate` | EtymologyTrail | xsd:string | Cognate word in another language |

Classes: `og:EtymologyTrail`, `og:EtymologySegment`, `og:LexicalRelation`

The full ontology is available as `opengloss-ontology.ttl` in the release assets.

## Field Coverage

All 52 source fields from the OpenGloss `OpenGlossWordRecord` schema are mapped. The 14 derived/aggregate fields (counts, flattened lists, markdown rendering) are omitted because they can be recomputed from the source fields.

<details>
<summary>Complete field mapping (click to expand)</summary>

| # | Source Field | RDF Mapping |
|---|-------------|-------------|
| 1 | `id` | URI identity (`ogr:entry/{id}`) |
| 2 | `word` | `rdfs:label` |
| 3 | `created_at` | `dcterms:created` |
| 4 | `updated_at` | `dcterms:modified` |
| 5 | `processed_at` | `og:processedAt` |
| 6 | `language` | `dcterms:language` |
| 7 | `reading_level` | `og:readingLevel` |
| 8 | `tags` | `dcterms:subject` |
| 9 | `is_stopword` | `og:isStopword` |
| 10 | `stopword_reason` | `og:stopwordReason` |
| 11 | `entries[].pos` | `lexinfo:partOfSpeech` |
| 12 | `entries[].senses[].sense_index` | `og:senseIndex` |
| 13 | `entries[].senses[].definition` | `skos:definition` |
| 14 | `entries[].senses[].synonyms` | `wn:synonym` |
| 15 | `entries[].senses[].antonyms` | `wn:antonym` |
| 16 | `entries[].senses[].hypernyms` | `skos:broader` |
| 17 | `entries[].senses[].hyponyms` | `skos:narrower` |
| 18 | `entries[].senses[].examples` | `skos:example` |
| 19 | `entries[].morphology.base_form` | `og:baseForm` |
| 20 | `entries[].morphology.inflections.plural` | `lexinfo:plural` |
| 21 | `entries[].morphology.inflections.past_tense` | `lexinfo:pastTense` |
| 22 | `entries[].morphology.inflections.past_participle` | `lexinfo:pastParticiple` |
| 23 | `entries[].morphology.inflections.present_participle` | `lexinfo:presentParticiple` |
| 24 | `entries[].morphology.inflections.third_person_singular` | `lexinfo:thirdPersonSingular` |
| 25 | `entries[].morphology.inflections.comparative` | `lexinfo:comparative` |
| 26 | `entries[].morphology.inflections.superlative` | `lexinfo:superlative` |
| 27 | `entries[].morphology.derivations.noun_forms` | `og:derivationNoun` |
| 28 | `entries[].morphology.derivations.verb_forms` | `og:derivationVerb` |
| 29 | `entries[].morphology.derivations.adjective_forms` | `og:derivationAdjective` |
| 30 | `entries[].morphology.derivations.adverb_forms` | `og:derivationAdverb` |
| 31 | `entries[].collocations` | `og:collocation` |
| 32 | `etymology_summary` | `skos:note` |
| 33 | `etymology_cognates` | `og:cognate` |
| 34 | `etymology_segments[].order` | `og:etymologyOrder` |
| 35 | `etymology_segments[].language` | `dcterms:language` |
| 36 | `etymology_segments[].headword` | `ontolex:writtenRep` |
| 37 | `etymology_segments[].gloss` | `skos:definition` |
| 38 | `etymology_segments[].era` | `og:era` |
| 39 | `etymology_segments[].notes` | `rdfs:comment` |
| 40 | `etymology_segments[].sources` | `dcterms:source` |
| 41 | `etymology_references` | `dcterms:references` |
| 42 | `encyclopedia_entry` | `og:encyclopediaEntry` |
| 43 | `lexical_explanation` | `og:lexicalExplanation` |
| 44 | `wiki_frequency` | `og:wikiFrequency` |
| 45 | `wiki_frequency_rank` | `og:wikiFrequencyRank` |
| 46 | `edges[].source_word` | compact: `og:sourceWord`, triples: `og:sourceEntry` |
| 47 | `edges[].target_word` | compact: `og:targetWord`, triples: `og:targetEntry` |
| 48 | `edges[].relationship_type` | compact: `og:relationshipType`, triples: `og:relationCategory` |
| 49 | `edges[].source_pos` | `og:sourcePOS` |
| 50 | `edges[].target_pos` | `og:targetPOS` |
| 51 | `edges[].sense_index` | `og:senseIndex` |
| 52 | `edges[].metadata` | `og:edgeMetadata` |

</details>

## Output Formats

### Compact JSON-LD (recommended)

The primary output preserves the original nested JSON structure with a `@context` header that maps field names to RDF URIs. This keeps the file compact (~3.5 GB uncompressed, ~500 MB gzipped) while being fully valid JSON-LD that any RDF processor can interpret.

```bash
# Download and decompress
curl -L https://github.com/mjbommar/opengloss-graph/releases/download/v1.0.0/opengloss.jsonld.gz | gzip -d > opengloss.jsonld

# Load in Python (no special libraries needed)
import json
with open("opengloss.jsonld") as f:
    data = json.load(f)

for entry in data["@graph"]:
    print(entry["word"], entry["@id"])
```

### Flat RDF Triples (Turtle, N-Triples, RDF/XML)

For use cases requiring materialized triples (SPARQL stores, graph databases), the `triples` command flattens the data into individual RDF statements.

N-Triples (`.nt`) streams in batches and can handle the full dataset (~116M triples). Turtle (`.ttl`) and RDF/XML (`.xml`) build an in-memory graph — use `--limit` for those formats.

```bash
# Full dataset as streamed N-Triples
uv run opengloss-graph triples -o opengloss.nt

# Small Turtle subset for testing
uv run opengloss-graph triples --limit 1000 -o sample.ttl

# With ontology
uv run opengloss-graph triples --limit 1000 -o sample.ttl --ontology ontology.ttl
```

Note: the compact and triples paths use slightly different property names for edge fields (`og:sourceWord` vs `og:sourceEntry`). Both paths produce typed nodes for `og:LexicalRelation`, `og:EtymologyTrail`, and `og:EtymologySegment`.

## Building from Source

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/). A HuggingFace token is needed to download the source dataset.

```bash
git clone https://github.com/mjbommar/opengloss-graph.git
cd opengloss-graph
uv sync

# Compact JSON-LD (recommended)
uv run opengloss-graph compact -o opengloss.jsonld

# Test with a small subset
uv run opengloss-graph compact -o test.jsonld --limit 100

# Flat triples — N-Triples streams and can handle the full dataset
uv run opengloss-graph triples -o opengloss.nt

# Turtle requires in-memory graph — use --limit
uv run opengloss-graph triples -o sample.ttl --limit 1000

# Export just the ontology or context
uv run opengloss-graph ontology -o opengloss-ontology.ttl
uv run opengloss-graph context -o opengloss-context.jsonld
```

The HuggingFace token is read from `~/.cache/huggingface/token` by default. Override with `--token-path`.

## Example Entry

A single entry in the compact JSON-LD output (abbreviated):

```json
{
  "@id": "ogr:entry/complect",
  "@type": "ontolex:LexicalEntry",
  "word": "complect",
  "canonical_form": {"@type": "ontolex:Form", "written_rep": "complect"},
  "language": "en",
  "reading_level": "PhD",
  "tags": ["domain:language"],
  "is_stopword": false,
  "entries": [
    {
      "pos": "lexinfo:verb",
      "senses": [
        {
          "@type": "ontolex:LexicalSense",
          "sense_index": 0,
          "definition": "To join or combine elements so as to form a single complex or unified whole.",
          "synonyms": ["ogr:entry/unite", "ogr:entry/join", "ogr:entry/merge"],
          "antonyms": ["ogr:entry/separate", "ogr:entry/detach"],
          "hypernyms": ["ogr:entry/transitive_verb"],
          "hyponyms": ["ogr:entry/intertwine", "ogr:entry/weave"],
          "examples": ["The study complected sensor data from multiple sources."]
        }
      ],
      "morphology": {
        "base_form": "complect",
        "inflections": {
          "past_tense": ["complected"],
          "present_participle": ["complecting"],
          "third_person_singular": ["complects"]
        },
        "derivations": {
          "noun_forms": ["ogr:entry/complection"],
          "adjective_forms": ["ogr:entry/complective"]
        }
      },
      "collocations": ["data", "variables", "concepts"]
    }
  ],
  "etymology": {
    "@type": "og:EtymologyTrail",
    "@id": "ogr:etymology/complect",
    "etymology_summary": "From Latin complectere 'to entwine'...",
    "etymology_segments": [
      {"@type": "og:EtymologySegment", "order": 0, "language": "English", "headword": "complect", "era": "15th century"},
      {"@type": "og:EtymologySegment", "order": 1, "language": "Latin", "headword": "complecti", "era": "Classical Latin"}
    ]
  },
  "encyclopedia_entry": "**complect** is a verb meaning to entwine or interweave...",
  "wiki_frequency": 5,
  "wiki_frequency_rank": 134254,
  "edges": [
    {
      "@type": "og:LexicalRelation",
      "source_word": "ogr:entry/complect",
      "target_word": "ogr:entry/unite",
      "relationship_type": "wn:synonym",
      "source_pos": "verb",
      "sense_index": 0
    }
  ]
}
```

## Citation

If you use this in your research, please cite:

```bibtex
@misc{bommarito2025opengloss,
  title={OpenGloss: A Synthetic Encyclopedic Dictionary and Semantic Knowledge Graph},
  author={Michael J. Bommarito II},
  year={2025},
  eprint={2511.18622},
  archivePrefix={arXiv},
  primaryClass={cs.CL}
}
```

## License

This repository uses two licenses:

- **Code** (source files in `src/`, `pyproject.toml`): [MIT](LICENSE) 
- **Data** (release assets: `opengloss.jsonld.gz`, `opengloss-ontology.ttl`, `opengloss-context.jsonld`): [CC-BY 4.0](LICENSE-DATA), consistent with the upstream [OpenGloss dataset](https://huggingface.co/datasets/mjbommar/opengloss-v1.1-dictionary)
