# VedyaAI — How the AI / Decision Module Works

> Read this to understand what is *real logic* vs *demo UI*, and how a request becomes a ranked formulation.

---

## One-sentence truth

VedyaAI is **not** “ChatGPT over Ayurveda PDFs.”  
It is a **deterministic clinical discrimination pipeline** with optional LLM only for language understanding and explanation.

**Core principle:**

> **Structure decides → Rules protect → Retrieval grounds → LLM explains**

---

## Is it only demo data?

| Layer | Reality |
|-------|---------|
| Demo presets | Convenience shortcuts (Pinasa / Shotha / Diabetes) — same pipeline as free text |
| Knowledge base | Loaded classical structured data: yogas, indications, herbs, synonyms, constraint rules, sense rules |
| Ranking | Feature-weighted math — works with `LLM_ENABLED=false` (M3 gate) |
| Safety | Deterministic YAML/DB rules — never LLM |
| Explanation | LLM *or* template fallback; citations must come from retrieved refs |

So: presets are demos of *vignettes*, not fake answers. The engine is real.

---

## End-to-end request flow

```
User vignette (text / structured / follow-up)
        │
        ▼
1. Intake          validate_and_normalize()
        │
        ▼
2. Understand      free text → ClinicalFrame  (LLM optional)
        │
        ▼
3. Resolver        synonyms + sense rules → concept IDs
        │
        ▼
4. Retriever       SQL: yogas linked to those concepts
        │
        ▼
5. SafetyEngine    HARD_EXCLUDE / WARN (deterministic)
        │
        ▼
6. Ranker          weighted score (deterministic)
        │
        ▼
7. Evidence pack   refs + indications + ingredients
        │
        ▼
8. Explainer       LLM citation-bound OR templates
        │
        ▼
RecommendationResponse (+ optional conversation save)
```

**Key files**

| Step | Path |
|------|------|
| API entry | `backend/main.py` → `POST /recommend` |
| Intake | `backend/pipeline/intake.py` |
| NL understand | `backend/pipeline/understand.py` |
| Entity resolve | `backend/pipeline/resolver.py` |
| Retrieve | `backend/pipeline/retriever.py` |
| Safety | `backend/pipeline/safety.py` |
| Rank | `backend/pipeline/ranker.py` |
| Evidence | `backend/pipeline/evidence.py` |
| Explain | `backend/pipeline/explainer.py` |
| Auth | `backend/auth.py` |
| Conversations | `backend/conversations.py` |

---

## Ranking logic (the “AI brain” that is not an LLM)

From `ranker.py`:

```
score =
  W1 * primary_indication_match
+ W2 * secondary_indication_match
+ W3 * property_fit
+ W4 * citation_bonus
- W5 * contraindication_penalty
- W6 * medium_penalty
```

Default weights: `W1=3.0`, `W2=1.0`, `W3=0.5`, `W4=0.5`, `W5=5.0`, `W6=2.0`.

**Why Punarnavadi vs Vyaghryadi works without LLM**

- Both match Jvara + Kasa as primary.
- Vyaghryadi has stronger **secondary** weight for Pinasa / URTI-like tags.
- Punarnavadi has stronger secondary weight for Shotha / systemic inflammatory tags.
- Changing secondary context flips the ranking — that is discrimination, not search.

Acceptance gate (M3): Pinasa vignette ranks Vyaghryadi above Punarnavadi with LLM disabled.

---

## Safety logic (never LLM)

`SafetyEngine` loads `constraint_rules` from Postgres (seeded from `data/constraint_rules.yaml`).

Examples:

- Diabetes / Prameha × fermented media (Asava–Arishta) → HARD_EXCLUDE or WARN
- Sweetener / jaggery-class ingredients × diabetes → flagged

Safety runs **before** ranking presentation. Hard-excluded yogas are marked and filtered from “active” picks in the UI.

---

## Synonyms & homonyms

- Synonyms: surface string → `terms` → `concepts` → expand retrieval (e.g. Fever ↔ Jvara ↔ Santapa)
- Homonyms: `sense_rules` (e.g. Abhaya default vs Abhaya in Jatyadi context)

This is ontology logic, not embedding similarity.

---

## What the LLM is allowed to do

| Allowed | Forbidden |
|---------|-----------|
| Parse free-text vignette into structured frame | Invent formulations |
| Write teaching explanation from evidence pack | Invent classical citations |
| Polish compare narrative from packs | Override safety rules |
| | Fill missing Rasa/Guna/Virya into DB |

If `OPENAI_API_KEY` missing or `LLM_ENABLED=false`, ranking + safety still work; explanations use templates.

---

## Conversations (continuity)

When a user is logged in:

1. First `/recommend` creates a `conversations` row + user message.
2. Follow-up sends `follow_up=true` + `conversation_id`.
3. Prior user turns are merged into context text for re-ranking.
4. Assistant message stores summary + full JSON payload for “My cases”.

Guests can rank; they cannot persist follow-up history.

---

## Auth (not the clinical AI, but part of the product)

- Passwords: **bcrypt** (passlib)
- Session: **JWT** (PyJWT HS256), `Authorization: Bearer …`
- See `SECURITY.md`

---

## How to verify the module yourself

```bash
# Health + corpus counts
curl http://localhost:8000/health

# Deterministic demo (no LLM required)
curl http://localhost:8000/presets/pinasa_urti
# Expect top ≈ Vyaghryadi Kashayam

curl http://localhost:8000/presets/inflammatory_shotha
# Expect Punarnavadi to rise

curl http://localhost:8000/presets/diabetic_respiratory
# Expect safety alerts on fermented / sweetener rules
```

Eval harness (gates): `backend/eval/run_eval.py` with `--gate M3|M4|M5`.

---

## Mental model for judges / teammates

> “We don’t return ten decoctions for fever. We show why one fits this patient context better than another — with classical citations and safety gates. The LLM narrates; the ranker and rules decide.”
