"""
Candidate Retriever: fetch yogas linked to resolved concepts.
Primary path: structured SQL over yoga_indications.
"""
from __future__ import annotations
from models.schemas import ResolverOutput, ClinicalFrame


def retrieve_candidates(
    resolver_output: ResolverOutput,
    frame: ClinicalFrame,
    db_conn,
    top_k: int = 50,
) -> list[dict]:
    """
    Return yoga candidate dicts with indication weights.
    Each dict: {yoga_id, yoga_name, kalpana_name, medium_class, category,
                dosage, anupana, reference_text, external_only,
                differentiation_note, ambiguity_notes,
                primary_match_count, secondary_match_count,
                primary_concepts, secondary_concepts, references, ingredients}
    """
    # Collect concept_ids to query
    # Exclude comorbidity concepts from indication matching (they're for safety)
    comorb_canonicals = set()
    for c in frame.comorbidities:
        comorb_canonicals.add(c.lower())
        comorb_canonicals.add(c.strip().lower())

    indication_concept_ids = [
        rc.concept_id
        for rc in resolver_output.resolved_concepts
        if rc.concept_type in ("roga", "lakshana", "karma")
        and rc.canonical_name.lower() not in comorb_canonicals
    ]

    if not indication_concept_ids:
        return []

    cur = db_conn.cursor()

    # Main query: yogas with any matching indication, plus their indication data
    cur.execute(
        """
        SELECT
            y.yoga_id::text,
            y.name AS yoga_name,
            k.name AS kalpana_name,
            k.medium_class,
            y.category,
            y.dosage,
            y.anupana,
            y.reference_text,
            y.external_only,
            y.differentiation_note,
            y.ambiguity_notes,
            SUM(CASE WHEN yi.weight = 'primary' AND yi.concept_id = ANY(%s::uuid[]) THEN 1 ELSE 0 END) AS primary_match_count,
            SUM(CASE WHEN yi.weight = 'secondary' AND yi.concept_id = ANY(%s::uuid[]) THEN 1 ELSE 0 END) AS secondary_match_count,
            ARRAY_AGG(DISTINCT CASE WHEN yi.weight = 'primary' THEN c.canonical_name END) FILTER (WHERE yi.weight='primary') AS all_primary,
            ARRAY_AGG(DISTINCT CASE WHEN yi.weight = 'secondary' THEN c.canonical_name END) FILTER (WHERE yi.weight='secondary') AS all_secondary
        FROM yogas y
        JOIN kalpanas k ON y.kalpana_id = k.kalpana_id
        JOIN yoga_indications yi ON y.yoga_id = yi.yoga_id
        JOIN concepts c ON yi.concept_id = c.concept_id
        WHERE yi.concept_id = ANY(%s::uuid[])
        GROUP BY y.yoga_id, y.name, k.name, k.medium_class, y.category,
                 y.dosage, y.anupana, y.reference_text, y.external_only,
                 y.differentiation_note, y.ambiguity_notes
        ORDER BY primary_match_count DESC, secondary_match_count DESC
        LIMIT %s
        """,
        (indication_concept_ids, indication_concept_ids, indication_concept_ids, top_k),
    )
    rows = cur.fetchall()

    candidates = []
    for row in rows:
        yoga_id = row[0]

        # Fetch references for this yoga
        cur.execute(
            """
            SELECT r.ref_id::text, r.work, r.sthana, r.chapter, r.verse_id, r.excerpt_text
            FROM yoga_references yr
            JOIN "references" r ON yr.ref_id = r.ref_id
            WHERE yr.yoga_id = %s
            """,
            (yoga_id,),
        )
        refs = [
            {
                "ref_id": str(rr[0]),
                "work": rr[1],
                "sthana": rr[2],
                "chapter": rr[3],
                "verse_id": rr[4],
                "excerpt_text": rr[5],
            }
            for rr in cur.fetchall()
        ]

        # Fetch ingredients
        cur.execute(
            """
            SELECT ing.ingredient_name, ing.sense_override, d.botanical_name,
                   ps.rasa, ps.guna, ps.virya, ps.vipaka, ps.pacify, ps.aggravate
            FROM yoga_ingredients ing
            LEFT JOIN dravyas d ON ing.dravya_id = d.dravya_id
            LEFT JOIN property_sets ps ON d.dravya_id = ps.dravya_id
            WHERE ing.yoga_id = %s
            """,
            (yoga_id,),
        )
        ingredients = [
            {
                "name": r[0],
                "sense_override": r[1],
                "botanical_name": r[2],
                "rasa": r[3],
                "guna": r[4],
                "virya": r[5],
                "vipaka": r[6],
                "pacify": r[7] or [],
                "aggravate": r[8] or [],
            }
            for r in cur.fetchall()
        ]

        cand = {
                "yoga_id": yoga_id,
                "yoga_name": row[1],
                "kalpana_name": row[2],
                "medium_class": row[3],
                "category": row[4],
                "dosage": row[5],
                "anupana": row[6],
                "reference_text": row[7],
                "external_only": row[8],
                "differentiation_note": row[9],
                "ambiguity_notes": row[10],
                "primary_match_count": int(row[11] or 0),
                "secondary_match_count": int(row[12] or 0),
                "all_primary": [x for x in (row[13] or []) if x],
                "all_secondary": [x for x in (row[14] or []) if x],
                "references": refs,
                "ingredients": ingredients,
            }
        # Apply kalpana filter when requested
        if frame.kalpana_filter:
            kf = frame.kalpana_filter.lower()
            name = (cand.get("kalpana_name") or "").lower()
            if kf not in name:
                continue
        candidates.append(cand)

    cur.close()
    return candidates
