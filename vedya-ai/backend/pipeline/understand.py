"""
Understand module: convert free-text vignette → ClinicalFrame JSON.
Uses LLM when enabled; falls back to structured parsing from intake.
"""
from __future__ import annotations
import json
import os
from models.schemas import VignetteInput, ClinicalFrame
from pipeline.intake import build_clinical_frame

LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"

SYSTEM_PROMPT = """You are a clinical Ayurvedic entity extractor. 
Extract symptoms, diseases (rogas), and comorbidities from the patient vignette.
Output ONLY valid JSON matching this schema:
{
  "symptoms": ["list of symptom terms"],
  "rogas": ["list of roga/disease names in Ayurvedic or English"],
  "comorbidities": ["list of comorbidities e.g. Diabetes, Pregnancy"],
  "age_band": "child|adult|elderly or null",
  "pregnancy": false
}
Use Ayurvedic canonical terms where known (e.g. Jvara for fever, Kasa for cough, Pinasa for cold).
Do NOT invent diseases. Only extract what is clearly stated."""


async def understand(inp: VignetteInput, llm_client=None) -> ClinicalFrame:
    """Parse vignette into structured ClinicalFrame."""
    if not LLM_ENABLED or not llm_client or not inp.free_text:
        return build_clinical_frame(inp)

    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Patient vignette:\n{inp.free_text}"},
            ],
            max_tokens=400,
        )
        extracted = json.loads(response.choices[0].message.content)

        # Merge LLM extraction with explicit structured fields
        symptoms = list(dict.fromkeys(
            (extracted.get("symptoms") or []) + inp.symptoms
        ))
        rogas = list(dict.fromkeys(
            (extracted.get("rogas") or []) + inp.rogas
        ))
        comorbidities = list(dict.fromkeys(
            (extracted.get("comorbidities") or []) + inp.comorbidities
        ))
        pregnancy = extracted.get("pregnancy", False) or inp.pregnancy
        age_band = extracted.get("age_band") or inp.age_band

        if pregnancy and "Garbhini" not in comorbidities and "Pregnancy" not in comorbidities:
            comorbidities.append("Pregnancy")

        return ClinicalFrame(
            symptoms=symptoms,
            rogas=rogas,
            comorbidities=comorbidities,
            age_band=age_band,
            pregnancy=pregnancy,
            prakriti=inp.prakriti,
            kalpana_filter=inp.kalpana_filter,
            raw_input=inp.free_text,
        )
    except Exception:
        # Graceful degradation: fall back to structured
        return build_clinical_frame(inp)
