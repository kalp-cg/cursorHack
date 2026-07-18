"""
Evidence Pack Builder: assembles the full evidence context for the
top-N ranked yogas. This pack is the ONLY context given to the Explainer.
"""
from __future__ import annotations
from models.schemas import (
    EvidencePack, PropertyCard, ReferenceCard,
    RecommendedFormulation, SafetyViolation,
)


def _build_property_card(ingredients: list[dict]) -> PropertyCard | None:
    """Aggregate herb properties across ingredients. Returns None if all sparse."""
    rasas, gunas, viryas, vipakas, prabhavs, pacify, aggravate = [], [], [], [], [], [], []
    for ing in ingredients:
        if ing.get("rasa"):
            rasas.extend(ing["rasa"])
        if ing.get("guna"):
            gunas.extend(ing["guna"])
        if ing.get("virya"):
            viryas.append(ing["virya"])
        if ing.get("vipaka"):
            vipakas.append(ing["vipaka"])

    if not any([rasas, gunas, viryas, vipakas]):
        return PropertyCard(coverage_note="Pharmacological properties not available in corpus.")

    def dedup(lst):
        return list(dict.fromkeys(lst)) if lst else None

    return PropertyCard(
        rasa=dedup(rasas),
        guna=dedup(gunas),
        virya=viryas[0] if viryas else None,
        vipaka=vipakas[0] if vipakas else None,
        prabhav=dedup(prabhavs) or None,
        pacify=dedup(pacify) or None,
        aggravate=dedup(aggravate) or None,
    )


def build_evidence_pack(
    yoga_data: dict,
    ranked_result: RecommendedFormulation,
) -> EvidencePack:
    """Build an EvidencePack from raw yoga data + ranked result."""
    ingredients = yoga_data.get("ingredients") or []
    ingredient_names = [i.get("name", "") for i in ingredients]

    prop_card = _build_property_card(ingredients)

    refs = [
        ReferenceCard(
            ref_id=r.get("ref_id", ""),
            work=r.get("work", ""),
            sthana=r.get("sthana"),
            chapter=r.get("chapter"),
            verse_id=r.get("verse_id"),
            excerpt_text=r.get("excerpt_text"),
        )
        for r in (yoga_data.get("references") or [])
    ]

    return EvidencePack(
        yoga_id=ranked_result.yoga_id,
        yoga_name=ranked_result.yoga_name,
        kalpana=ranked_result.kalpana,
        medium_class=yoga_data.get("medium_class"),
        primary_indications=ranked_result.primary_indications,
        secondary_indications=ranked_result.secondary_indications,
        ingredients=ingredient_names,
        references=refs,
        properties=prop_card,
        rank_features=ranked_result.rank_features,
        safety_violations=ranked_result.safety_violations,
        differentiation_note=yoga_data.get("differentiation_note"),
        ambiguity_notes=yoga_data.get("ambiguity_notes"),
        score=ranked_result.score,
    )


def build_compare_packs(
    yoga_a_data: dict,
    yoga_b_data: dict,
    ranked_results: list[RecommendedFormulation],
) -> tuple[EvidencePack, EvidencePack]:
    """Build evidence packs for comparison of two yogas."""
    result_map = {r.yoga_id: r for r in ranked_results}

    def get_result(yoga_id: str) -> RecommendedFormulation:
        if yoga_id in result_map:
            return result_map[yoga_id]
        # Fallback: create a minimal result
        return RecommendedFormulation(
            rank=0, yoga_id=yoga_id,
            yoga_name=yoga_a_data.get("yoga_name", "Unknown"),
            score=0.0,
            rank_features=__import__("models.schemas", fromlist=["RankFeatures"]).RankFeatures(),
        )

    pack_a = build_evidence_pack(yoga_a_data, get_result(yoga_a_data["yoga_id"]))
    pack_b = build_evidence_pack(yoga_b_data, get_result(yoga_b_data["yoga_id"]))
    return pack_a, pack_b
