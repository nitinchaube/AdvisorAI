#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Post-Training Pipeline — merge DoRA adapter + quantize to AWQ
# ═══════════════════════════════════════════════════════════════════════
#
# Run AFTER training completes. Produces:
#   checkpoints/advisorai-qwen2.5-14b-merged/   (BF16, ~28 GB — for GGUF conversion)
#   checkpoints/advisorai-qwen2.5-14b-awq/      (AWQ 4-bit, ~9 GB — for vLLM)
#
# NOTE: The merge step needs ~56 GB RAM. Make sure swap is configured.
#       (scripts/00_preflight.sh sets this up)
#
# Run:
#     bash scripts/03_merge_and_quantize.sh                # full pipeline
#     bash scripts/03_merge_and_quantize.sh --skip-awq     # merge only
#     bash scripts/03_merge_and_quantize.sh --skip-merge   # quantize only

set -e

cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/merge_${TIMESTAMP}.log"
mkdir -p logs

echo "═══════════════════════════════════════════════════════════════════"
echo " AdvisorAI — POST-TRAINING MERGE + QUANTIZE"
echo "═══════════════════════════════════════════════════════════════════"
echo " Log:     $LOG_FILE"
echo " Started: $(date)"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Pass through any flags to the Python script
python src/merge_and_quantize.py "$@" 2>&1 | tee "$LOG_FILE"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " MERGE + QUANTIZE FINISHED"
echo "═══════════════════════════════════════════════════════════════════"
echo " Log: $LOG_FILE"
echo ""
echo " To serve the model:"
echo "     bash scripts/04_serve_vllm.sh"
echo ""
