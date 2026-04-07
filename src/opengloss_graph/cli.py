"""CLI for OpenGloss RDF/SKOS/OWL graph export."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(name="opengloss-graph", help="Convert OpenGloss v1.1 dictionary to RDF.")

# Default batch size for streaming N-Triples (records per flush).
_NT_BATCH = 500


def _resolve_token(token_path: Path) -> str | None:
    if token_path.exists():
        token = token_path.read_text().strip()
        typer.echo(f"Using HuggingFace token from {token_path}")
        return token
    typer.echo(f"Warning: no token found at {token_path}, trying without auth.", err=True)
    return None


def _load_dataset(repo: str, split: str, token: str | None, limit: int | None = None):
    """Load a HuggingFace dataset, using split slicing when limit is set."""
    from datasets import load_dataset

    if limit is not None:
        split = f"{split}[:{limit}]"
    typer.echo(f"Loading dataset {repo} (split={split})...")
    return load_dataset(repo, split=split, token=token)


# ── Compact JSON-LD (recommended) ──────────────────────────────────────

@app.command()
def compact(
    output: Path = typer.Option(
        Path("opengloss.jsonld"),
        "--output", "-o",
        help="Output JSON-LD file path.",
    ),
    repo: str = typer.Option(
        "mjbommar/opengloss-v1.1-dictionary",
        "--repo", "-r",
        help="HuggingFace dataset repo ID.",
    ),
    token_path: Path = typer.Option(
        Path.home() / ".cache" / "huggingface" / "token",
        "--token-path",
        help="Path to HuggingFace token file.",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit", "-n",
        help="Only convert the first N records (for testing). Uses split slicing to avoid loading the full dataset.",
    ),
    split: str = typer.Option(
        "train",
        "--split", "-s",
        help="Dataset split to load.",
    ),
) -> None:
    """Export as compact JSON-LD (preserves nested structure, ~same size as source)."""
    from .compact import write_compact_jsonld

    token = _resolve_token(token_path)
    ds = _load_dataset(repo, split, token, limit=limit)

    total = len(ds)
    typer.echo(f"Converting {total:,} records to compact JSON-LD...")

    with open(output, "w", encoding="utf-8") as f:
        count = write_compact_jsonld(
            ds,
            f,
            progress_fn=lambda n: typer.echo(f"  ... {n:,} / {total:,} records"),
        )

    size_mb = output.stat().st_size / (1024 * 1024)
    typer.echo(f"Wrote {count:,} records ({size_mb:.1f} MB) to {output}")
    typer.echo("Done.")


# ── Flat triples via rdflib (Turtle, N-Triples, RDF/XML) ──────────────

@app.command()
def triples(
    output: Path = typer.Option(
        Path("opengloss.nt"),
        "--output", "-o",
        help="Output file. Extension determines format: .nt (N-Triples, streamed), .ttl (Turtle, in-memory), .xml (RDF/XML, in-memory).",
    ),
    ontology_output: Path | None = typer.Option(
        None,
        "--ontology", "--ont",
        help="Also write the OWL ontology to this file.",
    ),
    repo: str = typer.Option(
        "mjbommar/opengloss-v1.1-dictionary",
        "--repo", "-r",
        help="HuggingFace dataset repo ID.",
    ),
    token_path: Path = typer.Option(
        Path.home() / ".cache" / "huggingface" / "token",
        "--token-path",
        help="Path to HuggingFace token file.",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit", "-n",
        help="Only convert the first N records. Uses split slicing to avoid loading the full dataset.",
    ),
    split: str = typer.Option(
        "train",
        "--split", "-s",
        help="Dataset split to load.",
    ),
) -> None:
    """Export as flat RDF triples via rdflib.

    N-Triples (.nt) streams in batches and can handle the full dataset.
    Turtle (.ttl) and RDF/XML (.xml) build an in-memory graph — use --limit
    to avoid running out of memory on the full 150K-record dataset.
    """
    from .convert import convert_record, new_graph
    from .ontology import build_ontology

    token = _resolve_token(token_path)
    ds = _load_dataset(repo, split, token, limit=limit)

    total = len(ds)
    fmt = _format_from_suffix(output.suffix)

    if fmt == "nt":
        # Stream N-Triples: process in batches, serialize and append.
        typer.echo(f"Streaming {total:,} records to N-Triples...")
        triple_count = 0
        with open(output, "wb") as f:
            g = new_graph()
            for i, record in enumerate(ds):
                convert_record(g, record)
                if (i + 1) % _NT_BATCH == 0 or (i + 1) == total:
                    batch_data = g.serialize(format="nt")
                    if isinstance(batch_data, str):
                        batch_data = batch_data.encode("utf-8")
                    f.write(batch_data)
                    triple_count += len(g)
                    g = new_graph()
                    if (i + 1) % 10_000 == 0:
                        typer.echo(f"  ... {i + 1:,} / {total:,} records ({triple_count:,} triples)")

        size_mb = output.stat().st_size / (1024 * 1024)
        typer.echo(f"Wrote {triple_count:,} triples ({size_mb:.1f} MB) to {output}")
    else:
        # In-memory graph for Turtle, RDF/XML, etc.
        if limit is None:
            typer.echo(
                f"Warning: {fmt} format builds an in-memory graph. "
                "For the full dataset (~116M triples) this will likely exceed available RAM. "
                "Use .nt for streaming, or add --limit.",
                err=True,
            )
        typer.echo(f"Converting {total:,} records to flat triples ({fmt})...")
        g = new_graph()
        for i, record in enumerate(ds):
            convert_record(g, record)
            if (i + 1) % 10_000 == 0:
                typer.echo(f"  ... {i + 1:,} / {total:,} records")

        typer.echo(f"Graph has {len(g):,} triples.")
        typer.echo(f"Serializing to {output} (format={fmt})...")
        g.serialize(destination=str(output), format=fmt)
        size_mb = output.stat().st_size / (1024 * 1024)
        typer.echo(f"Wrote {size_mb:.1f} MB to {output}")

    if ontology_output is not None:
        ont_g = build_ontology()
        ont_fmt = _format_from_suffix(ontology_output.suffix)
        ont_g.serialize(destination=str(ontology_output), format=ont_fmt)
        typer.echo(f"Wrote ontology to {ontology_output}")

    typer.echo("Done.")


# ── Ontology only ─────────────────────────────────────────────────────

@app.command()
def ontology(
    output: Path = typer.Option(
        Path("opengloss-ontology.ttl"),
        "--output", "-o",
        help="Output file for the OWL ontology.",
    ),
) -> None:
    """Export only the OpenGloss OWL ontology (no data)."""
    from .ontology import build_ontology

    g = build_ontology()
    fmt = _format_from_suffix(output.suffix)
    g.serialize(destination=str(output), format=fmt)
    typer.echo(f"Wrote ontology ({len(g)} triples) to {output}")


# ── Context only ──────────────────────────────────────────────────────

@app.command()
def context(
    output: Path = typer.Option(
        Path("opengloss-context.jsonld"),
        "--output", "-o",
        help="Output file for the standalone JSON-LD context.",
    ),
) -> None:
    """Export only the JSON-LD @context (no data)."""
    import json

    from .context import JSONLD_CONTEXT

    with open(output, "w", encoding="utf-8") as f:
        json.dump({"@context": JSONLD_CONTEXT}, f, indent=2, ensure_ascii=False)
    typer.echo(f"Wrote JSON-LD context to {output}")


def _format_from_suffix(suffix: str) -> str:
    return {
        ".ttl": "turtle",
        ".turtle": "turtle",
        ".jsonld": "json-ld",
        ".json": "json-ld",
        ".nt": "nt",
        ".ntriples": "nt",
        ".xml": "xml",
        ".rdf": "xml",
        ".trig": "trig",
        ".nq": "nquads",
    }.get(suffix.lower(), "turtle")


if __name__ == "__main__":
    app()
