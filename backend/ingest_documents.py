"""Ingest Markdown, text, and CSV documents into Neon pgvector.

Usage:
    python -m backend.ingest_documents --path knowledge_base
    python -m backend.ingest_documents --path path/to/one.md
"""
import argparse
from pathlib import Path

from backend.rag import chunk_text, ingest_chunks, read_document

SUPPORTED = {".md", ".txt", ".csv"}


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into WeatherGPT RAG.")
    parser.add_argument("--path", default="knowledge_base", help="A file or directory to ingest.")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=180)
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"Path does not exist: {target}")

    files = [target] if target.is_file() else sorted(
        path for path in target.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED
    )
    total = 0
    for path in files:
        if path.suffix.lower() not in SUPPORTED:
            print(f"Skipping unsupported file: {path}")
            continue
        text = read_document(path)
        chunks = chunk_text(text, args.chunk_size, args.overlap)
        resolved = path.resolve()
        try:
            source_name = resolved.relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            source_name = path.name
        count = ingest_chunks(
            source=source_name,
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            chunks=chunks,
        )
        total += count
        print(f"Ingested {count} chunks: {path}")
    print(f"Done. Upserted {total} chunks from {len(files)} file(s).")


if __name__ == "__main__":
    main()
