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
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    VignetteInput, RecommendationResponse, HealthResponse,
    PresetVignette, CompareResult, RecommendedFormulation,
    EvidencePack, TranslateRequest, TranslateResponse,
)
from translate_service import translate_texts, last_provider
from rag import answer_question
from pipeline.intake import validate_and_normalize, get_presets, get_preset, build_clinical_frame
from pipeline.understand import understand
from pipeline.resolver import EntityResolver
from pipeline.retriever import retrieve_candidates
from pipeline.safety import SafetyEngine
from pipeline.ranker import rank
from pipeline.evidence import build_evidence_pack, build_compare_packs
from pipeline.explainer import explain_recommendation, explain_compare
from auth import (
    AuthResponse, AuthUser, LoginRequest, SignupRequest,
    authenticate_user, create_access_token, create_user,
    fetch_user_by_id, get_optional_user, require_admin, require_user,
)
from conversations import (
    add_message, assert_conversation_owner, build_followup_context,
    create_conversation, get_messages, list_conversations,
)
from voice import (
    build_listen_script, synthesize_speech, transcribe_audio, voice_configured, voice_status,
)
from fastapi.responses import Response
from fastapi import File, Form, UploadFile

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

_extra_origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    # Local dev origins + deployed frontend URL(s) via FRONTEND_ORIGINS env
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        *_extra_origins,
    ],
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


@app.post("/auth/signup", response_model=AuthResponse, tags=["Auth"])
async def signup(req: SignupRequest):
    db = _get_db()
    user = create_user(db, req)
    token = create_access_token(user.user_id, user.email, user.role)
    return AuthResponse(access_token=token, user=user)


@app.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
async def login(req: LoginRequest):
    db = _get_db()
    user = authenticate_user(db, req)
    token = create_access_token(user.user_id, user.email, user.role)
    return AuthResponse(access_token=token, user=user)


@app.get("/auth/me", response_model=AuthUser, tags=["Auth"])
async def me(user: AuthUser = Depends(require_user)):
    db = _get_db()
    row = fetch_user_by_id(db, user.user_id)
    if not row or not row["is_active"]:
        raise HTTPException(status_code=401, detail="User not found")
    return AuthUser(
        user_id=row["user_id"],
        email=row["email"],
        display_name=row["display_name"],
        preferred_locale=row["preferred_locale"],
        role=row.get("role", "user"),
    )


@app.get("/conversations", tags=["Conversations"])
async def conversations_list(user: AuthUser = Depends(require_user)):
    db = _get_db()
    return list_conversations(db, user.user_id)


@app.get("/conversations/{conversation_id}", tags=["Conversations"])
async def conversation_detail(conversation_id: str, user: AuthUser = Depends(require_user)):
    db = _get_db()
    meta = assert_conversation_owner(db, conversation_id, user.user_id)
    return {"conversation": meta, "messages": get_messages(db, conversation_id, user.user_id)}


@app.get("/presets", response_model=list[PresetVignette], tags=["Demo"])
async def list_presets(locale: str = Query("en")):
    presets = get_presets()
    loc = (locale or "en").lower()
    if loc not in {"hi", "gu"}:
        return presets
    labels = [p.label for p in presets]
    descs = [p.description for p in presets]
    try:
        t_labels = await translate_texts(labels, loc, "en")
        t_descs = await translate_texts(descs, loc, "en")
        return [
            PresetVignette(
                id=p.id,
                label=t_labels[i] if i < len(t_labels) else p.label,
                description=t_descs[i] if i < len(t_descs) else p.description,
                vignette=p.vignette,
            )
            for i, p in enumerate(presets)
        ]
    except Exception as e:
        print(f"✗ Preset translation skipped: {e}")
        return presets


