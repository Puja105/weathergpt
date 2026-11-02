"""Manual Neon connectivity check: run with `python -m backend.test_database`."""
from backend.database import get_connection


def main():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            print("PostgreSQL connection successful:", cursor.fetchone()[0])
    finally:
        connection.close()


if __name__ == "__main__":
    main()
