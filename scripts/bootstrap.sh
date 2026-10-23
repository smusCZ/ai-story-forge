#!/usr/bin/env bash
set -e

echo "=== AI Story Forge Bootstrap ==="

echo "→ Starting Docker services (db, redis, minio)..."
docker compose up -d db redis minio

echo "→ Waiting for Postgres..."
sleep 5

echo "→ Installing Python dependencies..."
cd apps/api
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -r requirements.txt

echo "→ Creating database schema..."
PYTHONPATH=. python ../../scripts/init_db.py

echo ""
echo "✅ Bootstrap complete."
echo "Run API with:"
echo "  cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Docs: http://localhost:8000/docs"
