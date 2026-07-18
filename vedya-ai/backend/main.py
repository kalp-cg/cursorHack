"""
VedyaAI FastAPI application.
Pipeline: Intake → Understand → Resolver → Retriever → Safety → Ranker → Evidence → Explain
"""
from __future__ import annotations
import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    VignetteInput, RecommendationResponse, HealthResponse,
    PresetVignette, CompareResult, RecommendedFormulation,
    EvidencePack,
)
from pipeline.intake import validate_and_normalize, get_presets, get_preset, build_clinical_frame
from pipeline.understand import understand
from pipeline.resolver import EntityResolver
from pipeline.retriever import retrieve_candidates
from pipeline.safety import SafetyEngine
from pipeline.ranker import rank
from pipeline.evidence import build_evidence_pack, build_compare_packs
from pipeline.explainer import explain_recommendation, explain_compare

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vedya:vedyapass@localhost:5432/vedyaai")
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"
CORPUS_VERSION = os.getenv("CORPUS_VERSION", "1.0.0")

# Global state
_db_conn = None
_llm_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_conn, _llm_client
    # Connect DB
    try:
        _db_conn = psycopg2.connect(DATABASE_URL)
        print("✓ Database connected")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        _db_conn = None

    # Init LLM client
    if LLM_ENABLED:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                import openai
                _llm_client = openai.AsyncOpenAI(api_key=api_key)
                print("✓ LLM client initialized")
            except ImportError:
                print("✗ openai package not found; LLM disabled")
                _llm_client = None
        else:
            print("✗ OPENAI_API_KEY not set; LLM disabled")
            _llm_client = None
    else:
        print("✓ LLM disabled by config (LLM_ENABLED=false)")

    yield

    if _db_conn:
        _db_conn.close()
        print("✓ Database connection closed")


app = FastAPI(
    title="VedyaAI API",
    description="Classical Ayurvedic Formulation Decision Support & Learning Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_db():
    if _db_conn is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db_conn


def _vignette_summary(frame) -> str:
    terms = frame.symptoms + frame.rogas
    if frame.comorbidities:
        terms += [f"with {c}" for c in frame.comorbidities]
    return ", ".join(terms[:6]) if terms else (frame.raw_input or "")[:100]


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    db_ok = False
    yoga_count = 0
    herb_count = 0
    if _db_conn:
        try:
            cur = _db_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM yogas")
            yoga_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM dravyas")
            herb_count = cur.fetchone()[0]
            cur.close()
            db_ok = True
        except Exception:
            pass
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_connected=db_ok,
        llm_enabled=bool(_llm_client),
        corpus_version=CORPUS_VERSION,
        formulation_count=yoga_count,
        herb_count=herb_count,
    )


@app.get("/presets", response_model=list[PresetVignette], tags=["Demo"])
async def list_presets():
    return get_presets()


@app.get("/presets/{preset_id}", tags=["Demo"])
async def run_preset(preset_id: str):
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return await recommend(preset.vignette)


