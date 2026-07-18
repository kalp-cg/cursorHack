# VedyaAI

**Classical Ayurvedic Formulation Discrimination & Learning Platform**

> Educational decision support — not a diagnosis or prescription. Clinical judgment of a qualified vaidya is required.

| | |
|---|---|
| **Live app** | [https://cursor-hack-gamma.vercel.app/](https://cursor-hack-gamma.vercel.app/) |
| **API docs** | `https://<your-api-host>/docs` |
| **Database** | Neon Postgres (seeded: ~177 yogas · ~720 herbs · ~8.5k Charaka verses) |
| **Stack** | Next.js · FastAPI · Neon Postgres · (optional) OpenAI / ElevenLabs |

---

## What it does

When two formulations both list **Jvara** and **Kasa**, which one fits *this* patient?

VedyaAI ranks classical yogas by secondary indications, deterministic safety gates, and citation-bound explanations — so students and practitioners get **discrimination**, not another undifferentiated list.

```mermaid
flowchart LR
  A[Patient vignette] --> B[Entity resolve]
  B --> C[Candidate retrieve]
  C --> D[Safety gates]
  D --> E[Feature ranker]
  E --> F[Evidence pack]
  F --> G[Explainer]
  G --> H[Top yoga + why]
```

**Core principle:** Structure decides → Rules protect → Retrieval grounds → LLM explains.

---

## Live demo

1. Open **[cursor-hack-gamma.vercel.app](https://cursor-hack-gamma.vercel.app/)**
2. Click **Try the Pinasa case** (fever + cough + common cold)
3. Expect **Vyaghryadi** over **Punarnavadi** — secondary indication (Pinasa) decides
4. Compare top-2, ask follow-ups (sign in), or open **Ask the Texts** for Charaka-grounded Q&A

| Teaching case | Clinical idea | Expected discrimination |
|---------------|---------------|-------------------------|
| Pinasa URTI | Jvara + Kasa + Pinasa | Vyaghryadi > Punarnavadi |
| Inflammatory Shotha | Jvara + Kasa + Shotha | Punarnavadi > Vyaghryadi |
| Diabetic respiratory | Diabetes + fever/cough | Asava / Guda safety flags |

---

## Architecture

### Request pipeline

```mermaid
flowchart TB
  subgraph Client
    UI[Next.js app]
  end

  subgraph API["FastAPI backend"]
    REC["/recommend"]
    ASK["/ask RAG"]
    AUTH["/auth"]
    VOICE["/voice TTS·STT"]
  end

  subgraph Data["Neon Postgres"]
    Y[yogas · indications · ingredients]
    H[dravyas · property_sets]
    R[references · FTS]
    C[constraint_rules · sense_rules]
    U[users · conversations]
  end

  UI --> REC & ASK & AUTH & VOICE
  REC --> Y & H & C
  ASK --> R
  AUTH --> U
```

### Ranker decision flow

```mermaid
sequenceDiagram
  participant U as User
  participant API as FastAPI
  participant DB as Neon
  participant S as SafetyEngine
  participant Rank as Ranker
  participant X as Explainer

  U->>API: vignette (text / preset / voice)
  API->>DB: resolve terms + retrieve candidates
  API->>S: apply CR-01…CR-10 (deterministic)
  S-->>API: exclude / warn
  API->>Rank: score primary · secondary · properties
  Rank-->>API: ordered yogas
  API->>DB: build evidence pack + citations
  API->>X: template or LLM (citation-bound)
  X-->>U: RecommendationResponse
```

### Safety vs LLM

```mermaid
flowchart LR
  V[Vignette] --> R[Ranker scores]
  V --> S{Safety rules}
  S -->|hard exclude| X[Removed from list]
  S -->|warn| W[Shown with alert]
  R --> L[LLM / template explain]
  L -.->|cannot override| S
```

---

## Repository layout

```
vedya-ai/
├── frontend/          # Next.js (EN + Gujarati)
├── backend/           # FastAPI pipeline + auth + RAG + voice
│   ├── db/schema.sql
│   ├── db/auth_schema.sql
│   └── tests/test_golden.py
├── scripts/           # Data loaders → Postgres
├── data/              # Raw JSON/YAML + corpus.json
├── docker-compose.yml
└── .env.example
```

---

## Data sources (seeded into Neon)

| Source | What loads |
|--------|------------|
| `data/raw/formulations_bhaishajya.json` | ~177 yogas + indications + ingredients |
| `data/raw/herbs_amidha.json` | ~720 herbs + rasa/guna/virya/vipaka |
| `data/raw/Ayurveda/charak-samhita/` | Charaka verses for FTS / Ask |
| `data/synonyms.yaml` | Disease / symptom synonyms |
| `data/constraint_rules.yaml` | Safety rules (diabetes, pregnancy, …) |
| `data/sense_rules.yaml` | Homonyms (e.g. Abhaya in Jatyadi) |
| `scripts/build_corpus.py` | Unified `data/corpus.json` for RAG |

---

## Environment

Copy `.env.example` → `.env`:

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Neon (or local Docker) Postgres URL |
| `JWT_SECRET` | Auth signing key (**required** in production) |
| `FRONTEND_ORIGINS` | CORS allowlist, e.g. `https://cursor-hack-gamma.vercel.app` |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend build |
| `LLM_ENABLED` / `OPENAI_API_KEY` | Optional narration |
| `ELEVENLABS_*` | Optional voice |
| `SMTP_USER` / `SMTP_PASS` | Gmail app password for forgot-password email |

**Neon:** create a project, copy the connection string (use `sslmode=require`). Prefer the **pooler** URL for the API; the app sets `search_path=public` on each checkout. Do **not** commit credentials — keep them in `.env` / host secrets only.

```bash
# Example shape (replace with your Neon URL)
DATABASE_URL=postgresql://USER:PASSWORD@ep-….neon.tech/neondb?sslmode=require
FRONTEND_ORIGINS=https://cursor-hack-gamma.vercel.app
```

### Seeded demo admin

| Email | Password | Role |
|-------|----------|------|
| `kalp@gmail.com` | `12345678` | admin |

---

## Seed Neon (or any Postgres)

```bash
# 1) Apply schemas
psql "$DATABASE_URL" -f backend/db/schema.sql
psql "$DATABASE_URL" -f backend/db/auth_schema.sql

# 2) Load clinical corpus
cd scripts
DATABASE_URL="$DATABASE_URL" bash run_all_loaders.sh
# Optional unified RAG upsert:
DATABASE_URL="$DATABASE_URL" python3 build_corpus.py --load

# 3) Seed admin (example)
# email: kalp@gmail.com  password: 12345678  role: admin
```

Admin seed (one-shot Python from `backend/`):

```bash
cd backend
DATABASE_URL="$DATABASE_URL" .venv/bin/python - <<'PY'
from auth import hash_password
from db_utils import get_connection  # or psycopg2 + DATABASE_URL
import os, psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(
  """INSERT INTO users (email, password_hash, display_name, preferred_locale, role)
     VALUES (%s,%s,%s,'en','admin')
     ON CONFLICT (email) DO UPDATE
       SET password_hash = EXCLUDED.password_hash, role = 'admin', is_active = TRUE""",
  ("kalp@gmail.com", hash_password("12345678"), "Kalp"),
)
conn.commit()
print("admin ready: kalp@gmail.com")
PY
```

---

## Local development

### Docker (all services)

```bash
cp .env.example .env
docker compose up -d
# Postgres: localhost:5433  · API: :8000  · Web: :3000

cd scripts
DATABASE_URL=postgresql://vedya:vedyapass@localhost:5433/vedyaai bash run_all_loaders.sh
```

### Backend only

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=...   # Neon or local
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Golden tests

```bash
cd backend
API_BASE=http://localhost:8000 pytest tests/test_golden.py -q
```

---

## Deploy map

```mermaid
flowchart LR
  Browser --> Vercel["Vercel frontend<br/>cursor-hack-gamma.vercel.app"]
  Vercel --> API["FastAPI host<br/>Railway / Render / Fly / …"]
  API --> Neon[(Neon Postgres)]
  API --> SMTP[Gmail SMTP]
  API --> EL[ElevenLabs optional]
```

1. **Frontend (Vercel)** — set `NEXT_PUBLIC_API_URL` to your public API
2. **Backend** — set `DATABASE_URL` (Neon), `JWT_SECRET`, `FRONTEND_ORIGINS=https://cursor-hack-green.vercel.app,https://cursor-hack-gamma.vercel.app`, SMTP / voice keys as needed
3. **Neon** — run schema + loaders once (see Seed above)

---

## Product surfaces

| Route | Purpose |
|-------|---------|
| `/` | Presets + free-text / voice vignette |
| `/results` | Ranked yogas, safety, compare, follow-up |
| `/compare` | A vs B with evidence |
| `/ask` | Charaka FTS + citation-bound answers |
| `/learn` | Synonyms / sense demos |
| `/login` · `/signup` · `/forgot-password` | Auth + email reset |
| `/admin` | Faculty stats (admin role) |

---

## Eval gates

| Gate | Criterion |
|------|-----------|
| M3 | Pinasa ranks Vyaghryadi > Punarnavadi with `LLM_ENABLED=false` |
| M4 | 100% safety catch on golden cases |
| M5 | 0 fabricated citations in top explanations |
| M6 | Presets one-click; guest + signed-in journeys work |

```bash
cd backend
LLM_ENABLED=false DATABASE_URL=... python3 eval/run_eval.py --gate M3
```

---

## License & disclaimer

Educational / research prototype for classical formulation discrimination.

**Not** a medical device. **Not** a diagnosis or prescription.
