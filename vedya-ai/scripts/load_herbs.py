"""
Load herbs from data/raw/herbs_amidha.json into:
  - concepts (type='dravya')
  - terms (canonical name + all sanskrit_synonyms)
  - dravyas
  - property_sets
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_connection, upsert_concept, upsert_term

ROOT = Path(__file__).parent.parent
HERBS_FILE = ROOT / "data" / "raw" / "herbs_amidha.json"


def main():
    herbs = json.loads(HERBS_FILE.read_text(encoding="utf-8"))
    conn = get_connection()
    cur = conn.cursor()

    loaded = 0
    for herb in herbs:
        name = herb["name"]

        # Concept
        concept_id = upsert_concept(cur, name, "dravya")

        # Terms: canonical name + all synonyms
        upsert_term(cur, name, concept_id, "sa", "herbs_amidha")
        upsert_term(cur, name.lower(), concept_id, "en", "herbs_amidha")
        if herb.get("english_name"):
            upsert_term(cur, herb["english_name"], concept_id, "en", "herbs_amidha")
            upsert_term(cur, herb["english_name"].lower(), concept_id, "en", "herbs_amidha")
        for syn in herb.get("sanskrit_synonyms") or []:
            upsert_term(cur, syn, concept_id, "sa", "herbs_amidha")
            upsert_term(cur, syn.lower(), concept_id, "en", "herbs_amidha")

        # Dravya row
        cur.execute(
            """
            INSERT INTO dravyas
                (concept_id, name, botanical_name, family, english_name, part_used, image_url, external_link, preview_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING dravya_id
            """,
            (
                concept_id,
                name,
                herb.get("botanical_name"),
                herb.get("family"),
                herb.get("english_name"),
                herb.get("part_used") or [],
                herb.get("image") or None,
                herb.get("link") or None,
                herb.get("preview") or None,
            ),
        )
        row = cur.fetchone()
        if row is None:
            # Already exists — fetch the id
            cur.execute("SELECT dravya_id FROM dravyas WHERE concept_id = %s", (concept_id,))
            row = cur.fetchone()
        dravya_id = str(row[0])

        # Property set
        rasa = herb.get("rasa") or []
        guna = herb.get("guna") or []
        virya = herb.get("virya") or None
        vipaka = herb.get("vipaka") or None
        prabhav = herb.get("prabhav") or []
        pacify = herb.get("pacify") or []
        aggravate = herb.get("aggravate") or []
        tridosha = bool(herb.get("tridosha", False))

        cur.execute(
            """
            INSERT INTO property_sets (dravya_id, rasa, guna, virya, vipaka, prabhav, pacify, aggravate, tridosha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dravya_id) DO UPDATE
              SET rasa=EXCLUDED.rasa, guna=EXCLUDED.guna, virya=EXCLUDED.virya,
                  vipaka=EXCLUDED.vipaka, prabhav=EXCLUDED.prabhav,
                  pacify=EXCLUDED.pacify, aggravate=EXCLUDED.aggravate,
                  tridosha=EXCLUDED.tridosha
            """,
            (dravya_id, rasa, guna, virya, vipaka, prabhav, pacify, aggravate, tridosha),
        )
        loaded += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {loaded} herbs (dravyas + property_sets)")


if __name__ == "__main__":
    main()