@app.post("/recommend", response_model=RecommendationResponse, tags=["Core"])
async def recommend(inp: VignetteInput):
    db = _get_db()
    trace_id = str(uuid.uuid4())

    # 1. Validate & normalize
    inp = validate_and_normalize(inp)

    # 2. NL Understand → ClinicalFrame
    frame = await understand(inp, _llm_client)

    # 3. Entity resolution
    resolver = EntityResolver(db)
    resolver_output = resolver.resolve(frame)

    if not resolver_output.resolved_concepts:
        return RecommendationResponse(
            trace_id=trace_id,
            vignette_summary=frame.raw_input[:100],
            unresolved_terms=resolver_output.unresolved_terms,
            coverage_note="No recognized Ayurvedic terms found. Try adding symptoms like 'Jvara', 'Kasa', 'Pinasa'.",
        )

    # 4. Candidate retrieval
    candidates = retrieve_candidates(resolver_output, frame, db, top_k=50)

    if not candidates:
        return RecommendationResponse(
            trace_id=trace_id,
            vignette_summary=_vignette_summary(frame),
            resolved_concepts=resolver_output.resolved_concepts,
            unresolved_terms=resolver_output.unresolved_terms,
            sense_disambiguations=resolver_output.sense_disambiguations,
            coverage_note="No formulations found for these conditions in the current corpus.",
        )

    # 5. Safety engine (deterministic)
    safety_engine = SafetyEngine(db)
    safety_results = safety_engine.apply(candidates, frame)

    # Collect global safety alerts (any HARD_EXCLUDE or WARN across all candidates)
    all_violations = []
    for sr in safety_results:
        all_violations.extend(sr.violations)
    global_alerts = list({v.rule_id: v for v in all_violations}.values())

    # 6. Rank
    ranked = rank(candidates, safety_results, frame, top_k=inp.top_k)

    # 7. Evidence pack + Explanation for top results
    candidate_map = {c["yoga_id"]: c for c in candidates}
    excluded_count = sum(1 for sr in safety_results if sr.hard_excluded)
    warned_count = sum(1 for sr in safety_results if sr.violations and not sr.hard_excluded)

    vignette_summary = _vignette_summary(frame)
    llm_used = False

    for r in ranked[:5]:  # explain top 5 only
        yoga_data = candidate_map.get(r.yoga_id, {})
        pack = build_evidence_pack(yoga_data, r)
        explanation = await explain_recommendation(pack, vignette_summary, _llm_client)
        r.explanation = explanation
        if explanation.llm_used:
            llm_used = True

    # Log trace (anonymous)
    try:
        vignette_hash = hashlib.sha256(json.dumps(inp.model_dump(), sort_keys=True).encode()).hexdigest()[:16]
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO recommendation_traces
                (trace_id, vignette_hash, corpus_version, llm_used, top_yoga_id, feature_vector, safety_hits)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                trace_id,
                vignette_hash,
                CORPUS_VERSION,
                llm_used,
                ranked[0].yoga_id if ranked else None,
                json.dumps(ranked[0].rank_features.model_dump()) if ranked else None,
                json.dumps([v.rule_id for v in global_alerts]),
            ),
        )
        db.commit()
        cur.close()
    except Exception:
        pass  # Trace logging is non-critical

    coverage_note = None
    if resolver_output.unresolved_terms:
        coverage_note = f"Could not resolve: {', '.join(resolver_output.unresolved_terms[:5])}"

    return RecommendationResponse(
        trace_id=trace_id,
        vignette_summary=vignette_summary,
        resolved_concepts=resolver_output.resolved_concepts,
        sense_disambiguations=resolver_output.sense_disambiguations,
        unresolved_terms=resolver_output.unresolved_terms,
        safety_alerts=global_alerts,
        results=ranked,
        total_candidates=len(candidates),
        excluded_count=excluded_count,
        warned_count=warned_count,
        corpus_version=CORPUS_VERSION,
        llm_used=llm_used,
        coverage_note=coverage_note,
    )


