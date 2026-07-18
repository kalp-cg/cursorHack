#!/usr/bin/env bash
# Run all data load scripts in order.
# Assumes PostgreSQL is running and DATABASE_URL is set (or defaults to localhost).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== VedyaAI Data Loader ==="
echo ""

echo "[1/6] Enriching formulations..."
python3 enrich_formulations.py

echo "[2/6] Loading synonyms..."
python3 load_synonyms.py

echo "[3/6] Loading herbs (dravyas + properties)..."
python3 load_herbs.py

echo "[4/6] Loading formulations (yogas + indications + ingredients)..."
python3 load_formulations.py

echo "[5/6] Loading constraint rules..."
python3 load_constraints.py

echo "[6/6] Loading sense rules..."
python3 load_sense_rules.py

echo "[7/7] Loading Charaka verses..."
python3 load_charaka.py

echo ""
echo "=== All loaders complete ==="
echo "To generate vector embeddings (requires OPENAI_API_KEY):"
echo "  python3 embed_verses.py"