@app.post("/translate", response_model=TranslateResponse, tags=["i18n"])
async def translate_endpoint(body: TranslateRequest):
    """Batch-translate strings via Google Cloud Translation or gtx fallback."""
    if not body.texts:
        return TranslateResponse(
            translations=[],
            target_locale=body.target_locale,
            source_locale=body.source_locale,
            provider="none",
        )
    if len(body.texts) > 80:
        raise HTTPException(status_code=400, detail="Max 80 texts per request")
    for t in body.texts:
        if len(t) > 2000:
            raise HTTPException(status_code=400, detail="Each text max 2000 chars")

    provider = "none"
    translations = await translate_texts(
        body.texts, body.target_locale, body.source_locale
    )
    provider = last_provider()
    return TranslateResponse(
        translations=translations,
        target_locale=body.target_locale,
        source_locale=body.source_locale,
        provider=provider,
    )


@app.get("/presets/{preset_id}", tags=["Demo"])
async def run_preset(
    preset_id: str,
    locale: str = Query("en"),
    user: Optional[AuthUser] = Depends(get_optional_user),
):
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    loc = (locale or "en").lower()
    if loc not in {"en", "gu"}:
        loc = "en"
    vignette = preset.vignette.model_copy(update={"locale": loc})
    return await recommend(vignette, user=user)


