
"""OpenRouter embeddings + Neon pgvector retrieval for WeatherGPT."""

import csv
import logging
import os
from pathlib import Path
from typing import Any

import requests
from fastapi import HTTPException

from backend.database import get_connection

logger = logging.getLogger(__name__)

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"

EMBEDDING_MODEL = os.getenv(
    "OPENROUTER_EMBEDDING_MODEL",
    "nvidia/nemotron-3.5-embed-1b:free",
)

EMBEDDING_DIMENSIONS = 1536


def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
) -> list[str]:
    """Split text into overlapping, paragraph-aware chunks."""

    cleaned = " ".join(text.split())

    if not cleaned:
        return []

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "chunk_size must be positive and overlap must be smaller than chunk_size"
        )

    chunks = []
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


def create_embeddings(
    texts: list[str],
    input_type: str,
) -> list[list[float]]:
    """Generate embeddings through OpenRouter."""

    if not texts:
        return []

    if input_type not in {"query", "passage"}:
        raise ValueError("input_type must be 'query' or 'passage'")

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is missing from the environment.",
        )

    try:
        response = requests.post(
            OPENROUTER_EMBEDDINGS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "WeatherGPT",
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": texts,
                "input_type": input_type,
                "dimensions": EMBEDDING_DIMENSIONS,
                "encoding_format": "float",
            },
            timeout=60,
        )

        response.raise_for_status()

        payload = response.json()

        items = sorted(
            payload["data"],
            key=lambda item: item["index"],
        )

        vectors = [
            item["embedding"]
            for item in items
        ]

        if len(vectors) != len(texts):
            raise ValueError(
                "Embedding response count did not match input count"
            )

        for vector in vectors:
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                    f"received {len(vector)}"
                )

        return vectors

    except requests.RequestException as error:
        logger.exception("OpenRouter embedding request failed")

        raise HTTPException(
            status_code=502,
            detail="OpenRouter embedding request failed. Check API access and model availability.",
        ) from error

    except (KeyError, TypeError, ValueError) as error:
        logger.exception("Invalid embedding response")

        raise HTTPException(
            status_code=502,
            detail="OpenRouter returned an invalid embedding response.",
        ) from error


def ingest_chunks(
    source: str,
    title: str,
    chunks: list[str],
) -> int:
    """Embed and upsert chunks for one source document."""

    if not chunks:
        return 0

    connection = None
    cursor = None
    inserted = 0

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Replace the document's old chunks atomically.
        cursor.execute(
            "DELETE FROM weather_documents WHERE source = %s;",
            (source,),
        )

        # Keep API batches small.
        for batch_start in range(0, len(chunks), 64):

            batch = chunks[batch_start:batch_start + 64]

            vectors = create_embeddings(
                batch,
                input_type="passage",
            )

            for offset, (content, vector) in enumerate(
                zip(batch, vectors)
            ):

                chunk_index = batch_start + offset

                vector_literal = (
                    "["
                    + ",".join(str(float(value)) for value in vector)
                    + "]"
                )

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
                    (
                        source,
                        title,
                        chunk_index,
                        content,
                        vector_literal,
                    ),
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


def retrieve_documents(
    question: str,
    limit: int = 5,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks, filtering weak matches and exact duplicates.

    RAG_MIN_SIMILARITY can tune the cosine-similarity cutoff for the project's
    embedding model. A conservative default prevents unrelated documents from
    being presented as evidence.
    """
    if min_similarity is None:
        min_similarity = float(os.getenv("RAG_MIN_SIMILARITY", "0.25"))

    query_vectors = create_embeddings(
        [question],
        input_type="query",
    )

    query_vector = query_vectors[0]

    vector_literal = (
        "["
        + ",".join(str(float(value)) for value in query_vector)
        + "]"
    )

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

        relevant_documents = []
        seen_content = set()

        for row in rows:
            similarity = float(row[3]) if row[3] is not None else None

            if similarity is None or similarity < min_similarity:
                continue

            normalized_content = " ".join(str(row[2]).lower().split())
            if normalized_content in seen_content:
                continue

            seen_content.add(normalized_content)
            relevant_documents.append({
                "title": row[0],
                "source": row[1],
                "content": row[2],
                "similarity": round(similarity, 4),
            })

        return relevant_documents

    except Exception as error:
        if connection is not None:
            connection.rollback()

        logger.exception("RAG document retrieval failed")

        raise HTTPException(
            status_code=503,
            detail=(
                "RAG storage is not ready. "
                "Run `python -m backend.setup_rag` and ingest documents."
            ),
        ) from error

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def read_document(path: Path) -> str:
    """Read Markdown, text, and CSV documents."""

    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    if suffix == ".csv":

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:

            rows = list(csv.DictReader(handle))

        return "\n".join(
            "; ".join(
                f"{key}: {value}"
                for key, value in row.items()
                if value not in (None, "")
            )
            for row in rows
        )

    raise ValueError(f"Unsupported document type: {suffix}")
