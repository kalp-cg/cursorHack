#!/usr/bin/env bash
# =============================================================================
# VedyaAI — Granular Git Commit & Push Script
# Run from the repo root: /home/kalppatel/Desktop/cursorHack
# Makes 50+ meaningful commits (one per logical unit) then pushes to GitHub.
# =============================================================================
set -euo pipefail

# Always work from the git repo root (parent of vedya-ai/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "================================================================"
echo "  VedyaAI — Git Commit + Push"
echo "  Repo root : $REPO_ROOT"
echo "  Remote    : $(git remote get-url origin)"
echo "================================================================"
echo ""

# ── helpers ───────────────────────────────────────────────────────────────────
commit() {
  local msg="$1"
  shift
  local files=()
  for f in "$@"; do
    if [ -e "$f" ]; then
      files+=("$f")
    fi
  done
  if [ ${#files[@]} -eq 0 ]; then
    echo "  [skip] no files: $msg"
    return
  fi
  git add "${files[@]}"
  if git diff --cached --quiet; then
    echo "  [skip] nothing new: $msg"
    return
  fi
  git commit -m "$msg"
  echo "  ✓ $msg"
}

# ─────────────────────────────────────────────────────────────────────────────
# ROOT CONFIG
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ Root config"
commit "chore: add .env.example (DATABASE_URL, OPENAI_API_KEY, LLM_ENABLED template)" \
  vedya-ai/.env.example

commit "chore: add docker-compose.yml — postgres+pgvector, FastAPI, Next.js services" \
  vedya-ai/docker-compose.yml

commit "docs: add README — quick-start, architecture, milestone gates M3/M4/M5/M6" \
  vedya-ai/README.md

commit "chore: add git_push_all.sh — granular 50+ commit + push script" \
  vedya-ai/git_push_all.sh

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 0 — DATA ENRICHMENT
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 0 — Data enrichment"

commit "data(raw): add formulations_bhaishajya.json — 178 Ayurvedic formulations" \
  vedya-ai/data/raw/formulations_bhaishajya.json

commit "data(raw): add herbs_amidha.json — 360 herbs with rasa/guna/virya/vipaka/prabhav" \
  vedya-ai/data/raw/herbs_amidha.json

commit "data(raw): add Charaka Samhita Sutrasthana — all 42 chapter JSON files" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/1.Sutrasthana (Sutra Sthana) — General Principles"

commit "data(raw): add Charaka Samhita Nidanasthana — 8 pathology chapters" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/2.Nidanasthana (Nidana Sthana) — Section on Pathology"

commit "data(raw): add Charaka Samhita Vimanasthana, Sharirasthana, Indriyasthana" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/3.Vimanasthana (Vimana Sthana) — Section on Measure" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/4.Sharirasthana (Sarira Sthana) — Section on Physiology" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/5.Indriyasthana (Indriya Sthana) — Section on Prognosis"

commit "data(raw): add Charaka Samhita Cikitsasthana — 30 therapeutics chapters" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/6.Cikitsasthana (Cikitsa Sthana) — Section on Therapeutics"

commit "data(raw): add Charaka Samhita Kalpasthana + Siddhisthana" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/7.Kalpasthana (Kalpa Sthana) — Section on Pharmaceutics" \
  "vedya-ai/data/raw/Ayurveda/charak-samhita/8.Siddhisthana (Siddhi Sthana) — Section on Successful Treatment"

commit "feat(phase0a): enrich_formulations.py — DISEASE_DICT + herb cross-reference → symptom_tags 178/178" \
  vedya-ai/scripts/enrich_formulations.py

commit "feat(phase0b): synonyms.yaml — 38 canonical concepts (Jvara, Kasa, Pinasa, Prameha, Shotha…)" \
  vedya-ai/data/synonyms.yaml

commit "feat(phase0c): constraint_rules.yaml — CR-01 Prameha×Asava, CR-02 Prameha×Guda, CR-04 Garbhini×purgatives" \
  vedya-ai/data/constraint_rules.yaml

commit "feat(phase0d): sense_rules.yaml — Abhaya homonym (Jatyadi Ghrita → Vetiveria zizanioides)" \
  vedya-ai/data/sense_rules.yaml

commit "data(enriched): add formulations_enriched.json — 178/178 tagged, Pinasa discriminator active" \
  vedya-ai/data/enriched/formulations_enriched.json

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — DATABASE
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 1 — Database schema + loaders"

commit "feat(phase1): schema.sql — concepts + terms ontology tables" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1): schema.sql — dravyas + property_sets (360 herbs)" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1): schema.sql — kalpanas + yogas + yoga_indications (primary/secondary)" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1): schema.sql — yoga_ingredients + yoga_references + references" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1): schema.sql — verse_embeddings (pgvector 1536), constraint_rules, sense_rules" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1): schema.sql — recommendation_traces audit table + yoga_detail view" \
  vedya-ai/backend/db/schema.sql

