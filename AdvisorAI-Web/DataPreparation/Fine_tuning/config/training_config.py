"""
Training configuration for AdvisorAI fine-tuning.

Edit the values below to adjust training. All hyperparameters live here
so you never need to dig into train.py itself.
"""

from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT.parent / "output"

TRAIN_FILE = DATA_DIR / "train.jsonl"
EVAL_FILE = DATA_DIR / "eval.jsonl"

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints" / "advisorai-qwen2.5-14b-qdora"
MERGED_DIR = PROJECT_ROOT / "checkpoints" / "advisorai-qwen2.5-14b-merged"
AWQ_DIR = PROJECT_ROOT / "checkpoints" / "advisorai-qwen2.5-14b-awq"

LOGS_DIR = PROJECT_ROOT / "logs"


# ═══════════════════════════════════════════════════════════════════════
# Base model
# ═══════════════════════════════════════════════════════════════════════

BASE_MODEL = "Qwen/Qwen2.5-14B-Instruct"
# Alternative (faster, lower quality):
# BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"


# ═══════════════════════════════════════════════════════════════════════
# QDoRA + rsLoRA configuration
# ═══════════════════════════════════════════════════════════════════════

# Quantization (4-bit NF4 for the base model weights)
USE_4BIT = True
BNB_4BIT_QUANT_TYPE = "nf4"
BNB_4BIT_USE_DOUBLE_QUANT = True

# LoRA / DoRA hyperparameters
LORA_R = 64                   # rank — rsLoRA makes higher rank useful
LORA_ALPHA = 128              # typically 2 * r
LORA_DROPOUT = 0.05
USE_DORA = True               # Weight-Decomposed LoRA (DoRA)
USE_RSLORA = True             # Rank-Stabilized LoRA scaling
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",    # attention projections
    "gate_proj", "up_proj", "down_proj",        # MLP projections
]


# ═══════════════════════════════════════════════════════════════════════
# Training hyperparameters
# ═══════════════════════════════════════════════════════════════════════

NUM_EPOCHS = 2
PER_DEVICE_TRAIN_BATCH_SIZE = 2      # 14B needs smaller batch than 7B
PER_DEVICE_EVAL_BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 8      # Effective batch: 2 GPUs × 2 × 8 = 32

LEARNING_RATE = 8e-5                 # Slightly lower for 14B (was 1e-4 for 7B)
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 0.3
OPTIMIZER = "paged_adamw_8bit"

# Precision & memory
BF16 = True                          # RTX 3090 supports BF16
TF32 = True                          # free speedup on Ampere
GRADIENT_CHECKPOINTING = True

# Sequence handling
MAX_SEQ_LENGTH = 2048                # covers 99% of our examples (max was 1175 tokens)
PACKING = True                       # 3× throughput on short sequences
DATASET_NUM_PROC = 8                 # parallel tokenization

# NEFTune — noise injection for better chat quality
NEFTUNE_NOISE_ALPHA = 5              # Research-backed; range 5-15


# ═══════════════════════════════════════════════════════════════════════
# Logging, evaluation, checkpointing
# ═══════════════════════════════════════════════════════════════════════

LOGGING_STEPS = 25
EVAL_STEPS = 250
SAVE_STEPS = 250
SAVE_TOTAL_LIMIT = 3
LOAD_BEST_MODEL_AT_END = True
METRIC_FOR_BEST_MODEL = "eval_loss"
EARLY_STOPPING_PATIENCE = 5          # Stop if no improvement in 5 evals

# Weights & Biases
REPORT_TO = "wandb"                  # "wandb" | "tensorboard" | "none"
WANDB_PROJECT = "advisorai"
RUN_NAME = "advisorai-qwen25-14b-qdora-neftune-v1"


# ═══════════════════════════════════════════════════════════════════════
# Misc
# ═══════════════════════════════════════════════════════════════════════

SEED = 42
DATALOADER_NUM_WORKERS = 4
DATALOADER_PIN_MEMORY = True
DDP_FIND_UNUSED_PARAMETERS = False
