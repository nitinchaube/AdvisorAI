#!/usr/bin/env python3
"""
Post-training pipeline: merge DoRA adapters into base model and quantize to AWQ.

Steps:
  1. Load base model in BF16 (on CPU to save VRAM)
  2. Load trained DoRA adapters
  3. Merge adapters into base weights
  4. Save merged model (~28 GB BF16)
  5. Quantize to AWQ 4-bit (~9 GB)
  6. Save AWQ model ready for vLLM deployment

Note: Merging 14B on CPU needs ~56 GB RAM. Make sure you have swap configured
(see scripts/00_preflight.sh).

Run from Fine_tuning/ root:
    python src/merge_and_quantize.py                # full pipeline
    python src/merge_and_quantize.py --skip-awq     # only merge, no quantize
    python src/merge_and_quantize.py --skip-merge   # only quantize existing merged
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.training_config import (
    AWQ_DIR,
    BASE_MODEL,
    CHECKPOINT_DIR,
    EVAL_FILE,
    MERGED_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Step 1: Merge DoRA adapter into base model
# ═══════════════════════════════════════════════════════════════════════

def merge_adapter():
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    adapter_dir = CHECKPOINT_DIR / "final"
    if not adapter_dir.exists():
        sys.exit(
            f"ERROR: Adapter directory not found: {adapter_dir}\n"
            f"Run src/train.py first."
        )

    log.info("=" * 60)
    log.info("STEP 1: MERGE DoRA ADAPTER INTO BASE MODEL")
    log.info("=" * 60)
    log.info("  Base model:  %s", BASE_MODEL)
    log.info("  Adapter:     %s", adapter_dir)
    log.info("  Output:      %s", MERGED_DIR)

    log.info("Loading base model (BF16 on CPU) — this uses ~28 GB RAM ...")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    log.info("Loading DoRA adapter ...")
    model = PeftModel.from_pretrained(base, str(adapter_dir))

    log.info("Merging adapter into base weights (this takes a few minutes) ...")
    merged = model.merge_and_unload()

    log.info("Saving merged model to %s ...", MERGED_DIR)
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_DIR), safe_serialization=True)

    # Save tokenizer alongside
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.save_pretrained(str(MERGED_DIR))

    log.info("Merged model saved (%.1f GB)", _dir_size_gb(MERGED_DIR))

    # Free memory
    del base, model, merged, tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ═══════════════════════════════════════════════════════════════════════
# Step 2: Quantize merged model to AWQ 4-bit
# ═══════════════════════════════════════════════════════════════════════

def quantize_awq():
    try:
        from awq import AutoAWQForCausalLM
    except ImportError:
        sys.exit(
            "ERROR: autoawq not installed.\n"
            "Install with: pip install autoawq==0.2.6"
        )
    from transformers import AutoTokenizer

    if not MERGED_DIR.exists():
        sys.exit(
            f"ERROR: Merged model not found: {MERGED_DIR}\n"
            f"Run this script without --skip-merge first, or with merge step enabled."
        )

    log.info("=" * 60)
    log.info("STEP 2: QUANTIZE TO AWQ 4-BIT")
    log.info("=" * 60)
    log.info("  Merged:   %s", MERGED_DIR)
    log.info("  Output:   %s", AWQ_DIR)

    # ── Build calibration data from eval set ──────────────────────────
    log.info("Building calibration set from eval.jsonl ...")
    calib_samples = _build_calibration_set(n=512)
    log.info("  Collected %d calibration samples", len(calib_samples))

    log.info("Loading merged model for quantization ...")
    model = AutoAWQForCausalLM.from_pretrained(
        str(MERGED_DIR),
        torch_dtype=torch.bfloat16,
        safetensors=True,
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(str(MERGED_DIR), trust_remote_code=True)

    log.info("Running AWQ calibration (this takes 15-30 minutes for 14B) ...")
    quant_config = {
        "zero_point": True,
        "q_group_size": 128,
        "w_bit": 4,
        "version": "GEMM",
    }
    model.quantize(tokenizer, quant_config=quant_config, calib_data=calib_samples)

    log.info("Saving AWQ model to %s ...", AWQ_DIR)
    AWQ_DIR.mkdir(parents=True, exist_ok=True)
    model.save_quantized(str(AWQ_DIR))
    tokenizer.save_pretrained(str(AWQ_DIR))

    log.info("AWQ model saved (%.1f GB)", _dir_size_gb(AWQ_DIR))

    del model, tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _build_calibration_set(n: int = 512) -> list[str]:
    """Build a calibration set from the eval.jsonl file."""
    if not EVAL_FILE.exists():
        log.warning("No eval file, falling back to synthetic calibration")
        return [f"The Stevens Institute program covers topic {i}." for i in range(n)]

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

    samples = []
    with open(EVAL_FILE, encoding="utf-8") as f:
        for line in f:
            if len(samples) >= n:
                break
            try:
                rec = json.loads(line)
                messages = rec.get("messages")
                if messages:
                    text = tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=False
                    )
                    samples.append(text)
            except (json.JSONDecodeError, Exception):
                continue
    return samples


def _dir_size_gb(path: Path) -> float:
    total = sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
    return total / 1e9


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-merge", action="store_true",
                        help="Skip merge step (use if merged model already exists)")
    parser.add_argument("--skip-awq", action="store_true",
                        help="Skip AWQ quantization (only produce merged BF16 model)")
    args = parser.parse_args()

    if not args.skip_merge:
        merge_adapter()
    else:
        log.info("Skipping merge (using existing %s)", MERGED_DIR)

    if not args.skip_awq:
        quantize_awq()
    else:
        log.info("Skipping AWQ quantization")

    log.info("=" * 60)
    log.info("POST-TRAINING PIPELINE COMPLETE")
    log.info("=" * 60)
    if MERGED_DIR.exists():
        log.info("  Merged (BF16): %s (%.1f GB)", MERGED_DIR, _dir_size_gb(MERGED_DIR))
    if AWQ_DIR.exists():
        log.info("  AWQ (4-bit):   %s (%.1f GB)", AWQ_DIR, _dir_size_gb(AWQ_DIR))
    log.info("  Next: bash scripts/04_serve_vllm.sh")


if __name__ == "__main__":
    main()
