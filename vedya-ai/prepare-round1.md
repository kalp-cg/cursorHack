# VedyaAI — Round 1 reviewer / demo prep sheet

Use this when a judge asks you to walk through the product, UI, or backend.
Speak in plain language. Keep the disclaimer ready: educational decision support, not diagnosis or prescription.

---

## 1. One-sentence pitch

**VedyaAI ranks classical Ayurvedic formulations for a clinical vignette, shows why A beats B, cites sources, and blocks unsafe picks — with optional voice and Hindi/Gujarati explanations.**

Core rule (memorize this):

> **Structure decides → Rules protect → Retrieval grounds → LLM explains**

The LLM never chooses the winner. The deterministic ranker + safety engine do.

---

## 2. Live demo path (2–3 minutes)

1. Open `http://localhost:3000` (API on `:8000`).
2. Switch language (EN / HI / GU) in the top bar — UI + explanations follow locale.
3. Click a **demo vignette** (e.g. Pinasa / URTI) **or** type/speak a vignette.
4. On **Results**:
   - Top recommendation + Listen (ElevenLabs TTS if key set)
   - **What if…** toggles (Diabetes / Pregnancy…) → re-rank → show score/safety flip
   - Compare A vs B → spoken “why A over B”
   - **Share case** / **Export markdown** for faculty
5. Optional: Log in (`demo@vedya.ai` / `DemoPass123`) → follow-up question → history.

If voice buttons say “Voice off”: `ELEVENLABS_API_KEY` is missing in `vedya-ai/.env`. Ranking still works.

---

## 3. Architecture (draw this if asked)

```
Browser (Next.js :3000)
   │  POST /recommend, /compare, /voice/*
   ▼
FastAPI (backend/main.py :8000)
   │
   ├─ intake → understand → resolver (synonyms / sense)
   ├─ retriever (candidate yogas from Postgres)
   ├─ safety (HARD_EXCLUDE / WARN)
   ├─ ranker (feature scores → ordered list)
   ├─ evidence packs + citations
   └─ explainer (templates or LLM; locale-aware)
         │
         └─ voice.py → ElevenLabs TTS / STT (optional)
                │
Postgres (Docker, host port 5433 → container 5432)
   yogas, herbs, terms, constraints, auth, conversations
```

**Data flow for a recommend call**

1. Normalize vignette (symptoms, rogas, comorbidities, locale).
2. Resolve vernacular → canonical concepts (`terms` / synonyms).
3. Retrieve candidate formulations.
4. Apply safety rules (pregnancy, diabetes-sensitive media, etc.).
5. Score remaining candidates (indication match, properties, citations, penalties).
6. Build evidence + explanation in EN/HI/GU.
7. Optionally persist conversation if JWT user is present.

Voice path: Mic → `/voice/stt` → text into same `/recommend` → `/voice/listen-recommendation` or `/voice/tts` → MP3 in browser. Voice never bypasses safety.

---

## 4. Features you can explain (this round)

| Feature | Where in UI | What to say |
|---------|-------------|-------------|
| Locale-aware explanations | Language select + Results summary | Ranker is language-agnostic; explainer templates (and LLM prompts) emit EN/HI/GU. Sanskrit yoga names stay classical. |
| ElevenLabs Listen | Results top pick, Compare, preset “read case” | TTS of ranking summary + disclaimer. Models via env (`eleven_multilingual_v2` default). |
| Voice intake | Home mic, New Case mic, Follow-up mic | STT (Scribe) with Ayurveda **keyterms** (Jvara, Kashaya, Punarnavadi…). Transcript fills free text → same ranker. |
| Speak why A over B | Compare page Listen | Uses compare `winner_reason` + discrimination summary as TTS script. |
| Counterfactual “What if…” | Results panel | Toggle comorbidity → fresh `/recommend` → show baseline vs alternate top pick, score delta, safety flip. Teaching / pedagogy. |
| Share + export | Results bottom | Share copies `/results?case=<base64url vignette>`; opening the link re-runs ranking. Export downloads citation markdown for faculty. |
| Auth + history | Login / My cases | JWT in localStorage; conversations stored in Postgres for follow-ups. |

---

## 5. Backend endpoints worth naming

- `POST /recommend` — full discrimination pipeline  
- `POST /compare?yoga_a_id=&yoga_b_id=` — side-by-side + winner reason  
- `GET /presets`, `GET /presets/{id}` — golden classroom cases  
- `GET /voice/status`, `POST /voice/tts`, `POST /voice/stt`, `POST /voice/listen-recommendation`  
- `POST /auth/signup|login`, `GET /auth/me`, `/conversations*`  
- `GET /health` — DB + corpus version  

Key modules: `pipeline/ranker.py`, `pipeline/safety.py`, `pipeline/explainer.py`, `voice.py`, `auth.py`.

---

## 6. Likely reviewer questions → short answers

**“Is this just ChatGPT over Ayurveda PDFs?”**  
No. Retrieval and ranking are structured. LLM (if enabled) only narrates already-chosen evidence. With `LLM_ENABLED=false` the system still ranks via templates.

**“How do you prevent unsafe recommendations?”**  
`SafetyEngine` applies hard excludes and warnings before/along ranking. Excluded yogas stay visible but marked; they are not the top pick.

**“Why voice?”**  
Classroom demos + accessibility + faster intake. Still educational — audio ends with the same disclaimer.

**“How does Hindi/Gujarati work?”**  
`locale` on the request drives i18n UI and explainer language. Entity resolution still uses the synonym table (classical + vernacular surfaces).

**“What is counterfactual for?”**  
Show students that adding diabetes can flip the winner or raise safety flags — discrimination, not autocomplete.

**“Where is the corpus?”**  
Postgres loaded from formulation JSON, herbs, synonyms, constraints. Demo count is on `/health` (`formulation_count`).

**“Ports?”**  
Frontend 3000, API 8000, Postgres **5433** on Windows (mapped from container 5432) because local Postgres often owns 5432.

---

## 7. Env knobs

| Variable | Role |
|----------|------|
| `DATABASE_URL` | Postgres (use port 5433 locally) |
| `LLM_ENABLED` | `false` = template explanations only |
| `OPENAI_API_KEY` | Optional LLM narrations |
| `JWT_SECRET` | Auth tokens |
| `ELEVENLABS_API_KEY` | Enables voice |
| `ELEVENLABS_VOICE_ID` / `ELEVENLABS_TTS_MODEL` / `ELEVENLABS_STT_MODEL` | Voice tuning |

Copy from `vedya-ai/.env.example`.

---

## 8. Honest limits (say these before they ask)

- Not a licensed clinical system; for education / decision support demos.  
- Corpus coverage is incomplete vs all of Bhaishajya Ratnavali / Samhitas.  
- Homonyms (e.g. Abhaya) need sense rules — we surface disambiguation when available.  
- Voice quality depends on ElevenLabs quota/network; UI degrades gracefully without a key.  
- JWT in localStorage is demo-grade (httpOnly cookies are backlog).

---

## 9. Files to open if they want “show me the code”

- Pipeline entry: `vedya-ai/backend/main.py` (`/recommend`)  
- Ranker / safety: `vedya-ai/backend/pipeline/ranker.py`, `safety.py`  
- Locale explain: `vedya-ai/backend/pipeline/explainer.py`  
- Voice: `vedya-ai/backend/voice.py`  
- Product backlog: `feature-suggestion.md` / `vedya-ai/feature-suggestion.md`  
- Agent context: `vedya-ai/agent.md`

---

## 10. Closing line

“We don’t ask the model what to prescribe — we ask it to explain a ranking the classical structure and safety rules already decided.”
