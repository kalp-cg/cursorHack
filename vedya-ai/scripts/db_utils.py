"""Shared database utilities for load scripts."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values


def get_connection():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://vedya:vedyapass@localhost:5432/vedyaai",
    )
    conn = psycopg2.connect(url)
    # Neon pooler can start with an empty search_path
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public")
    conn.commit()
    return conn


def upsert_concept(cur, canonical_name: str, type_: str) -> str:
    """Insert or return existing concept_id (UUID string)."""
    cur.execute(
        """
        INSERT INTO concepts (canonical_name, type)
        VALUES (%s, %s)
        ON CONFLICT (canonical_name) DO UPDATE SET type = EXCLUDED.type
        RETURNING concept_id
        """,
        (canonical_name, type_),
    )
    return str(cur.fetchone()[0])


def upsert_term(cur, surface_form: str, concept_id: str, language: str = "en", source: str = "manual") -> None:
    cur.execute(
        """
        INSERT INTO terms (surface_form, language, concept_id, source)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (surface_form, language) DO UPDATE SET concept_id = EXCLUDED.concept_id
        """,
        (surface_form, language, concept_id, source),
    )
