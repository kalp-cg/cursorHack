#!/usr/bin/env bash
# VedyaAI — Linux/macOS one-shot launcher
# Checks deps, installs packages, starts Postgres + FastAPI backend + Next.js frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
DATABASE_URL="${DATABASE_URL:-postgresql://vedya:vedyapass@localhost:5432/vedyaai}"
LLM_ENABLED="${LLM_ENABLED:-false}"
SKIP_DATA_LOAD="${SKIP_DATA_LOAD:-false}"
PID_DIR="$ROOT/.run"
LOG_DIR="$ROOT/.run/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[VedyaAI]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

require_cmd() {
  local name="$1"
  local hint="${2:-}"
  if command -v "$name" >/dev/null 2>&1; then
    ok "$name found: $($name --version 2>&1 | head -n1)"
  else
    fail "Missing required command: $name${hint:+ — $hint}"
  fi
}

cleanup() {
  info "Stopping services..."
  if [[ -f "$PID_DIR/backend.pid" ]]; then
    kill "$(cat "$PID_DIR/backend.pid")" 2>/dev/null || true
    rm -f "$PID_DIR/backend.pid"
  fi
  if [[ -f "$PID_DIR/frontend.pid" ]]; then
    kill "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null || true
    rm -f "$PID_DIR/frontend.pid"
  fi
}

trap cleanup EXIT INT TERM

echo ""
echo "========================================"
echo "  VedyaAI — Local Dev Launcher (Unix)"
echo "========================================"
echo ""

# ── 1. Prerequisite checks ──────────────────────────
info "Cross-verifying system dependencies..."
require_cmd python3 "Install Python 3.11+"
require_cmd node "Install Node.js 20+"
require_cmd npm "Install npm (bundled with Node.js)"
require_cmd docker "Install Docker Desktop / Engine"

if docker compose version >/dev/null 2>&1; then
  ok "docker compose found"
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  ok "docker-compose found"
  COMPOSE=(docker-compose)
else
  fail "Neither 'docker compose' nor 'docker-compose' is available"
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10 ) ]]; then
  fail "Python 3.10+ required (found ${PY_MAJOR}.${PY_MINOR})"
fi
ok "Python version OK (${PY_MAJOR}.${PY_MINOR})"

NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]")
if [[ "$NODE_MAJOR" -lt 18 ]]; then
  fail "Node.js 18+ required (found v$(node -v))"
fi
ok "Node.js version OK (v$(node -v | sed 's/^v//'))"

# ── 2. Environment file ─────────────────────────────
if [[ ! -f "$ROOT/.env" ]]; then
  if [[ -f "$ROOT/.env.example" ]]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
    warn "Created .env from .env.example — edit OPENAI_API_KEY if you want LLM explanations"
  else
    fail ".env.example missing"
  fi
else
  ok ".env present"
fi

# Load .env (simple KEY=VALUE lines)
set -a
# shellcheck disable=SC1091
source "$ROOT/.env" 2>/dev/null || true
set +a
export DATABASE_URL="${DATABASE_URL:-postgresql://vedya:vedyapass@localhost:5432/vedyaai}"
export LLM_ENABLED="${LLM_ENABLED:-false}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
export CORPUS_VERSION="${CORPUS_VERSION:-1.0.0}"

# ── 3. Postgres via Docker ───────────────────────────
info "Starting PostgreSQL (pgvector)..."
"${COMPOSE[@]}" up -d postgres

info "Waiting for Postgres to become healthy..."
for i in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T postgres pg_isready -U vedya -d vedyaai >/dev/null 2>&1; then
    ok "Postgres is ready"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    fail "Postgres did not become ready in time"
  fi
  sleep 1
done

# ── 4. Python virtualenv + backend deps ──────────────
info "Setting up Python backend environment..."
VENV="$ROOT/backend/.venv"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
  ok "Created virtualenv at backend/.venv"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

pip install --upgrade pip >/dev/null
info "Installing / verifying backend requirements..."
pip install -r "$ROOT/backend/requirements.txt"

info "Cross-verifying Python packages..."
python3 - <<'PY'
import importlib, sys
required = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("psycopg2", "psycopg2"),
    ("pydantic", "pydantic"),
    ("dotenv", "python-dotenv"),
    ("yaml", "PyYAML"),
    ("httpx", "httpx"),
    ("openai", "openai"),
]
missing = []
for mod, pkg in required:
    try:
        importlib.import_module(mod)
        print(f"  ✓ {pkg}")
    except ImportError:
        missing.append(pkg)
        print(f"  ✗ {pkg}")
