"""
Intake module: validate and normalize the user vignette input.
Also owns the demo presets.
"""
from __future__ import annotations
from models.schemas import VignetteInput, PresetVignette, ClinicalFrame

PRESETS: list[PresetVignette] = [
    PresetVignette(
        id="pinasa_urti",
        label="Fever + Cough + Common Cold (Pinasa)",
        description="Adult patient with fever, cough, and clear nasal discharge — classic URTI / Pratishyaya presentation.",
        vignette=VignetteInput(
            free_text="Patient with fever, cough, and running nose (common cold). No known comorbidities.",
            symptoms=["Fever", "Cough", "Common Cold", "Runny nose"],
            rogas=["Jvara", "Kasa", "Pinasa"],
            comorbidities=[],
            age_band="adult",
        ),
    ),
    PresetVignette(
        id="inflammatory_shotha",
        label="Fever + Cough + Generalized Inflammation",
        description="Patient with fever, cough, and systemic inflammatory changes / edema (Shotha) throughout the body.",
        vignette=VignetteInput(
            free_text="Patient presenting with fever, cough, and generalized inflammatory swelling (Shotha/edema) all over the body.",
            symptoms=["Fever", "Cough", "Edema", "Swelling", "Inflammation"],
            rogas=["Jvara", "Kasa", "Shotha"],
            comorbidities=[],
            age_band="adult",
        ),
    ),
    PresetVignette(
        id="diabetic_respiratory",
        label="Fever + Cough + Diabetes (Prameha)",
        description="Diabetic patient with fever and cough — demonstrates safety gates for fermented preparations and sweeteners.",
        vignette=VignetteInput(
            free_text="Diabetic patient with fever and cough. Known case of Prameha (Diabetes Mellitus).",
            symptoms=["Fever", "Cough"],
            rogas=["Jvara", "Kasa"],
            comorbidities=["Diabetes", "Prameha"],
            age_band="adult",
        ),
    ),
]

PRESET_MAP = {p.id: p for p in PRESETS}


def get_presets() -> list[PresetVignette]:
    return PRESETS


def get_preset(preset_id: str) -> PresetVignette | None:
    return PRESET_MAP.get(preset_id)


def validate_and_normalize(inp: VignetteInput) -> VignetteInput:
    """Normalize the input: strip whitespace, lowercase comorbidities for matching."""
    return VignetteInput(
        free_text=(inp.free_text or "").strip() or None,
        symptoms=[s.strip() for s in inp.symptoms if s.strip()],
        rogas=[r.strip() for r in inp.rogas if r.strip()],
        comorbidities=[c.strip() for c in inp.comorbidities if c.strip()],
        age_band=inp.age_band,
        pregnancy=inp.pregnancy,
        prakriti=inp.prakriti,
        kalpana_filter=inp.kalpana_filter,
        top_k=inp.top_k,
    )


def build_clinical_frame(inp: VignetteInput) -> ClinicalFrame:
    """Build a ClinicalFrame directly from structured input (used when LLM is off)."""
    all_terms = inp.symptoms + inp.rogas
    raw = inp.free_text or ", ".join(all_terms)
    comorbidities = list(inp.comorbidities)
    if inp.pregnancy and "Garbhini" not in comorbidities and "Pregnancy" not in comorbidities:
        comorbidities.append("Pregnancy")
    return ClinicalFrame(
        symptoms=inp.symptoms,
        rogas=inp.rogas,
        comorbidities=comorbidities,
        age_band=inp.age_band,
        pregnancy=inp.pregnancy,
        prakriti=inp.prakriti,
        kalpana_filter=inp.kalpana_filter,
        raw_input=raw,
    )
