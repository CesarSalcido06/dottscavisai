#!/bin/bash
# Start DottscavisAI

cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load config
if [ -f "config/settings.json" ]; then
    export BENCHAI_URL=$(python3 -c "import json; print(json.load(open('config/settings.json')).get('benchai_url', 'http://benchai.local:8085'))")
fi

echo "=== Starting DottscavisAI ==="
echo "BenchAI URL: ${BENCHAI_URL:-http://benchai.local:8085}"
echo ""

# Start router
python3 router/creative_router.py
