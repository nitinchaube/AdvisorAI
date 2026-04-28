#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Serve the fine-tuned model with vLLM (OpenAI-compatible API)
# ═══════════════════════════════════════════════════════════════════════
#
# Starts vLLM's OpenAI-compatible server on port 8000.
# Uses the AWQ-quantized 14B model (~9 GB VRAM on one 3090).
#
# Usage:
#     bash scripts/04_serve_vllm.sh
#
# Test from another terminal:
#     curl http://localhost:8000/v1/chat/completions \
#         -H "Content-Type: application/json" \
#         -d '{
#             "model": "advisorai-v2",
#             "messages": [{"role":"user","content":"What is AAI 551?"}]
#         }'

set -e

cd "$(dirname "$0")/.."

AWQ_DIR="checkpoints/advisorai-qwen2.5-14b-awq"
PORT="${PORT:-8000}"
GPU_ID="${GPU_ID:-0}"        # which GPU to serve on

if [ ! -d "$AWQ_DIR" ]; then
    echo "[ERROR] AWQ model not found: $AWQ_DIR"
    echo "        Run scripts/03_merge_and_quantize.sh first."
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════════"
echo " AdvisorAI — vLLM INFERENCE SERVER"
echo "═══════════════════════════════════════════════════════════════════"
echo " Model:       $AWQ_DIR"
echo " Port:        $PORT"
echo " GPU:         $GPU_ID"
echo " API style:   OpenAI-compatible (chat/completions, completions)"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

if ! command -v vllm &> /dev/null && ! python -c "import vllm" 2>/dev/null; then
    echo "[ERROR] vLLM not installed. Install with:"
    echo "        pip install vllm==0.6.3"
    exit 1
fi

export CUDA_VISIBLE_DEVICES="$GPU_ID"

python -m vllm.entrypoints.openai.api_server \
    --model "$AWQ_DIR" \
    --served-model-name advisorai-v2 \
    --quantization awq \
    --dtype bfloat16 \
    --host 0.0.0.0 \
    --port "$PORT" \
    --gpu-memory-utilization 0.85 \
    --max-model-len 4096 \
    --enable-prefix-caching
