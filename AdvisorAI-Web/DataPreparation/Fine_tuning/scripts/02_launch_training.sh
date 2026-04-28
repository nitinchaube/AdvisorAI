#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Launch Training — runs the main training job
# ═══════════════════════════════════════════════════════════════════════
#
# Launches src/train.py with Accelerate for DDP across 2× RTX 3090.
#
# Usage:
#     bash scripts/02_launch_training.sh           # use both GPUs (default)
#     bash scripts/02_launch_training.sh single    # single GPU debug mode
#
# Automatically:
#   - Exports W&B project + environment variables
#   - Redirects output to timestamped log file in logs/
#   - Resumes from the latest checkpoint if one exists

set -e

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

MODE="${1:-multi}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/train_${TIMESTAMP}.log"
mkdir -p logs

# ── Environment variables ─────────────────────────────────────────────
export WANDB_PROJECT="advisorai"
export WANDB_LOG_MODEL="false"
export TOKENIZERS_PARALLELISM=false

# NCCL tuning for consumer GPUs (no InfiniBand, PCIe only)
export NCCL_P2P_DISABLE=0
export NCCL_IB_DISABLE=1
export NCCL_SHM_DISABLE=0

# Help debug if things go wrong
# export TORCH_DISTRIBUTED_DEBUG=INFO
# export NCCL_DEBUG=INFO

echo "═══════════════════════════════════════════════════════════════════"
echo " AdvisorAI Training — LAUNCH"
echo "═══════════════════════════════════════════════════════════════════"
echo " Mode:      $MODE"
echo " Log:       $LOG_FILE"
echo " Started:   $(date)"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# ── Launch ────────────────────────────────────────────────────────────
if [ "$MODE" = "single" ]; then
    echo "Running in SINGLE-GPU mode (for debugging)..."
    export CUDA_VISIBLE_DEVICES=0
    python src/train.py 2>&1 | tee "$LOG_FILE"
else
    echo "Running in MULTI-GPU mode (DDP across 2 GPUs)..."
    export CUDA_VISIBLE_DEVICES=0,1
    accelerate launch \
        --config_file config/accelerate_ddp.yaml \
        src/train.py 2>&1 | tee "$LOG_FILE"
fi

# ── Done ──────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " TRAINING FINISHED"
echo "═══════════════════════════════════════════════════════════════════"
echo " Log saved: $LOG_FILE"
echo ""
echo " Next steps:"
echo "   1. Evaluate:  python src/eval_model.py --model-path checkpoints/advisorai-qwen2.5-14b-qdora/final"
echo "   2. Merge:     python src/merge_and_quantize.py"
echo "   3. Serve:     bash scripts/04_serve_vllm.sh"
echo ""
