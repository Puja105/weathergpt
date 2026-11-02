"""Create the pgvector extension and WeatherGPT RAG table in Neon."""
from pathlib import Path
from backend.database import get_connection


def setup():
    sql = (Path(__file__).resolve().parents[1] / "sql" / "001_rag.sql").read_text(encoding="utf-8")
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        connection.commit()
        print("RAG database is ready (vector extension + weather_documents table).")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    setup()