commit "feat(phase1-load): db_utils.py — shared psycopg2 helpers (upsert_concept, upsert_term)" \
  vedya-ai/scripts/db_utils.py

commit "feat(phase1-load): load_synonyms.py — import 38 canonical disease concepts + synonym terms" \
  vedya-ai/scripts/load_synonyms.py

commit "feat(phase1-load): load_herbs.py — 360 dravyas + property_sets + sanskrit synonyms" \
  vedya-ai/scripts/load_herbs.py

commit "feat(phase1-load): load_formulations.py — 178 yogas + kalpana detection + indications + ingredients" \
  vedya-ai/scripts/load_formulations.py

commit "feat(phase1-load): load_constraints.py — CR-01…CR-10 safety rules from YAML into postgres" \
  vedya-ai/scripts/load_constraints.py

commit "feat(phase1-load): load_sense_rules.py — Abhaya + 6 other homonym rules into sense_rules table" \
  vedya-ai/scripts/load_sense_rules.py

commit "feat(phase1-load): load_charaka.py — batch insert 8215 Charaka verses from 142 chapter JSONs" \
  vedya-ai/scripts/load_charaka.py

commit "feat(phase1-load): embed_verses.py — OpenAI text-embedding-3-small → pgvector verse_embeddings" \
  vedya-ai/scripts/embed_verses.py

commit "feat(phase1-load): run_all_loaders.sh — master 7-step loader script with ordering" \
  vedya-ai/scripts/run_all_loaders.sh

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — BACKEND
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 2 — FastAPI backend pipeline"

commit "feat(phase2): backend/requirements.txt — FastAPI, psycopg2, pydantic, openai, uvicorn" \
  vedya-ai/backend/requirements.txt

commit "feat(phase2): models/schemas.py — VignetteInput, ClinicalFrame, RankFeatures, SafetyViolation, RecommendationResponse" \
  vedya-ai/backend/models/__init__.py \
  vedya-ai/backend/models/schemas.py

commit "feat(phase2-intake): pipeline/intake.py — normalize vignette + 3 demo presets (Pinasa, Shotha, Prameha)" \
  vedya-ai/backend/pipeline/__init__.py \
  vedya-ai/backend/pipeline/intake.py

commit "feat(phase2-understand): pipeline/understand.py — LLM→ClinicalFrame with structured fallback" \
  vedya-ai/backend/pipeline/understand.py

commit "feat(phase2-resolver): pipeline/resolver.py — term→concept expansion + sense rule disambiguation" \
  vedya-ai/backend/pipeline/resolver.py

commit "feat(phase2-retriever): pipeline/retriever.py — SQL yoga_indications candidate retrieval with ingredient data" \
  vedya-ai/backend/pipeline/retriever.py

commit "feat(phase2-safety): pipeline/safety.py — DETERMINISTIC constraint engine (HARD_EXCLUDE / WARN, no LLM)" \
  vedya-ai/backend/pipeline/safety.py

commit "feat(phase2-ranker): pipeline/ranker.py — W1=3×primary + W2=1×secondary − W5=5×penalty (M3 gate live)" \
  vedya-ai/backend/pipeline/ranker.py

