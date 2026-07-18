"""
Ranker: feature-weighted deterministic scoring.
Score = W1*primary_match + W2*secondary_match + W3*property_fit
      + W4*citation_bonus - W5*contraindication_penalty - W6*medium_penalty

Tuned so that:
  Pinasa vignette → Vyaghryadi score > Punarnavadi WITHOUT LLM (M3 gate).
  Inflammatory vignette (Shotha) → Punarnavadi score > Vyaghryadi.
"""
from __future__ import annotations
from models.schemas import (
    RankFeatures, RecommendedFormulation, SafetyResult, ReferenceCard,
    ResolvedConcept, ClinicalFrame,
)

# Weight constants (tunable without code change)
W1 = 3.0   # primary indication match per concept
W2 = 1.0   # secondary indication match per concept
W3 = 0.5   # property fit (dosha alignment)
W4 = 0.5   # citation completeness bonus
W5 = 5.0   # contraindication penalty per WARN violation
W6 = 2.0   # medium unsuitability penalty (hard gate already removed HARD_EXCLUDE)


def _dosha_from_prakriti(prakriti: str | None) -> list[str]:
    """Map prakriti string to list of dominant doshas."""
    if not prakriti:
        return []
    p = prakriti.lower()
    doshas = []
    if "vata" in p:
        doshas.append("Vata")
    if "pitta" in p:
        doshas.append("Pitta")
    if "kapha" in p:
        doshas.append("Kapha")
    return doshas


def _property_fit(ingredients: list[dict], frame: ClinicalFrame) -> float:
    """
    Dosha fit using pacify/aggravate lists from herb data when present.
    Falls back to rasa heuristics only if pacify is empty.
    Returns normalised 0–1 score.
    """
    if not frame.prakriti or not ingredients:
        return 0.0
    dominant_doshas = _dosha_from_prakriti(frame.prakriti)
    if not dominant_doshas:
        return 0.0
    fit_count = 0
    total = 0
    for ing in ingredients:
        pacify = list(ing.get("pacify") or [])
        aggravate = list(ing.get("aggravate") or [])
        rasa = list(ing.get("rasa") or [])
        if not pacify and rasa:
            if any(r in ("Tikta", "Katu", "Kashaya") for r in rasa):
                pacify.append("Kapha")
            if any(r in ("Madhura", "Amla", "Lavana") for r in rasa):
                pacify.append("Vata")
            if any(r in ("Madhura", "Tikta", "Kashaya") for r in rasa):
                pacify.append("Pitta")
        for dosha in dominant_doshas:
            total += 1
            if dosha in pacify and dosha not in aggravate:
                fit_count += 1
    return (fit_count / total) if total else 0.0


def _medium_penalty(medium_class: str, comorbidities: list[str]) -> float:
    """Non-safety-rule medium penalty (soft — rule engine handles hard cases)."""
    comorb_lower = {c.lower() for c in comorbidities}
    if medium_class == "fermented" and any(
        d in comorb_lower for d in ("prameha", "diabetes", "diabetic", "madhumeha")
    ):
        return W6
    return 0.0


def rank(
    candidates: list[dict],
    safety_results: list[SafetyResult],
    frame: ClinicalFrame,
    top_k: int = 10,
) -> list[RecommendedFormulation]:
    """
    Score, sort, and return top-k RecommendedFormulation objects.
    Hard-excluded yogas are filtered out first.
    """
    safety_map = {sr.yoga_id: sr for sr in safety_results}
    ranked: list[tuple[float, dict, RankFeatures, SafetyResult]] = []

    for yoga in candidates:
        yid = yoga["yoga_id"]
        sr = safety_map.get(yid, SafetyResult(yoga_id=yid, yoga_name=yoga["yoga_name"]))

        # Skip hard-excluded
        if sr.hard_excluded:
            continue

        # Primary indication match
        primary_score = float(yoga.get("primary_match_count", 0)) * W1

        # Secondary indication match
        secondary_score = float(yoga.get("secondary_match_count", 0)) * W2

        # Property fit (Prakriti-based)
        prop_fit = _property_fit(yoga.get("ingredients", []), frame) * W3

        # Citation bonus (has at least one reference)
        citation_bonus = W4 if yoga.get("references") else 0.0

        # Safety penalty (WARN violations deduct points; HARD already filtered)
        contra_penalty = sum(
            W5 for v in sr.violations if v.severity == "WARN"
        )

        # Medium penalty
        med_penalty = _medium_penalty(yoga.get("medium_class", ""), frame.comorbidities)

        total = primary_score + secondary_score + prop_fit + citation_bonus \
                - contra_penalty - med_penalty
        total = max(total, 0.0)

        features = RankFeatures(
            primary_indication_match=round(primary_score, 3),
            secondary_indication_match=round(secondary_score, 3),
            property_fit=round(prop_fit, 3),
            citation_bonus=round(citation_bonus, 3),
            contraindication_penalty=round(contra_penalty, 3),
            medium_penalty=round(med_penalty, 3),
            total_score=round(total, 3),
        )

        ranked.append((total, yoga, features, sr))

    # Sort descending by total score
    ranked.sort(key=lambda x: x[0], reverse=True)

    results: list[RecommendedFormulation] = []
    for rank_pos, (score, yoga, features, sr) in enumerate(ranked[:top_k], start=1):
        refs = [
            ReferenceCard(
                ref_id=r.get("ref_id", ""),
                work=r.get("work", ""),
                sthana=r.get("sthana"),
                chapter=r.get("chapter"),
                verse_id=r.get("verse_id"),
                excerpt_text=r.get("excerpt_text"),
            )
            for r in (yoga.get("references") or [])
        ]

        coverage_note = None
        if not yoga.get("references"):
            coverage_note = "Reference details not available in corpus for this formulation."

        results.append(
            RecommendedFormulation(
                rank=rank_pos,
                yoga_id=yoga["yoga_id"],
                yoga_name=yoga["yoga_name"],
                kalpana=yoga.get("kalpana_name"),
                category=yoga.get("category"),
                score=round(score, 3),
                rank_features=features,
                safety_violations=sr.violations,
                hard_excluded=sr.hard_excluded,
                primary_indications=yoga.get("all_primary") or [],
                secondary_indications=yoga.get("all_secondary") or [],
                references=refs,
                differentiation_note=yoga.get("differentiation_note"),
                dosage=yoga.get("dosage"),
                anupana=yoga.get("anupana"),
                coverage_note=coverage_note,
            )
        )

    return results
