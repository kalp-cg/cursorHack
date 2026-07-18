"""
Explainer: citation-bound explanations from the Evidence Pack.
Supports EN / HI / GU template explanations; LLM may narrate in the same locale.
"""
from __future__ import annotations
import json
import os
from models.schemas import (
    EvidencePack, Explanation, ExplanationClaim,
    CompareResult,
)

LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"

_LOCALE_NAMES = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}


def _norm_locale(locale: str | None) -> str:
    loc = (locale or "en").lower().strip()
    return loc if loc in {"en", "hi", "gu"} else "en"


def _recommend_system(locale: str) -> str:
    lang = _LOCALE_NAMES.get(locale, "English")
    return f"""You are a classical Ayurvedic clinical educator.
Given an Evidence Pack for a formulation, explain WHY it is recommended for the patient's conditions.
Your explanation must:
1. Be grounded ONLY in the evidence pack provided.
2. Reference citations using their ref_id (format: [ref_id]).
3. Output ONLY valid JSON: {{"summary": "...", "claims": [{{"text": "...", "ref_ids": ["..."]}}]}}
4. Never invent new formulations, ingredients, or references.
5. If evidence is insufficient, say so honestly.
6. Write the summary and claim texts in {lang}. Keep classical Sanskrit yoga names unchanged."""


def _compare_system(locale: str) -> str:
    lang = _LOCALE_NAMES.get(locale, "English")
    return f"""You are a classical Ayurvedic clinical educator.
Compare two formulations (A and B) for a patient vignette and explain which is more appropriate.
Ground every claim in the evidence packs. Output ONLY valid JSON:
{{"summary": "...", "claims": [{{"text": "...", "ref_ids": ["..."]}}], "winner": "A or B", "winner_reason": "one sentence"}}
Never invent references.
Write summary, claims, and winner_reason in {lang}. Keep classical Sanskrit yoga names unchanged."""


def _template_explanation(pack: EvidencePack, locale: str = "en") -> Explanation:
    """Deterministic template explanation — used when LLM is off or fails."""
    ref_ids = [r.ref_id for r in pack.references if r.ref_id]
    primary_str = ", ".join(pack.primary_indications[:3]) if pack.primary_indications else ""
    secondary_str = ", ".join(pack.secondary_indications[:3]) if pack.secondary_indications else ""
    ingredient_str = ", ".join(pack.ingredients[:4]) if pack.ingredients else ""
    work = pack.references[0].work if pack.references else ""
    kalpana = pack.kalpana or ""

    if locale == "hi":
        primary_str = primary_str or "उल्लिखित स्थितियाँ"
        ingredient_str = ingredient_str or "इसके अवयव द्रव्य"
        work = work or "शास्त्रीय ग्रंथ"
        kalpana = kalpana or "कषाय"
        claims = [
            ExplanationClaim(
                text=f"{pack.yoga_name} मुख्य रूप से {primary_str} में इंगित है।",
                ref_ids=ref_ids[:1],
            )
        ]
        if secondary_str:
            claims.append(
                ExplanationClaim(
                    text=f"इसके घटक ({ingredient_str}) {secondary_str} के लिए अतिरिक्त आवरण देते हैं।",
                    ref_ids=ref_ids[:1],
                )
            )
        if pack.safety_violations:
            claims.append(
                ExplanationClaim(
                    text="सुरक्षा ध्यान दें: " + "; ".join(v.message[:80] for v in pack.safety_violations),
                    ref_ids=[],
                )
            )
        if pack.differentiation_note:
            claims.append(ExplanationClaim(text=pack.differentiation_note, ref_ids=ref_ids[:1]))
        summary = (
            f"{pack.yoga_name} ({kalpana}) एक शास्त्रीय योग है, "
            f"जो {primary_str} के लिए उपयुक्त है; संदर्भ: {work}।"
        )
    elif locale == "gu":
        primary_str = primary_str or "ઉલ્લેખિત સ્થિતિઓ"
        ingredient_str = ingredient_str or "તેના ઘટક દ્રવ્યો"
        work = work or "શાસ્ત્રીય ગ્રંથ"
        kalpana = kalpana or "કષાય"
        claims = [
            ExplanationClaim(
                text=f"{pack.yoga_name} મુખ્યત્વે {primary_str} માટે સૂચવાય છે.",
                ref_ids=ref_ids[:1],
            )
        ]
        if secondary_str:
            claims.append(
                ExplanationClaim(
                    text=f"તેના ઘટકો ({ingredient_str}) {secondary_str} માટે વધારાનું આવરણ આપે છે.",
                    ref_ids=ref_ids[:1],
                )
            )
        if pack.safety_violations:
            claims.append(
                ExplanationClaim(
                    text="સુરક્ષા નોંધ: " + "; ".join(v.message[:80] for v in pack.safety_violations),
                    ref_ids=[],
                )
            )
        if pack.differentiation_note:
            claims.append(ExplanationClaim(text=pack.differentiation_note, ref_ids=ref_ids[:1]))
        summary = (
            f"{pack.yoga_name} ({kalpana}) એક શાસ્ત્રીય યોગ છે, "
            f"જે {primary_str} માટે યોગ્ય છે; સંદર્ભ: {work}."
        )
    else:
        primary_str = primary_str or "the stated conditions"
        ingredient_str = ingredient_str or "its constituent herbs"
        work = work or "classical texts"
        kalpana = kalpana or "decoction"
        claims = [
            ExplanationClaim(
                text=f"{pack.yoga_name} is indicated in {primary_str}.",
                ref_ids=ref_ids[:1],
            )
        ]
        if secondary_str:
            claims.append(
                ExplanationClaim(
                    text=f"Its constituent herbs ({ingredient_str}) provide additional coverage for {secondary_str}.",
                    ref_ids=ref_ids[:1],
                )
            )
        if pack.safety_violations:
            claims.append(
                ExplanationClaim(
                    text="Note safety considerations: " + "; ".join(v.message[:80] for v in pack.safety_violations),
                    ref_ids=[],
                )
            )
        if pack.differentiation_note:
            claims.append(ExplanationClaim(text=pack.differentiation_note, ref_ids=ref_ids[:1]))
        summary = (
            f"{pack.yoga_name} ({kalpana}) is a classical formulation "
            f"indicated for {primary_str}, referenced in {work}."
        )

    return Explanation(
        summary=summary,
        claims=claims,
        llm_used=False,
        template_fallback=True,
    )


