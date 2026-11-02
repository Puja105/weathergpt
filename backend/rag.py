"""OpenAI embeddings + Neon pgvector retrieval for WeatherGPT."""
import logging
import os
from pathlib import Path
from typing import Any

import requests
from fastapi import HTTPException

from backend.database import get_connection

logger = logging.getLogger(__name__)
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    """Split text into overlapping, paragraph-aware chunks."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            boundary = cleaned.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Create embeddings in one API request for a batch of texts."""
    if not texts:
        return []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Set OPENAI_API_KEY before generating document embeddings.",
        )

    try:
        response = requests.post(
            OPENAI_EMBEDDINGS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": EMBEDDING_MODEL, "input": texts},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        items = sorted(payload["data"], key=lambda item: item["index"])
        vectors = [item["embedding"] for item in items]
        if len(vectors) != len(texts):
            raise ValueError("Embedding response count did not match input count")
        return vectors
    except (requests.RequestException, KeyError, TypeError, ValueError) as error:
        logger.exception("Embedding request failed")
        raise HTTPException(
            status_code=502,
            detail="Could not generate embeddings. Check the OpenAI API key and model access.",
        ) from error


def ingest_chunks(source: str, title: str, chunks: list[str]) -> int:
    """Embed and upsert chunks for one source document."""
    if not chunks:
        return 0

    connection = None
    cursor = None
    inserted = 0
    try:
        connection = get_connection()
        cursor = connection.cursor()
        # Replace this source atomically so removed/shortened text does not leave stale chunks.
        cursor.execute("DELETE FROM weather_documents WHERE source = %s;", (source,))
        # Keep API batches small to avoid oversized requests.
        for batch_start in range(0, len(chunks), 64):
            batch = chunks[batch_start:batch_start + 64]
            vectors = create_embeddings(batch)
            for offset, (content, vector) in enumerate(zip(batch, vectors)):
                chunk_index = batch_start + offset
                vector_literal = "[" + ",".join(str(float(value)) for value in vector) + "]"
                cursor.execute(
                    """
                    INSERT INTO weather_documents
                        (source, title, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT (source, chunk_index)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW();
                    """,
                    (source, title, chunk_index, content, vector_literal),
                )
                inserted += 1
        connection.commit()
        return inserted
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def retrieve_documents(question: str, limit: int = 5) -> list[dict[str, Any]]:
    """Return the most semantically relevant document chunks."""
    query_vector = create_embeddings([question])[0]
    vector_literal = "[" + ",".join(str(float(value)) for value in query_vector) + "]"

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT title, source, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM weather_documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (vector_literal, vector_literal, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "title": row[0],
                "source": row[1],
                "content": row[2],
                "similarity": round(float(row[3]), 4) if row[3] is not None else None,
            }
            for row in rows
        ]
    except Exception as error:
        if connection is not None:
            connection.rollback()
        logger.exception("RAG document retrieval failed")
        # A missing RAG table should be actionable, not silently mistaken for no matches.
        raise HTTPException(
            status_code=503,
            detail="RAG storage is not ready. Run `python -m backend.setup_rag` and ingest documents.",
        ) from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def read_document(path: Path) -> str:
    """Read supported text documents. CSV rows are converted to searchable text."""
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".csv":
        import csv
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return "\n".join(
            "; ".join(f"{key}: {value}" for key, value in row.items() if value not in (None, ""))
            for row in rows
        )
    raise ValueError(f"Unsupported document type: {suffix}")
