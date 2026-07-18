"""
Load enriched formulations into:
  - kalpanas (upsert)
  - yogas
  - yoga_indications (primary + secondary)
  - yoga_ingredients
  - references (per-yoga reference string → one ref row)
  - yoga_references
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_connection, upsert_concept

ROOT = Path(__file__).parent.parent
FORMS_FILE = ROOT / "data" / "enriched" / "formulations_enriched.json"

# Kalpana type → medium_class mapping (matches schema seed)
MEDIUM_MAP = {
    "Kwatha/Kashayam": "aqueous",
    "Asava/Arishta":   "fermented",
    "Ghrita":          "lipid",
    "Taila":           "lipid",
    "Churna":          "powder",
    "Vati/Gutika":     "tablet",
    "Avaleha/Leha":    "leha",
    "Bhasma/Pishti":   "mineral",
}

EXTERNAL_ONLY_NAMES = {
    "Jatyadi Taila", "Jatyadi Ghrita", "Eladi Taila",
    "Ksheerabala Taila", "Bala Taila",
}


def get_or_create_kalpana(cur, kalpana_name: str) -> str:
    medium = MEDIUM_MAP.get(kalpana_name, "aqueous")
    cur.execute(
        """
        INSERT INTO kalpanas (name, medium_class)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET medium_class = EXCLUDED.medium_class
        RETURNING kalpana_id
        """,
        (kalpana_name, medium),
    )
    return str(cur.fetchone()[0])


def get_or_create_indication_concept(cur, canonical_name: str) -> str:
    """Get concept_id for a disease/symptom concept, creating it if needed."""
    cur.execute(
        "SELECT concept_id FROM concepts WHERE canonical_name = %s",
        (canonical_name,),
    )
    row = cur.fetchone()
    if row:
        return str(row[0])
    return upsert_concept(cur, canonical_name, "roga")


def get_dravya_id_by_name(cur, name: str):
    """Fuzzy match a dravya by name (case-insensitive, partial)."""
    if not name:
        return None
    cur.execute(
        "SELECT dravya_id FROM dravyas WHERE lower(name) = lower(%s)",
        (name.strip(),),
    )
    row = cur.fetchone()
    if row:
        return str(row[0])
    # Try via terms table
    cur.execute(
        "SELECT d.dravya_id FROM dravyas d JOIN concepts c ON d.concept_id=c.concept_id "
        "JOIN terms t ON t.concept_id=c.concept_id WHERE lower(t.surface_form)=lower(%s)",
        (name.strip(),),
    )
    row = cur.fetchone()
    return str(row[0]) if row else None


def main():
    formulations = json.loads(FORMS_FILE.read_text(encoding="utf-8"))
    conn = get_connection()
    cur = conn.cursor()

    yoga_count = 0
    ind_count = 0
    ing_count = 0
    ref_count = 0

    for f in formulations:
        name = f["name"]
        kalpana_name = f.get("type", "Kwatha/Kashayam")
        kalpana_id = get_or_create_kalpana(cur, kalpana_name)

        external_only = name in EXTERNAL_ONLY_NAMES
        ambiguity = f.get("ambiguity_notes")

        cur.execute(
            """
            INSERT INTO yogas
                (name, kalpana_id, category, dosage, anupana, reference_text,
                 external_only, differentiation_note, ambiguity_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name, kalpana_id) DO UPDATE
              SET category=EXCLUDED.category, dosage=EXCLUDED.dosage,
                  anupana=EXCLUDED.anupana, reference_text=EXCLUDED.reference_text,
                  external_only=EXCLUDED.external_only,
                  differentiation_note=EXCLUDED.differentiation_note,
                  ambiguity_notes=EXCLUDED.ambiguity_notes
            RETURNING yoga_id
            """,
            (
                name,
                kalpana_id,
                f.get("category"),
                f.get("dosage"),
                f.get("anupana"),
                f.get("reference"),
                external_only,
                f.get("differentiation_note"),
                json.dumps(ambiguity) if ambiguity else None,
            ),
        )
        yoga_id = str(cur.fetchone()[0])
        yoga_count += 1

        # Reference row
        ref_text = f.get("reference") or ""
        if ref_text:
            cur.execute(
                """
                INSERT INTO references (work, excerpt_text)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                RETURNING ref_id
                """,
                (ref_text, ref_text),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT ref_id FROM references WHERE work = %s AND excerpt_text = %s", (ref_text, ref_text))
                row = cur.fetchone()
            if row:
                ref_id = str(row[0])
                cur.execute(
                    "INSERT INTO yoga_references (yoga_id, ref_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                    (yoga_id, ref_id),
                )
                ref_count += 1

        # Primary indications
        for ind in f.get("primary_indications") or []:
            cid = get_or_create_indication_concept(cur, ind)
            cur.execute(
                """
                INSERT INTO yoga_indications (yoga_id, concept_id, weight)
                VALUES (%s, %s, 'primary')
                ON CONFLICT DO NOTHING
                """,
                (yoga_id, cid),
            )
            ind_count += 1

        # Secondary indications
        for ind in f.get("secondary_indications") or []:
            cid = get_or_create_indication_concept(cur, ind)
            cur.execute(
                """
                INSERT INTO yoga_indications (yoga_id, concept_id, weight)
                VALUES (%s, %s, 'secondary')
                ON CONFLICT DO NOTHING
                """,
                (yoga_id, cid),
            )
            ind_count += 1

        # Ingredients
        for ing_name in f.get("main_ingredients") or []:
            dravya_id = get_dravya_id_by_name(cur, ing_name)
            sense_override = None
            # Apply sense overrides from ambiguity_notes
            if ambiguity and ing_name in ambiguity:
                sense_override = str(ambiguity[ing_name])
            cur.execute(
                """
                INSERT INTO yoga_ingredients (yoga_id, dravya_id, ingredient_name, sense_override)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (yoga_id, dravya_id, ing_name, sense_override),
            )
            ing_count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(
        f"Loaded {yoga_count} yogas, {ind_count} indications, "
        f"{ing_count} ingredients, {ref_count} references"
    )


if __name__ == "__main__":
    main()