commit "feat(phase2-evidence): pipeline/evidence.py — evidence pack builder with herb property aggregation" \
  vedya-ai/backend/pipeline/evidence.py

commit "feat(phase2-explainer): pipeline/explainer.py — citation-bound LLM explanation + template fallback" \
  vedya-ai/backend/pipeline/explainer.py

commit "feat(phase2-api): main.py — FastAPI lifespan, POST /recommend, GET /presets, POST /compare, GET /health" \
  vedya-ai/backend/main.py

commit "feat(phase2-api): backend Dockerfile — python:3.11-slim, uvicorn ASGI server" \
  vedya-ai/backend/Dockerfile

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — EVAL
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 2 — Eval harness"

commit "feat(phase2-eval): golden_vignettes.json — 27 cases (pairwise, safety, synonym, recall, citation)" \
  vedya-ai/backend/eval/__init__.py \
  vedya-ai/backend/eval/golden_vignettes.json

commit "feat(phase2-eval): GV-01/02 pairwise — Pinasa→Vyaghryadi, Shotha→Punarnavadi discrimination" \
  vedya-ai/backend/eval/golden_vignettes.json

commit "feat(phase2-eval): GV-03/04 safety gates — Prameha×Asava CR-01, Garbhini×purgatives CR-04" \
  vedya-ai/backend/eval/golden_vignettes.json

commit "feat(phase2-eval): GV-05/06 synonym retrieval — Santapa→Jvara, Pratishyaya→Pinasa" \
  vedya-ai/backend/eval/golden_vignettes.json

commit "feat(phase2-eval): GV-17 wound healing — Jatyadi Ghrita in recall; GV-27 citation validity" \
  vedya-ai/backend/eval/golden_vignettes.json

commit "feat(phase2-eval): run_eval.py — M3/M4/M5 gate harness, --gate flag, pairwise + safety + recall checks" \
  vedya-ai/backend/eval/run_eval.py

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — FRONTEND
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 3 — Next.js frontend"

commit "feat(phase3-tokens): tokens.css — §17.10 exact: shila/ink/harita/agni/kesar/tamra + font vars" \
  vedya-ai/frontend/src/styles/tokens.css

commit "feat(phase3-layout): globals.css (import tokens) + layout.tsx (DisclaimerBar in root)" \
  vedya-ai/frontend/src/app/globals.css \
  vedya-ai/frontend/src/app/layout.tsx

commit "feat(phase3-api): lib/api.ts — typed API client (recommend, presets, compare, formulation, synonymMap)" \
  vedya-ai/frontend/src/lib/api.ts

commit "feat(phase3-ui): DisclaimerBar — always-visible educational disclaimer in footer" \
  vedya-ai/frontend/src/components/DisclaimerBar.tsx

commit "feat(phase3-ui): PrimaryButton — harita CTA + outline variant, accessible focus ring" \
  vedya-ai/frontend/src/components/PrimaryButton.tsx

commit "feat(phase3-ui): SafetyDot — semantic agni/kesar/harita dot (hard/warn/safe)" \
  vedya-ai/frontend/src/components/SafetyDot.tsx

commit "feat(phase3-ui): SafetyPanel — agni-wash panel with HARD_EXCLUDE + WARN violation display" \
  vedya-ai/frontend/src/components/SafetyPanel.tsx

commit "feat(phase3-ui): TermChip — resolved (harita) + unresolved (kesar) with canonical display" \
  vedya-ai/frontend/src/components/TermChip.tsx

commit "feat(phase3-ui): CaseChip — sticky vignette summary + comorbidity badges" \
  vedya-ai/frontend/src/components/CaseChip.tsx

commit "feat(phase3-ui): CoverageNote — honest dashed-border corpus gap indicator" \
  vedya-ai/frontend/src/components/CoverageNote.tsx

commit "feat(phase3-ui): CitationCard — tamra-accented classical reference with excerpt" \
  vedya-ai/frontend/src/components/CitationCard.tsx

commit "feat(phase3-ui): RankRow — score bar + compare toggle + safety dot + hard-excluded dim" \
  vedya-ai/frontend/src/components/RankRow.tsx