@app.post("/recommend", response_model=RecommendationResponse, tags=["Core"])
async def recommend(inp: VignetteInput, user: Optional[AuthUser] = Depends(get_optional_user)):
    db = _get_db()
    trace_id = str(uuid.uuid4())
    conversation_id = inp.conversation_id
    locale = (inp.locale or "en").lower()
    if locale not in {"en", "gu"}:
        locale = "en"

    # Conversation continuity (authenticated users)
    if user and inp.follow_up and conversation_id:
        assert_conversation_owner(db, conversation_id, user.user_id)
        follow_text = (inp.free_text or "").strip()
        if not follow_text:
            raise HTTPException(status_code=400, detail="Follow-up text required")
        merged = build_followup_context(db, conversation_id, follow_text)
        inp = inp.model_copy(update={"free_text": merged})
        add_message(db, conversation_id, "user", follow_text)
    elif user and not conversation_id:
        title = (inp.free_text or ",".join(inp.symptoms + inp.rogas) or "Clinical case")[:120]
        conversation_id = create_conversation(db, user.user_id, title, locale)
        add_message(db, conversation_id, "user", inp.free_text or title)
    elif conversation_id and not user:
        # Guests cannot attach to persisted conversations
        conversation_id = None

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
            conversation_id=conversation_id,
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
            conversation_id=conversation_id,
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
        explanation = await explain_recommendation(pack, vignette_summary, _llm_client, locale=locale)
        r.explanation = explanation
        if explanation.llm_used:
            llm_used = True

    # Log trace (anonymous hash; user/conversation linked when authenticated)
    try:
        vignette_hash = hashlib.sha256(json.dumps(inp.model_dump(), sort_keys=True).encode()).hexdigest()[:16]
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO recommendation_traces
                (trace_id, vignette_hash, corpus_version, llm_used, top_yoga_id, feature_vector,
                 safety_hits, user_id, conversation_id, unresolved_terms, vignette_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                trace_id,
                vignette_hash,
                CORPUS_VERSION,
                llm_used,
                ranked[0].yoga_id if ranked else None,
                json.dumps(ranked[0].rank_features.model_dump()) if ranked else None,
                json.dumps([v.rule_id for v in global_alerts]),
                user.user_id if user else None,
                conversation_id,
                json.dumps(resolver_output.unresolved_terms or []),
                vignette_summary[:300] if vignette_summary else None,
            ),
        )
        db.commit()
        cur.close()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    coverage_note = None
    if resolver_output.unresolved_terms:
        coverage_note = f"Could not resolve: {', '.join(resolver_output.unresolved_terms[:5])}"

    response = RecommendationResponse(
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
        conversation_id=conversation_id,
    )

    if user and conversation_id:
        top_name = ranked[0].yoga_name if ranked else "No match"
        summary = f"Top pick: {top_name}. {vignette_summary}"
        add_message(
            db,
            conversation_id,
            "assistant",
            summary,
            payload=response.model_dump(mode="json"),
        )

    return response


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
        JOIN "references" r ON yr.ref_id = r.ref_id
        WHERE yr.yoga_id = %s
        """,
        (yoga_id,),
    )
    refs = [
        {"ref_id": r[0], "work": r[1], "sthana": r[2], "chapter": r[3], "verse_id": r[4], "excerpt_text": r[5]}
        for r in cur.fetchall()
    ]
    cur.close()

    # Indication tags (primary / secondary)
    cur2 = db.cursor()
    cur2.execute(
        """
        SELECT c.canonical_name, yi.weight
        FROM yoga_indications yi
        JOIN concepts c ON yi.concept_id = c.concept_id
        WHERE yi.yoga_id = %s
        ORDER BY yi.weight, c.canonical_name
        """,
        (yoga_id,),
    )
    primary_indications: list[str] = []
    secondary_indications: list[str] = []
    for name, weight in cur2.fetchall():
        if (weight or "").lower() == "primary":
            primary_indications.append(name)
        else:
            secondary_indications.append(name)
    cur2.close()

    return {
        "yoga_id": row[0], "name": row[1], "kalpana": row[2],
        "medium_class": row[3], "category": row[4],
        "dosage": row[5], "anupana": row[6], "reference_text": row[7],
        "differentiation_note": row[8], "ambiguity_notes": row[9],
        "external_only": row[10],
        "ingredients": ingredients,
        "references": refs,
        "primary_indications": primary_indications,
        "secondary_indications": secondary_indications,
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
            'FROM yoga_references yr JOIN "references" r ON yr.ref_id=r.ref_id WHERE yr.yoga_id=%s',
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
    locale = (inp.locale or "en").lower() if inp else "en"
    return await explain_compare(pack_a, pack_b, vignette_summary, _llm_client, locale=locale)


@app.get("/voice/status", tags=["Voice"])
async def get_voice_status():
    return voice_status()


@app.post("/voice/tts", tags=["Voice"])
async def voice_tts(
    text: str = Form(...),
    locale: str = Form("en"),
    voice_id: Optional[str] = Form(None),
):
    """Speak arbitrary clinical text (explanation, compare reason, case read-aloud)."""
    if not voice_configured():
        raise HTTPException(
            status_code=503,
            detail="Voice is not configured. Set ELEVENLABS_API_KEY in the server environment.",
        )
    try:
        audio = await synthesize_speech(text, voice_id=voice_id, locale=locale)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return Response(content=audio, media_type="audio/mpeg")


@app.post("/voice/listen-recommendation", tags=["Voice"])
async def voice_listen_recommendation(
    yoga_name: str = Form(...),
    summary: str = Form(""),
    kalpana: str = Form(""),
    winner_reason: str = Form(""),
    locale: str = Form("en"),
):
    """Build a localized listen script for top pick / A-vs-B and return MP3."""
    if not voice_configured():
        raise HTTPException(
            status_code=503,
            detail="Voice is not configured. Set ELEVENLABS_API_KEY in the server environment.",
        )
    script = build_listen_script(
        yoga_name=yoga_name,
        kalpana=kalpana or None,
        summary=summary,
        winner_reason=winner_reason or None,
        locale=locale,
    )
    try:
        audio = await synthesize_speech(script, locale=locale)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"X-Vedya-Script": script[:200].encode("ascii", "ignore").decode()},
    )


@app.post("/voice/stt", tags=["Voice"])
async def voice_stt(
    file: UploadFile = File(...),
    locale: str = Form("en"),
):
    """Transcribe a spoken vignette (browser mic recording) into text for /recommend."""
    if not voice_configured():
        raise HTTPException(
            status_code=503,
            detail="Voice is not configured. Set ELEVENLABS_API_KEY in the server environment.",
        )
    raw = await file.read()
    try:
        result = await transcribe_audio(raw, filename=file.filename or "audio.webm", locale=locale)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    if not result.get("text"):
        raise HTTPException(status_code=422, detail="Could not transcribe audio. Please try again.")
    return result


# ─── Ask — RAG over the classical corpus ─────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    locale: str = "en"
    top_k: int = 8


# Deterministic answers (no LLM) → identical questions can share one response.
# Bounded FIFO cache: repeated demo/classroom questions cost zero DB and zero
# translation calls, which is where the per-prompt cost actually lives.
_ASK_CACHE: dict[tuple[str, str], dict] = {}
_ASK_CACHE_MAX = 512

_DISCLAIMER = "Educational reference from classical sources — not a diagnosis or prescription."


@app.post("/ask", tags=["Ask"])
async def ask(req: AskRequest, user: Optional[AuthUser] = Depends(get_optional_user)):
    """Question answering grounded in the 16k+ verse corpus.
    Query expansion via synonyms → FTS retrieval → citation-bound answer.
    Optional LLM narration when a key is configured; retrieval always decides content."""
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 chars)")

    locale = (req.locale or "en").lower()
    if locale not in {"en", "gu"}:
        locale = "en"

    cache_key = (" ".join(question.lower().split()), locale)
    cached = _ASK_CACHE.get(cache_key)
    if cached is not None and _llm_client is None:
        return {**cached, "cached": True}

    # Corpus + synonym table are English/IAST. Bridge Gujarati-script questions
    # via translation; romanized Gujarati ("mane tav chhe") is handled inside
    # the RAG lexicon without a network call.
    retrieval_question = question
    import re as _re
    if _re.search(r"[\u0900-\u097F\u0A80-\u0AFF]", question):
        src = "gu" if _re.search(r"[\u0A80-\u0AFF]", question) else "hi"
        try:
            retrieval_question = (await translate_texts([question], "en", src))[0]
        except Exception:
            pass

    db = _get_db()
    result = await answer_question(
        db, retrieval_question, llm_client=_llm_client, locale=locale, k=min(max(req.top_k, 3), 12)
    )
    result["question"] = question
    if retrieval_question != question:
        result["retrieval_question"] = retrieval_question

    # Translate the composed summary line-by-line so structure survives;
    # verse excerpts stay in the original translation of the source text.
    if locale != "en" and not result["llm_used"] and result.get("answer_lines"):
        try:
            translated = await translate_texts(result["answer_lines"], locale, "en")
            result["answer_lines"] = translated
            result["answer"] = "\n".join(translated)
        except Exception:
            pass

    result["disclaimer"] = _DISCLAIMER

    if len(_ASK_CACHE) >= _ASK_CACHE_MAX:
        _ASK_CACHE.pop(next(iter(_ASK_CACHE)))
    _ASK_CACHE[cache_key] = result
    return result


# ─── Admin scope — corpus stewardship & oversight ────────────────────────────
# Users (students/vaidyas) run cases. Admins (faculty/curators) close the loop:
# see what the corpus is missing, watch usage, manage accounts.

@app.get("/admin/stats", tags=["Admin"])
async def admin_stats(admin: AuthUser = Depends(require_admin)):
    """Corpus + usage overview for the curator dashboard."""
    db = _get_db()
    cur = db.cursor()
    counts: dict[str, int] = {}
    for label, sql in [
        ("formulations", "SELECT COUNT(*) FROM yogas"),
        ("herbs", "SELECT COUNT(*) FROM dravyas"),
        ("concepts", "SELECT COUNT(*) FROM concepts"),
        ("synonym_terms", "SELECT COUNT(*) FROM terms"),
        ("constraint_rules", "SELECT COUNT(*) FROM constraint_rules"),
        ("sense_rules", "SELECT COUNT(*) FROM sense_rules"),
        ("references", 'SELECT COUNT(*) FROM "references"'),
        ("users", "SELECT COUNT(*) FROM users"),
        ("conversations", "SELECT COUNT(*) FROM conversations"),
        ("cases_run", "SELECT COUNT(*) FROM recommendation_traces"),
    ]:
        cur.execute(sql)
        counts[label] = cur.fetchone()[0]

    cur.execute(
        """
        SELECT y.name, COUNT(*) AS n
        FROM recommendation_traces rt
        JOIN yogas y ON rt.top_yoga_id = y.yoga_id
        GROUP BY y.name ORDER BY n DESC LIMIT 5
        """
    )
    top_yogas = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM recommendation_traces WHERE created_at > NOW() - INTERVAL '24 hours'")
    counts["cases_last_24h"] = cur.fetchone()[0]
    cur.close()

    return {
        "corpus_version": CORPUS_VERSION,
        "llm_enabled": LLM_ENABLED,
        "counts": counts,
        "top_recommended": top_yogas,
    }


@app.get("/admin/unresolved-terms", tags=["Admin"])
async def admin_unresolved_terms(admin: AuthUser = Depends(require_admin)):
    """Vocabulary gap report: terms users typed that the resolver could not map.
    This is the curator's to-do list for expanding synonyms/corpus."""
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT term, COUNT(*) AS n, MAX(created_at) AS last_seen
        FROM recommendation_traces rt,
             jsonb_array_elements_text(COALESCE(rt.unresolved_terms, '[]'::jsonb)) AS term
        GROUP BY term ORDER BY n DESC, last_seen DESC LIMIT 50
        """
    )
    rows = [{"term": r[0], "count": r[1], "last_seen": r[2].isoformat() if r[2] else None} for r in cur.fetchall()]
    cur.close()
    return {"unresolved_terms": rows, "total_distinct": len(rows)}


@app.get("/admin/traces", tags=["Admin"])
async def admin_traces(limit: int = Query(25, ge=1, le=100), admin: AuthUser = Depends(require_admin)):
    """Recent cases run on the platform (anonymised summaries)."""
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT rt.trace_id::text, rt.created_at, rt.vignette_summary, y.name,
               rt.llm_used, rt.safety_hits, u.email
        FROM recommendation_traces rt
        LEFT JOIN yogas y ON rt.top_yoga_id = y.yoga_id
        LEFT JOIN users u ON rt.user_id = u.user_id
        ORDER BY rt.created_at DESC LIMIT %s
        """,
        (limit,),
    )
    traces = [
        {
            "trace_id": r[0],
            "created_at": r[1].isoformat() if r[1] else None,
            "vignette_summary": r[2],
            "top_yoga": r[3],
            "llm_used": r[4],
            "safety_hits": r[5] or [],
            "user_email": r[6],
        }
        for r in cur.fetchall()
    ]
    cur.close()
    return {"traces": traces}


