#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Pre-Flight Checks — run this before training
# ═══════════════════════════════════════════════════════════════════════
#
# Verifies:
#   1. No old llama-server / LM Studio processes are holding the GPUs
#   2. Both 3090s are free
#   3. Enough RAM + swap
#   4. Training data files exist
#   5. Disk space is sufficient
#
# Run:
#     bash scripts/00_preflight.sh

set -e

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "═══════════════════════════════════════════════════════════════════"
echo " AdvisorAI Training — PRE-FLIGHT CHECKS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# ── 1. Check for processes holding GPUs ──────────────────────────────
echo "[1/6] Checking for processes using GPUs..."
if pgrep -x llama-server > /dev/null; then
    echo "  [WARN] llama-server is running. Kill it with: sudo killall llama-server"
    echo "         (LM Studio must be closed or its server stopped)"
    read -rp "  Kill llama-server now? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo killall llama-server || true
        echo "  [OK] Killed"
    else
        echo "  Leaving running - you may need to close it manually."
    fi
else
    echo "  [OK] No llama-server process found"
fi

# ── 2. nvidia-smi check ──────────────────────────────────────────────
echo ""
echo "[2/6] Checking GPU status..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "  [ERROR] nvidia-smi not found. Is the NVIDIA driver installed?"
    exit 1
fi

nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader

NUM_GPUS=$(nvidia-smi --list-gpus | wc -l)
if [ "$NUM_GPUS" -lt 2 ]; then
    echo "  [WARN] Only $NUM_GPUS GPU detected. DDP expects 2."
    echo "         You can still train on 1 GPU by changing accelerate config."
else
    echo "  [OK] Detected $NUM_GPUS GPUs"
fi

# Check if any GPU has > 1 GB used
MAX_GPU_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sort -n -r | head -1)
if [ "$MAX_GPU_USED" -gt 1000 ]; then
    echo "  [WARN] A GPU is already using ${MAX_GPU_USED} MB. Make sure nothing is training/serving."
fi

# ── 3. RAM check ─────────────────────────────────────────────────────
echo ""
echo "[3/6] Checking system RAM..."
free -h
AVAILABLE_GB=$(free -g | awk '/^Mem:/ {print $7}')
if [ "$AVAILABLE_GB" -lt 15 ]; then
    echo "  [WARN] Only ${AVAILABLE_GB} GB free. 14B training needs ~20+ GB for dataset + model loading."
    echo "         Consider closing other apps."
else
    echo "  [OK] ${AVAILABLE_GB} GB free"
fi

# ── 4. Swap check (needed for 14B merge step) ───────────────────────
echo ""
echo "[4/6] Checking swap space..."
SWAP_GB=$(free -g | awk '/^Swap:/ {print $2}')
if [ "$SWAP_GB" -lt 16 ]; then
    echo "  [WARN] Only ${SWAP_GB} GB swap. 14B LoRA merge needs ~56 GB RAM total."
    echo "         Recommend adding 32 GB swap:"
    echo "           sudo fallocate -l 32G /swapfile"
    echo "           sudo chmod 600 /swapfile"
    echo "           sudo mkswap /swapfile"
    echo "           sudo swapon /swapfile"
    read -rp "  Add 32G swap now? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo fallocate -l 32G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo "  [OK] Added 32G swap"
    fi
else
    echo "  [OK] ${SWAP_GB} GB swap configured"
fi

# ── 5. Training data files ───────────────────────────────────────────
echo ""
echo "[5/6] Checking training data files..."
TRAIN_FILE="$ROOT/../output/train.jsonl"
EVAL_FILE="$ROOT/../output/eval.jsonl"

if [ ! -f "$TRAIN_FILE" ]; then
    echo "  [ERROR] Train file not found: $TRAIN_FILE"
    echo "          Run the data prep pipeline first (01_clean, 02_generate, 03_score, 04_assemble)"
    exit 1
else
    TRAIN_LINES=$(wc -l < "$TRAIN_FILE")
    TRAIN_SIZE=$(du -h "$TRAIN_FILE" | cut -f1)
    echo "  [OK] Train: $TRAIN_LINES lines, $TRAIN_SIZE ($TRAIN_FILE)"
fi

if [ ! -f "$EVAL_FILE" ]; then
    echo "  [ERROR] Eval file not found: $EVAL_FILE"
    exit 1
else
    EVAL_LINES=$(wc -l < "$EVAL_FILE")
    EVAL_SIZE=$(du -h "$EVAL_FILE" | cut -f1)
    echo "  [OK] Eval:  $EVAL_LINES lines, $EVAL_SIZE ($EVAL_FILE)"
fi

# ── 6. Disk space for checkpoints ────────────────────────────────────
echo ""
echo "[6/6] Checking disk space..."
AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE" -lt 100 ]; then
    echo "  [WARN] Only ${AVAILABLE} GB free. Full pipeline needs:"
    echo "         - ~5 GB for LoRA checkpoints (every 250 steps, keep 3)"
    echo "         - ~30 GB for merged BF16 model"
    echo "         - ~10 GB for AWQ quantized model"
    echo "         Total: ~50 GB"
else
    echo "  [OK] ${AVAILABLE} GB free"
fi

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " PRE-FLIGHT COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo " Next steps:"
echo "   1. Set up environment:   bash scripts/01_setup_env.sh"
echo "   2. (Optional) Upsample safety data:"
echo "        python src/upsample_safety.py --backup"
echo "   3. Launch training:      bash scripts/02_launch_training.sh"
echo ""