commit "feat(phase3-ui): CompareTable — feature-aligned rows (primary, secondary, safety, score, citations)" \
  vedya-ai/frontend/src/components/CompareTable.tsx

commit "feat(phase3-screen): Home page — dark mineral hero, Fraunces wordmark, 3 preset tiles, quick input" \
  vedya-ai/frontend/src/app/page.tsx

commit "feat(phase3-screen): Results page — SafetyPanel→TopPick→CompareTeaser→RankList + IntakePanel" \
  vedya-ai/frontend/src/app/results/page.tsx

commit "feat(phase3-screen): Compare page — A|B discrimination, winner harita highlight, features table" \
  vedya-ai/frontend/src/app/compare/page.tsx

commit "feat(phase3-screen): Detail page — PropertyGrid null→Not in corpus, ambiguity notes, CitationCards" \
  "vedya-ai/frontend/src/app/detail/[id]/page.tsx"

commit "feat(phase3-screen): Learn page — synonym map search, teaching point, quick-links palette" \
  vedya-ai/frontend/src/app/learn/page.tsx

commit "feat(phase3): frontend Dockerfile — node:20-alpine multi-stage, standalone Next.js build" \
  vedya-ai/frontend/Dockerfile

commit "chore(frontend): next.config.ts, package.json, tsconfig, postcss, eslint" \
  vedya-ai/frontend/next.config.ts \
  vedya-ai/frontend/package.json \
  vedya-ai/frontend/tsconfig.json \
  vedya-ai/frontend/postcss.config.mjs \
  vedya-ai/frontend/eslint.config.mjs

commit "chore(frontend): package-lock.json lockfile" \
  vedya-ai/frontend/package-lock.json

commit "chore(frontend): public assets (SVG icons)" \
  vedya-ai/frontend/public

commit "chore(frontend): .gitignore, AGENTS.md, CLAUDE.md" \
  vedya-ai/frontend/.gitignore \
  vedya-ai/frontend/AGENTS.md \
  vedya-ai/frontend/CLAUDE.md \
  vedya-ai/frontend/README.md

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — INTEGRATION / FALLBACKS
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Phase 4 — Integration + precomputed fallbacks"

commit "feat(phase4): precomputed/pinasa_urti.json — Vyaghryadi #1, Pinasa demo golden response" \
  vedya-ai/backend/precomputed/pinasa_urti.json

commit "feat(phase4): precomputed/inflammatory_shotha.json — Punarnavadi #1, Shotha demo (reverse discriminator)" \
  vedya-ai/backend/precomputed/inflammatory_shotha.json

commit "feat(phase4): precomputed/diabetic_respiratory.json — safety gates CR-01/CR-02 demo response" \
  vedya-ai/backend/precomputed/diabetic_respiratory.json

# ─────────────────────────────────────────────────────────────────────────────
# CATCH ALL REMAINING
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Final sweep — remaining files"

# Exclude nested git repos and cache dirs
git add \
  vedya-ai/ \
  --ignore-errors 2>/dev/null || true

# Remove pycache and other noise from staging
git restore --staged \
  "vedya-ai/backend/__pycache__" \
  "vedya-ai/backend/models/__pycache__" \
  "vedya-ai/backend/pipeline/__pycache__" \
  "vedya-ai/scripts/__pycache__" \
  2>/dev/null || true

if ! git diff --cached --quiet; then
  git commit -m "chore: sweep remaining project files (favicon, lock files, misc config)"
  echo "  ✓ swept remaining files"
fi

# ─────────────────────────────────────────────────────────────────────────────
# PUSH
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Pushing to origin/main…"
git push origin main

echo ""
echo "================================================================"
TOTAL=$(git rev-list HEAD --count)
NEW=$(git log --oneline origin/main@{1}..HEAD 2>/dev/null | wc -l || echo "many")
echo "  ✓ Push complete!"
echo "  Remote: $(git remote get-url origin)"
echo "  Total commits on branch : $TOTAL"
echo "  New commits this run    : $NEW"
echo ""
echo "  Recent commits:"
git log --oneline -20
echo "================================================================"
