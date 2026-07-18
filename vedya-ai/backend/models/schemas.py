"""Pydantic schemas for API request/response and internal pipeline data."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Intake ───────────────────────────────────────────────────────────────────

class VignetteInput(BaseModel):
    """Raw user input — free-text or structured."""
    free_text: Optional[str] = Field(None, description="Free-text clinical vignette")
    symptoms: list[str] = Field(default_factory=list, description="Explicit symptom list")
    rogas: list[str] = Field(default_factory=list, description="Explicit disease names")
    comorbidities: list[str] = Field(default_factory=list, description="e.g. ['Diabetes','Pregnancy']")
    age_band: Optional[str] = Field(None, description="e.g. 'child','adult','elderly'")
    pregnancy: bool = False
    prakriti: Optional[str] = Field(None, description="Soft Prakriti hint: Vata/Pitta/Kapha")
    kalpana_filter: Optional[str] = Field(None, description="Prefer specific kalpana type")
    top_k: int = Field(10, ge=1, le=50)


class PresetVignette(BaseModel):
    id: str
    label: str
    description: str
    vignette: VignetteInput


# ─── Clinical Frame (output of NL Understand) ─────────────────────────────────

class ClinicalFrame(BaseModel):
    """Structured clinical frame derived from user vignette."""
    symptoms: list[str] = Field(default_factory=list)
    rogas: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    age_band: Optional[str] = None
    pregnancy: bool = False
    prakriti: Optional[str] = None
    kalpana_filter: Optional[str] = None
    raw_input: str = ""


# ─── Resolved concepts (output of Entity Resolver) ────────────────────────────

class ResolvedConcept(BaseModel):
    surface_form: str
    canonical_name: str
    concept_id: str
    concept_type: str
    synonyms_used: list[str] = Field(default_factory=list)


class SenseDisambiguation(BaseModel):
    term: str
    default_dravya: str
    resolved_dravya: str
    context_yoga: str
    explanation: str


class ResolverOutput(BaseModel):
    resolved_concepts: list[ResolvedConcept] = Field(default_factory=list)
    unresolved_terms: list[str] = Field(default_factory=list)
    sense_disambiguations: list[SenseDisambiguation] = Field(default_factory=list)


# ─── Safety ───────────────────────────────────────────────────────────────────

class SafetyViolation(BaseModel):
    rule_id: str
    severity: str  # HARD_EXCLUDE | WARN
    message: str
    classical_basis: Optional[str] = None


class SafetyResult(BaseModel):
    yoga_id: str
    yoga_name: str
    violations: list[SafetyViolation] = Field(default_factory=list)
    hard_excluded: bool = False


# ─── Ranking ──────────────────────────────────────────────────────────────────

class RankFeatures(BaseModel):
    primary_indication_match: float = 0.0
    secondary_indication_match: float = 0.0
    property_fit: float = 0.0
    citation_bonus: float = 0.0
    contraindication_penalty: float = 0.0
    medium_penalty: float = 0.0
    total_score: float = 0.0


# ─── Evidence Pack ────────────────────────────────────────────────────────────

class ReferenceCard(BaseModel):
    ref_id: str
    work: str
    sthana: Optional[str] = None
    chapter: Optional[str] = None
    verse_id: Optional[str] = None
    excerpt_text: Optional[str] = None


class PropertyCard(BaseModel):
    rasa: Optional[list[str]] = None
    guna: Optional[list[str]] = None
    virya: Optional[str] = None
    vipaka: Optional[str] = None
    prabhav: Optional[list[str]] = None
    pacify: Optional[list[str]] = None
    aggravate: Optional[list[str]] = None
    coverage_note: Optional[str] = None


class EvidencePack(BaseModel):
    yoga_id: str
    yoga_name: str
    kalpana: Optional[str] = None
    medium_class: Optional[str] = None
    primary_indications: list[str] = Field(default_factory=list)
    secondary_indications: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    references: list[ReferenceCard] = Field(default_factory=list)
    properties: Optional[PropertyCard] = None
    rank_features: Optional[RankFeatures] = None
    safety_violations: list[SafetyViolation] = Field(default_factory=list)
    differentiation_note: Optional[str] = None
    ambiguity_notes: Optional[dict[str, Any]] = None
    score: float = 0.0


# ─── Explanation ──────────────────────────────────────────────────────────────

class ExplanationClaim(BaseModel):
    text: str
    ref_ids: list[str] = Field(default_factory=list)


class Explanation(BaseModel):
    summary: str
    claims: list[ExplanationClaim] = Field(default_factory=list)
    llm_used: bool = False
    template_fallback: bool = False


# ─── Recommendation Response ──────────────────────────────────────────────────

class RecommendedFormulation(BaseModel):
    rank: int
    yoga_id: str
    yoga_name: str
    kalpana: Optional[str] = None
    category: Optional[str] = None
    score: float
    rank_features: RankFeatures
    safety_violations: list[SafetyViolation] = Field(default_factory=list)
    hard_excluded: bool = False
    primary_indications: list[str] = Field(default_factory=list)
    secondary_indications: list[str] = Field(default_factory=list)
    references: list[ReferenceCard] = Field(default_factory=list)
    explanation: Optional[Explanation] = None
    differentiation_note: Optional[str] = None
    dosage: Optional[str] = None
    anupana: Optional[str] = None
    coverage_note: Optional[str] = None


class CompareResult(BaseModel):
    yoga_a: EvidencePack
    yoga_b: EvidencePack
    discrimination_explanation: Optional[Explanation] = None
    winner_yoga_id: Optional[str] = None
    winner_reason: Optional[str] = None


class RecommendationResponse(BaseModel):
    trace_id: str
    vignette_summary: str
    resolved_concepts: list[ResolvedConcept] = Field(default_factory=list)
    sense_disambiguations: list[SenseDisambiguation] = Field(default_factory=list)
    unresolved_terms: list[str] = Field(default_factory=list)
    safety_alerts: list[SafetyViolation] = Field(default_factory=list)
    results: list[RecommendedFormulation] = Field(default_factory=list)
    total_candidates: int = 0
    excluded_count: int = 0
    warned_count: int = 0
    corpus_version: str = "1.0.0"
    llm_used: bool = False
    coverage_note: Optional[str] = None
    disclaimer: str = (
        "Educational decision support only. "
        "Not a diagnosis or prescription. "
        "Clinical judgment of a qualified vaidya is required."
    )


class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    llm_enabled: bool
    corpus_version: str
    formulation_count: int = 0
    herb_count: int = 0