def _validate_ref_ids(claims: list[dict], valid_ids: set[str]) -> list[ExplanationClaim]:
    result = []
    for c in claims:
        filtered_ids = [rid for rid in (c.get("ref_ids") or []) if rid in valid_ids]
        result.append(ExplanationClaim(text=c.get("text", ""), ref_ids=filtered_ids))
    return result


async def explain_recommendation(
    pack: EvidencePack,
    vignette_summary: str,
    llm_client=None,
    locale: str = "en",
) -> Explanation:
    locale = _norm_locale(locale)
    if not LLM_ENABLED or not llm_client:
        return _template_explanation(pack, locale)

    valid_ref_ids = {r.ref_id for r in pack.references if r.ref_id}
    pack_json = pack.model_dump_json(indent=2)

    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _recommend_system(locale)},
                {
                    "role": "user",
                    "content": f"Patient vignette: {vignette_summary}\n\nEvidence pack:\n{pack_json}",
                },
            ],
            max_tokens=600,
        )
        data = json.loads(response.choices[0].message.content)
        claims = _validate_ref_ids(data.get("claims", []), valid_ref_ids)
        return Explanation(
            summary=data.get("summary", ""),
            claims=claims,
            llm_used=True,
            template_fallback=False,
        )
    except Exception:
        return _template_explanation(pack, locale)


async def explain_compare(
    pack_a: EvidencePack,
    pack_b: EvidencePack,
    vignette_summary: str,
    llm_client=None,
    locale: str = "en",
) -> CompareResult:
    locale = _norm_locale(locale)

    def template_compare() -> CompareResult:
        winner = pack_a if pack_a.score >= pack_b.score else pack_b
        loser = pack_b if winner is pack_a else pack_a
        if locale == "hi":
            reason = (
                winner.differentiation_note
                or f"{winner.yoga_name} का समग्र उपयुक्तता अंक ({winner.score:.1f}) "
                   f"{loser.yoga_name} ({loser.score:.1f}) से अधिक है।"
            )
            summary = f"नैदानिक चित्र के आधार पर {winner.yoga_name} को {loser.yoga_name} से वरीयता दी गई है।"
        elif locale == "gu":
            reason = (
                winner.differentiation_note
                or f"{winner.yoga_name} નો એકંદર યોગ્યતા સ્કોર ({winner.score:.1f}) "
                   f"{loser.yoga_name} ({loser.score:.1f}) કરતાં વધુ છે."
            )
            summary = f"નૈદાનિક ચિત્રના આધારે {winner.yoga_name} ને {loser.yoga_name} કરતાં પ્રાધાન્ય આપવામાં આવ્યું છે."
        else:
            reason = (
                winner.differentiation_note
                or f"{winner.yoga_name} has a higher overall fit score ({winner.score:.1f}) "
                   f"vs {loser.yoga_name} ({loser.score:.1f}) for the given clinical picture."
            )
            summary = f"Based on the clinical presentation, {winner.yoga_name} is preferred over {loser.yoga_name}."

        explanation = Explanation(
            summary=summary,
            claims=[ExplanationClaim(text=reason, ref_ids=[r.ref_id for r in winner.references if r.ref_id][:1])],
            llm_used=False,
            template_fallback=True,
        )
        return CompareResult(
            yoga_a=pack_a,
            yoga_b=pack_b,
            discrimination_explanation=explanation,
            winner_yoga_id=winner.yoga_id,
            winner_reason=reason[:200],
        )

    if not LLM_ENABLED or not llm_client:
        return template_compare()

    valid_ref_ids = {r.ref_id for r in pack_a.references + pack_b.references if r.ref_id}

    try:
        user_content = (
            f"Patient vignette: {vignette_summary}\n\n"
            f"Formulation A:\n{pack_a.model_dump_json(indent=2)}\n\n"
            f"Formulation B:\n{pack_b.model_dump_json(indent=2)}"
        )
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _compare_system(locale)},
                {"role": "user", "content": user_content},
            ],
            max_tokens=800,
        )
        data = json.loads(response.choices[0].message.content)
        claims = _validate_ref_ids(data.get("claims", []), valid_ref_ids)
        winner_label = data.get("winner", "A")
        winner_pack = pack_a if winner_label == "A" else pack_b
        return CompareResult(
            yoga_a=pack_a,
            yoga_b=pack_b,
            discrimination_explanation=Explanation(
                summary=data.get("summary", ""),
                claims=claims,
                llm_used=True,
                template_fallback=False,
            ),
            winner_yoga_id=winner_pack.yoga_id,
            winner_reason=data.get("winner_reason", ""),
        )
    except Exception:
        return template_compare()
