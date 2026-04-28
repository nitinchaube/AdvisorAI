#!/usr/bin/env python3
"""
AdvisorAI Fine-Tuning — Main Training Script
=============================================

Fine-tunes Qwen2.5-14B-Instruct with QDoRA (4-bit NF4 + DoRA r=64) + NEFTune
+ rsLoRA on the Stevens dataset.

Pipeline:
  1. Load tokenizer + set up chat template
  2. Quantize base model to 4-bit NF4
  3. Prepare for k-bit training (enables gradient computation through quant)
  4. Apply DoRA adapters with rsLoRA scaling
  5. Load train/eval datasets (chat-format JSONL)
  6. Initialize TRL SFTTrainer with:
     - Flash Attention 2
     - Sequence packing
     - NEFTune noise injection
     - Early stopping
  7. Train, evaluate, save LoRA adapters

Launch (from Fine_tuning/ root):
    accelerate launch --config_file config/accelerate_ddp.yaml src/train.py

Or directly with Python (single GPU fallback):
    python src/train.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import torch

# Make config importable when running from Fine_tuning/ root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.training_config import (
    AWQ_DIR,
    BASE_MODEL,
    BF16,
    BNB_4BIT_QUANT_TYPE,
    BNB_4BIT_USE_DOUBLE_QUANT,
    CHECKPOINT_DIR,
    DATALOADER_NUM_WORKERS,
    DATALOADER_PIN_MEMORY,
    DATASET_NUM_PROC,
    DDP_FIND_UNUSED_PARAMETERS,
    EARLY_STOPPING_PATIENCE,
    EVAL_FILE,
    EVAL_STEPS,
    GRADIENT_ACCUMULATION_STEPS,
    GRADIENT_CHECKPOINTING,
    LEARNING_RATE,
    LOAD_BEST_MODEL_AT_END,
    LOGGING_STEPS,
    LOGS_DIR,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_R,
    LORA_TARGET_MODULES,
    LR_SCHEDULER,
    MAX_GRAD_NORM,
    MAX_SEQ_LENGTH,
    METRIC_FOR_BEST_MODEL,
    NEFTUNE_NOISE_ALPHA,
    NUM_EPOCHS,
    OPTIMIZER,
    PACKING,
    PER_DEVICE_EVAL_BATCH_SIZE,
    PER_DEVICE_TRAIN_BATCH_SIZE,
    REPORT_TO,
    RUN_NAME,
    SAVE_STEPS,
    SAVE_TOTAL_LIMIT,
    SEED,
    TF32,
    TRAIN_FILE,
    USE_4BIT,
    USE_DORA,
    USE_RSLORA,
    WANDB_PROJECT,
    WARMUP_RATIO,
    WEIGHT_DECAY,
)

# ═══════════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Environment setup
# ═══════════════════════════════════════════════════════════════════════

def setup_environment():
    """Configure environment variables and CUDA settings."""
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("WANDB_PROJECT", WANDB_PROJECT)
    os.environ.setdefault("WANDB_LOG_MODEL", "false")

    if TF32 and torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    if torch.cuda.is_available():
        torch.cuda.set_device(local_rank)
        log.info(
            "CUDA: device=%d, %s, %.1f GB",
            local_rank,
            torch.cuda.get_device_name(local_rank),
            torch.cuda.get_device_properties(local_rank).total_memory / 1e9,
        )
    return local_rank


# ═══════════════════════════════════════════════════════════════════════
# Tokenizer
# ═══════════════════════════════════════════════════════════════════════

def load_tokenizer():
    from transformers import AutoTokenizer

    log.info("Loading tokenizer for %s ...", BASE_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        trust_remote_code=True,
        use_fast=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"  # critical for causal LM training
    log.info(
        "Tokenizer loaded: vocab=%d, pad=%s, eos=%s",
        tokenizer.vocab_size, tokenizer.pad_token, tokenizer.eos_token,
    )
    return tokenizer


# ═══════════════════════════════════════════════════════════════════════
# Model (4-bit + QDoRA)
# ═══════════════════════════════════════════════════════════════════════

def load_model(local_rank: int):
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    # ── 4-bit NF4 quantization ────────────────────────────────────────
    if USE_4BIT:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=BNB_4BIT_QUANT_TYPE,
            bnb_4bit_compute_dtype=torch.bfloat16 if BF16 else torch.float16,
            bnb_4bit_use_double_quant=BNB_4BIT_USE_DOUBLE_QUANT,
        )
    else:
        bnb_config = None

    log.info("Loading base model %s with 4-bit NF4 ...", BASE_MODEL)

    # ── Check Flash Attention 2 availability ──────────────────────────
    attn_impl = "eager"
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
        log.info("Flash Attention 2 enabled")
    except ImportError:
        log.warning(
            "Flash Attention 2 not installed — using eager attention. "
            "Install with: pip install flash-attn --no-build-isolation"
        )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map={"": local_rank},      # critical for DDP
        torch_dtype=torch.bfloat16 if BF16 else torch.float16,
        attn_implementation=attn_impl,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    if hasattr(model.config, "pretraining_tp"):
        model.config.pretraining_tp = 1

    # ── Prepare for k-bit training ────────────────────────────────────
    if USE_4BIT:
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=GRADIENT_CHECKPOINTING,
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )

    # ── Apply QDoRA + rsLoRA ──────────────────────────────────────────
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        use_dora=USE_DORA,
        use_rslora=USE_RSLORA,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model


# ═══════════════════════════════════════════════════════════════════════
# Data
# ═══════════════════════════════════════════════════════════════════════

def load_data():
    from datasets import load_dataset

    if not TRAIN_FILE.exists():
        sys.exit(f"ERROR: Train file not found: {TRAIN_FILE}")
    if not EVAL_FILE.exists():
        sys.exit(f"ERROR: Eval file not found: {EVAL_FILE}")

    log.info("Loading data...")
    log.info("  Train: %s", TRAIN_FILE)
    log.info("  Eval:  %s", EVAL_FILE)

    train_ds = load_dataset("json", data_files=str(TRAIN_FILE), split="train")
    eval_ds = load_dataset("json", data_files=str(EVAL_FILE), split="train")

    log.info("  Train: %d examples", len(train_ds))
    log.info("  Eval:  %d examples", len(eval_ds))

    # Show a sample
    if len(train_ds) > 0:
        sample = train_ds[0]
        log.info("  Sample message count: %d", len(sample.get("messages", [])))

    return train_ds, eval_ds


# ═══════════════════════════════════════════════════════════════════════
# Trainer
# ═══════════════════════════════════════════════════════════════════════

def build_trainer(model, tokenizer, train_ds, eval_ds):
    from trl import SFTConfig, SFTTrainer
    from transformers import EarlyStoppingCallback

    training_args = SFTConfig(
        output_dir=str(CHECKPOINT_DIR),
        num_train_epochs=NUM_EPOCHS,

        # Batch
        per_device_train_batch_size=PER_DEVICE_TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=PER_DEVICE_EVAL_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,

        # Optimizer
        learning_rate=LEARNING_RATE,
        lr_scheduler_type=LR_SCHEDULER,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        max_grad_norm=MAX_GRAD_NORM,
        optim=OPTIMIZER,

        # Precision
        bf16=BF16,
        tf32=TF32,

        # Memory optimization
        gradient_checkpointing=GRADIENT_CHECKPOINTING,
        gradient_checkpointing_kwargs={"use_reentrant": False},

        # Sequence handling
        max_seq_length=MAX_SEQ_LENGTH,
        packing=PACKING,
        dataset_num_proc=DATASET_NUM_PROC,

        # NEFTune
        neftune_noise_alpha=NEFTUNE_NOISE_ALPHA,

        # Logging / eval / checkpointing
        logging_steps=LOGGING_STEPS,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        save_total_limit=SAVE_TOTAL_LIMIT,
        load_best_model_at_end=LOAD_BEST_MODEL_AT_END,
        metric_for_best_model=METRIC_FOR_BEST_MODEL,
        greater_is_better=False,

        # Monitoring
        report_to=REPORT_TO,
        run_name=RUN_NAME,

        # DDP
        ddp_find_unused_parameters=DDP_FIND_UNUSED_PARAMETERS,
        dataloader_num_workers=DATALOADER_NUM_WORKERS,
        dataloader_pin_memory=DATALOADER_PIN_MEMORY,

        seed=SEED,
        data_seed=SEED,
    )

    callbacks = []
    if EARLY_STOPPING_PATIENCE > 0:
        callbacks.append(
            EarlyStoppingCallback(early_stopping_patience=EARLY_STOPPING_PATIENCE)
        )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=training_args,
        callbacks=callbacks,
    )
    return trainer


# ═══════════════════════════════════════════════════════════════════════
# Resume logic
# ═══════════════════════════════════════════════════════════════════════

def find_latest_checkpoint() -> str | None:
    if not CHECKPOINT_DIR.exists():
        return None
    checkpoints = sorted(
        CHECKPOINT_DIR.glob("checkpoint-*"),
        key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else 0,
    )
    if checkpoints:
        return str(checkpoints[-1])
    return None


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    local_rank = setup_environment()

    # Set random seed
    from transformers import set_seed
    set_seed(SEED)

    # ── Build everything ─────────────────────────────────────────────
    tokenizer = load_tokenizer()
    model = load_model(local_rank)
    train_ds, eval_ds = load_data()
    trainer = build_trainer(model, tokenizer, train_ds, eval_ds)

    # ── Resume from checkpoint if available ──────────────────────────
    resume_ckpt = find_latest_checkpoint()
    if resume_ckpt:
        log.info("Resuming from checkpoint: %s", resume_ckpt)
    else:
        log.info("No checkpoint found, starting fresh training")

    # ── Train ────────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info("STARTING TRAINING")
    log.info("=" * 60)
    log.info("  Model:         %s", BASE_MODEL)
    log.info("  Method:        QDoRA (r=%d, alpha=%d, dora=%s, rslora=%s)",
             LORA_R, LORA_ALPHA, USE_DORA, USE_RSLORA)
    log.info("  NEFTune alpha: %s", NEFTUNE_NOISE_ALPHA)
    log.info("  Epochs:        %d", NUM_EPOCHS)
    log.info("  Effective BS:  %d",
             PER_DEVICE_TRAIN_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS
             * int(os.environ.get("WORLD_SIZE", 1)))
    log.info("  Learning rate: %s", LEARNING_RATE)
    log.info("  Max seq len:   %d", MAX_SEQ_LENGTH)
    log.info("  Output:        %s", CHECKPOINT_DIR)
    log.info("=" * 60)

    train_result = trainer.train(resume_from_checkpoint=resume_ckpt)

    # ── Save final model ─────────────────────────────────────────────
    final_dir = CHECKPOINT_DIR / "final"
    log.info("Saving final model to %s", final_dir)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    # ── Final eval ───────────────────────────────────────────────────
    log.info("Running final evaluation...")
    metrics = trainer.evaluate()
    trainer.log_metrics("final_eval", metrics)
    trainer.save_metrics("final_eval", metrics)

    # ── Summary ──────────────────────────────────────────────────────
    train_metrics = train_result.metrics
    trainer.log_metrics("train", train_metrics)
    trainer.save_metrics("train", train_metrics)
    trainer.save_state()

    log.info("=" * 60)
    log.info("TRAINING COMPLETE")
    log.info("=" * 60)
    log.info("  Final train loss: %.4f", train_metrics.get("train_loss", 0))
    log.info("  Final eval loss:  %.4f", metrics.get("eval_loss", 0))
    log.info("  Runtime:          %.1f hours",
             train_metrics.get("train_runtime", 0) / 3600)
    log.info("  Adapters saved:   %s", final_dir)
    log.info("  Next step:        python src/merge_and_quantize.py")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