@app.get("/formulation/{yoga_id}", tags=["Core"])
async def get_formulation(yoga_id: str):
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT y.yoga_id::text, y.name, k.name, k.medium_class, y.category,
               y.dosage, y.anupana, y.reference_text, y.differentiation_note,
               y.ambiguity_notes, y.external_only
        FROM yogas y
        LEFT JOIN kalpanas k ON y.kalpana_id = k.kalpana_id
        WHERE y.yoga_id = %s
        """,
        (yoga_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Formulation not found")

    # Ingredients with property data
    cur.execute(
        """
        SELECT ing.ingredient_name, ing.sense_override,
               d.botanical_name, d.english_name,
               ps.rasa, ps.guna, ps.virya, ps.vipaka, ps.prabhav, ps.pacify, ps.aggravate
        FROM yoga_ingredients ing
        LEFT JOIN dravyas d ON ing.dravya_id = d.dravya_id
        LEFT JOIN property_sets ps ON d.dravya_id = ps.dravya_id
        WHERE ing.yoga_id = %s
        """,
        (yoga_id,),
    )
    ingredients = [
        {
            "name": r[0], "sense_override": r[1], "botanical_name": r[2],
            "english_name": r[3], "rasa": r[4], "guna": r[5],
            "virya": r[6], "vipaka": r[7], "prabhav": r[8],
            "pacify": r[9], "aggravate": r[10],
        }
        for r in cur.fetchall()
    ]

    # References
    cur.execute(
        """
        SELECT r.ref_id::text, r.work, r.sthana, r.chapter, r.verse_id, r.excerpt_text
        FROM yoga_references yr
        JOIN references r ON yr.ref_id = r.ref_id
        WHERE yr.yoga_id = %s
        """,
        (yoga_id,),
    )
    refs = [
        {"ref_id": r[0], "work": r[1], "sthana": r[2], "chapter": r[3], "verse_id": r[4], "excerpt_text": r[5]}
        for r in cur.fetchall()
    ]
    cur.close()

    return {
        "yoga_id": row[0], "name": row[1], "kalpana": row[2],
        "medium_class": row[3], "category": row[4],
        "dosage": row[5], "anupana": row[6], "reference_text": row[7],
        "differentiation_note": row[8], "ambiguity_notes": row[9],
        "external_only": row[10],
        "ingredients": ingredients,
        "references": refs,
    }


@app.post("/compare", response_model=CompareResult, tags=["Core"])
async def compare_formulations(
    yoga_a_id: str = Query(..., description="Yoga A ID"),
    yoga_b_id: str = Query(..., description="Yoga B ID"),
    inp: VignetteInput = None,
):
    db = _get_db()
    if inp is None:
        inp = VignetteInput()

    frame = build_clinical_frame(inp)
    vignette_summary = _vignette_summary(frame) or "General comparison"

    async def fetch_yoga_data(yoga_id: str) -> dict:
        cur = db.cursor()
        cur.execute(
            """
            SELECT y.yoga_id::text, y.name, k.name, k.medium_class,
                   y.differentiation_note, y.ambiguity_notes
            FROM yogas y LEFT JOIN kalpanas k ON y.kalpana_id = k.kalpana_id
            WHERE y.yoga_id = %s
            """,
            (yoga_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Formulation {yoga_id} not found")

        cur.execute(
            "SELECT ing.ingredient_name, ing.sense_override, d.botanical_name, "
            "ps.rasa, ps.guna, ps.virya, ps.vipaka "
            "FROM yoga_ingredients ing LEFT JOIN dravyas d ON ing.dravya_id=d.dravya_id "
            "LEFT JOIN property_sets ps ON d.dravya_id=ps.dravya_id WHERE ing.yoga_id=%s",
            (yoga_id,),
        )
        ingredients = [{"name": r[0], "sense_override": r[1], "botanical_name": r[2],
                        "rasa": r[3], "guna": r[4], "virya": r[5], "vipaka": r[6]}
                       for r in cur.fetchall()]

        cur.execute(
            "SELECT r.ref_id::text, r.work, r.sthana, r.chapter, r.verse_id, r.excerpt_text "
            "FROM yoga_references yr JOIN references r ON yr.ref_id=r.ref_id WHERE yr.yoga_id=%s",
            (yoga_id,),
        )
        refs = [{"ref_id": r[0], "work": r[1], "sthana": r[2], "chapter": r[3],
                 "verse_id": r[4], "excerpt_text": r[5]} for r in cur.fetchall()]

        cur.execute(
            "SELECT concept_id::text, weight FROM yoga_indications WHERE yoga_id=%s", (yoga_id,)
        )
        ind_rows = cur.fetchall()
        primary = []
        secondary = []
        for cid, w in ind_rows:
            cur.execute("SELECT canonical_name FROM concepts WHERE concept_id=%s", (cid,))
            cn = cur.fetchone()
            if cn:
                (primary if w == "primary" else secondary).append(cn[0])
        cur.close()

        return {
            "yoga_id": row[0], "yoga_name": row[1], "kalpana_name": row[2],
            "medium_class": row[3], "differentiation_note": row[4],
            "ambiguity_notes": row[5], "ingredients": ingredients,
            "references": refs, "all_primary": primary, "all_secondary": secondary,
        }

    yoga_a_data = await fetch_yoga_data(yoga_a_id)
    yoga_b_data = await fetch_yoga_data(yoga_b_id)

    # Build minimal ranked results for evidence packs
    from pipeline.ranker import RankFeatures
    def make_result(yoga_data: dict, score: float) -> RecommendedFormulation:
        from models.schemas import RankFeatures as RF
        return RecommendedFormulation(
            rank=1, yoga_id=yoga_data["yoga_id"],
            yoga_name=yoga_data["yoga_name"],
            kalpana=yoga_data.get("kalpana_name"),
            score=score,
            rank_features=RF(),
            primary_indications=yoga_data.get("all_primary", []),
            secondary_indications=yoga_data.get("all_secondary", []),
            references=[],
            differentiation_note=yoga_data.get("differentiation_note"),
        )

    pack_a = build_evidence_pack(yoga_a_data, make_result(yoga_a_data, 0.0))
    pack_b = build_evidence_pack(yoga_b_data, make_result(yoga_b_data, 0.0))
    return await explain_compare(pack_a, pack_b, vignette_summary, _llm_client)


@app.get("/synonym-map/{concept_name}", tags=["Learn"])
async def synonym_map(concept_name: str):
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT c.concept_id::text, c.canonical_name, c.type,
               ARRAY_AGG(DISTINCT t.surface_form ORDER BY t.surface_form) AS synonyms
        FROM concepts c
        JOIN terms t ON t.concept_id = c.concept_id
        WHERE lower(c.canonical_name) = lower(%s) OR lower(t.surface_form) = lower(%s)
        GROUP BY c.concept_id, c.canonical_name, c.type
        LIMIT 1
        """,
        (concept_name, concept_name),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_name}' not found")
    return {
        "concept_id": row[0],
        "canonical_name": row[1],
        "type": row[2],
        "synonyms": row[3],
    }
