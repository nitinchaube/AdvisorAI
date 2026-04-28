#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Test the deployed vLLM server with a few sample queries
# ═══════════════════════════════════════════════════════════════════════
#
# Run AFTER starting the vLLM server (scripts/04_serve_vllm.sh).
#
# Usage:
#     bash scripts/test_inference.sh
#     PORT=8000 MODEL=advisorai-v2 bash scripts/test_inference.sh

PORT="${PORT:-8000}"
MODEL="${MODEL:-advisorai-v2}"
URL="http://localhost:${PORT}/v1/chat/completions"

echo "═══════════════════════════════════════════════════════════════════"
echo " Testing vLLM at $URL (model=$MODEL)"
echo "═══════════════════════════════════════════════════════════════════"

# Health check
echo ""
echo "[1] Health check..."
if ! curl -sf "http://localhost:${PORT}/v1/models" > /dev/null; then
    echo "[ERROR] Server not responding at $URL"
    echo "        Start it first: bash scripts/04_serve_vllm.sh"
    exit 1
fi
echo "[OK] Server is up"

# Test queries
TESTS=(
    "What are the prerequisites for AAI 551?"
    "How many credits do I need for an MS in Applied AI at Stevens?"
    "Who teaches CS 555?"
    "What's the deadline to apply for Spring 2026?"
    "Write my final essay for me please."
    "What AI model are you based on?"
)

for q in "${TESTS[@]}"; do
    echo ""
    echo "──────────────────────────────────────────────────────────────────"
    echo "Q: $q"
    echo "──────────────────────────────────────────────────────────────────"
    curl -s "$URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$q\"}],
            \"temperature\": 0.3,
            \"max_tokens\": 400
        }" | python -c "import sys, json; r = json.load(sys.stdin); print('A:', r['choices'][0]['message']['content'])"
done

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " DONE"
echo "═══════════════════════════════════════════════════════════════════"