@app.get("/admin/users", tags=["Admin"])
async def admin_users(admin: AuthUser = Depends(require_admin)):
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT u.user_id::text, u.email, u.display_name, u.role, u.is_active,
               u.created_at, u.last_login_at,
               (SELECT COUNT(*) FROM conversations c WHERE c.user_id = u.user_id) AS conversations,
               (SELECT COUNT(*) FROM recommendation_traces rt WHERE rt.user_id = u.user_id) AS cases_run
        FROM users u ORDER BY u.created_at DESC
        """
    )
    users = [
        {
            "user_id": r[0],
            "email": r[1],
            "display_name": r[2],
            "role": r[3],
            "is_active": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "last_login_at": r[6].isoformat() if r[6] else None,
            "conversations": r[7],
            "cases_run": r[8],
        }
        for r in cur.fetchall()
    ]
    cur.close()
    return {"users": users}


@app.patch("/admin/users/{user_id}", tags=["Admin"])
async def admin_update_user(
    user_id: str,
    is_active: Optional[bool] = Query(None),
    role: Optional[str] = Query(None),
    admin: AuthUser = Depends(require_admin),
):
    """Activate/deactivate a user or change their role. Admins cannot demote themselves."""
    if role is not None and role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    if user_id == admin.user_id and (role == "user" or is_active is False):
        raise HTTPException(status_code=400, detail="You cannot demote or deactivate yourself")
    if is_active is None and role is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    db = _get_db()
    cur = db.cursor()
    sets, params = [], []
    if is_active is not None:
        sets.append("is_active = %s")
        params.append(is_active)
    if role is not None:
        sets.append("role = %s")
        params.append(role)
    params.append(user_id)
    cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id = %s RETURNING user_id::text", params)
    row = cur.fetchone()
    db.commit()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"updated": row[0]}


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
