#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Environment Setup — creates conda env and installs all dependencies
# ═══════════════════════════════════════════════════════════════════════
#
# Creates a conda env called 'advisorai' with:
#   - PyTorch 2.4 + CUDA 12.4
#   - Transformers, TRL, PEFT, Accelerate, bitsandbytes
#   - Flash Attention 2 (compiles for ~10-20 min)
#   - vLLM + AutoAWQ (for post-training)
#
# Run:
#     bash scripts/01_setup_env.sh

set -e

cd "$(dirname "$0")/.."

ENV_NAME="advisorai"

echo "═══════════════════════════════════════════════════════════════════"
echo " AdvisorAI Training — ENVIRONMENT SETUP"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# ── Check conda ───────────────────────────────────────────────────────
if ! command -v conda &> /dev/null; then
    echo "[ERROR] conda not found. Install Miniconda first:"
    echo "        https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# ── Create env ────────────────────────────────────────────────────────
if conda env list | grep -q "^$ENV_NAME "; then
    echo "[WARN] Conda env '$ENV_NAME' already exists."
    read -rp "Remove it and recreate? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        conda env remove -n "$ENV_NAME" -y
    else
        echo "Using existing env. Make sure dependencies are up to date."
    fi
fi

if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "[1/4] Creating conda env '$ENV_NAME' with Python 3.11 ..."
    conda create -n "$ENV_NAME" python=3.11 -y
fi

# ── Activate ──────────────────────────────────────────────────────────
# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo ""
echo "[2/4] Installing PyTorch 2.4 with CUDA 12.4 ..."
pip install --upgrade pip
pip install torch==2.4.0 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

echo ""
echo "[3/4] Installing core training stack ..."
pip install -r requirements.txt

echo ""
echo "[4/4] Installing Flash Attention 2 (this takes 10-20 minutes) ..."
echo "     Press Ctrl-C to skip if you don't want to wait now."
pip install flash-attn==2.6.3 --no-build-isolation || {
    echo "[WARN] Flash Attention 2 install failed or was skipped."
    echo "       Training will fall back to eager attention (~30% slower)."
    echo "       You can retry later with:"
    echo "         pip install flash-attn==2.6.3 --no-build-isolation"
}

echo ""
echo "Optional: Install vLLM + AutoAWQ for post-training (serving & quantization)"
read -rp "Install now? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
    pip install vllm==0.6.3 autoawq==0.2.6
    echo "  [OK] vLLM + AutoAWQ installed"
else
    echo "  Skipped. Install later with:"
    echo "    pip install vllm==0.6.3 autoawq==0.2.6"
fi

# ── Verification ──────────────────────────────────────────────────────
echo ""
echo "Verifying installation ..."
python - <<'PY'
import sys
print(f"Python: {sys.version}")

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  [{i}] {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_memory/1e9:.1f} GB)")

import transformers, trl, peft, accelerate, bitsandbytes
print(f"transformers: {transformers.__version__}")
print(f"trl:          {trl.__version__}")
print(f"peft:         {peft.__version__}")
print(f"accelerate:   {accelerate.__version__}")
print(f"bitsandbytes: {bitsandbytes.__version__}")

try:
    import flash_attn
    print(f"flash_attn:   {flash_attn.__version__}")
except ImportError:
    print("flash_attn:   not installed (optional)")
PY

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " ENVIRONMENT SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo " Activate the env in your shell:"
echo "     conda activate $ENV_NAME"
echo ""
echo " Next step:"
echo "     bash scripts/02_launch_training.sh"
echo ""