if missing:
    print(f"Missing: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)
print("All backend packages verified.")
PY
ok "Backend dependencies verified"

# ── 5. Frontend deps ────────────────────────────────
info "Installing / verifying frontend packages..."
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
else
  npm install --prefer-offline
fi

info "Cross-verifying Node packages..."
node - <<'JS'
const required = ["next", "react", "react-dom", "framer-motion", "lucide-react"];
let ok = true;
for (const name of required) {
  try {
    require.resolve(name);
    console.log(`  ✓ ${name}`);
  } catch {
    console.log(`  ✗ ${name}`);
    ok = false;
  }
}
if (!ok) process.exit(1);
console.log("All frontend packages verified.");
JS
ok "Frontend dependencies verified"
cd "$ROOT"

# ── 6. Seed data if empty ────────────────────────────
if [[ "$SKIP_DATA_LOAD" != "true" ]]; then
  info "Checking whether knowledge base is loaded..."
  YOGA_COUNT=$(python3 - <<PY
import os, psycopg2
try:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM yogas")
    print(cur.fetchone()[0])
    conn.close()
except Exception as e:
    print(-1)
PY
)
  if [[ "$YOGA_COUNT" == "-1" ]]; then
    warn "Could not query yogas table (schema may still be initializing). Retrying shortly..."
    sleep 3
    YOGA_COUNT=$(python3 -c 'import os,psycopg2; c=psycopg2.connect(os.environ["DATABASE_URL"]); cur=c.cursor(); cur.execute("SELECT COUNT(*) FROM yogas"); print(cur.fetchone()[0]); c.close()' 2>/dev/null || echo 0)
  fi

  if [[ "${YOGA_COUNT:-0}" -lt 1 ]]; then
    info "Database empty — running data loaders (this may take a few minutes)..."
    cd "$ROOT/scripts"
    python3 enrich_formulations.py
    python3 load_synonyms.py
    python3 load_herbs.py
    python3 load_formulations.py
    python3 load_constraints.py
    python3 load_sense_rules.py
    python3 load_charaka.py
    cd "$ROOT"
    ok "Data load complete"
  else
    ok "Knowledge base already loaded ($YOGA_COUNT yogas)"
  fi
else
  warn "Skipping data load (SKIP_DATA_LOAD=true)"
fi

# ── 7. Start backend ─────────────────────────────────
info "Starting FastAPI backend on :$BACKEND_PORT ..."
cd "$ROOT/backend"
nohup uvicorn main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" \
  >"$LOG_DIR/backend.log" 2>&1 &
echo $! > "$PID_DIR/backend.pid"
cd "$ROOT"

# ── 8. Start frontend ────────────────────────────────
info "Starting Next.js frontend on :$FRONTEND_PORT ..."
cd "$ROOT/frontend"
nohup npm run dev -- --port "$FRONTEND_PORT" \
  >"$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$PID_DIR/frontend.pid"
cd "$ROOT"

# ── 9. Wait for health ───────────────────────────────
info "Waiting for backend health..."
for i in $(seq 1 45); do
  if curl -sf "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
    ok "Backend healthy"
    break
  fi
  if [[ "$i" -eq 45 ]]; then
    warn "Backend health check timed out — see $LOG_DIR/backend.log"
  fi
  sleep 1
done

info "Waiting for frontend..."
for i in $(seq 1 60); do
  if curl -sf "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
    ok "Frontend responding"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    warn "Frontend not responding yet — see $LOG_DIR/frontend.log"
  fi
  sleep 1
done

echo ""
echo "========================================"
echo "  VedyaAI is running"
echo "========================================"
echo "  App:      http://localhost:$FRONTEND_PORT"
echo "  API:      http://localhost:$BACKEND_PORT"
echo "  API docs: http://localhost:$BACKEND_PORT/docs"
echo "  Logs:     $LOG_DIR/"
echo ""
echo "  Press Ctrl+C to stop backend + frontend"
echo "  (Postgres container stays up — stop with: docker compose stop postgres)"
echo "========================================"
echo ""

# Keep script alive so trap can clean up children
wait
