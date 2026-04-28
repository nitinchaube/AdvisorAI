#!/usr/bin/env python3
"""
Step 4: Assemble the final fine-tuning dataset in chat format.

Reads scored/filtered data from Step 3 and converts everything into
the standard messages format compatible with:
  - HuggingFace TRL / SFTTrainer (tokenizer.apply_chat_template)
  - OpenAI fine-tuning API
  - Axolotl / Unsloth

Output:
  output/advisorai_finetune_v2.jsonl

Run:
  python 04_assemble_dataset.py [--split]

Use --split to also create train/eval splits (90/10).
"""

import argparse
import json
import logging
import random
from collections import Counter
from pathlib import Path

from config import (
    FINAL_DATASET_PATH,
    OUTPUT_DIR,
    SCORED_QA_PATH,
    SYSTEM_PROMPT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_scored_records() -> list[dict]:
    records = []
    if not SCORED_QA_PATH.exists():
        log.error("Scored file not found: %s", SCORED_QA_PATH)
        log.error("Run 03_score_and_filter.py first.")
        return records
    with open(SCORED_QA_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def to_single_turn_chat(record: dict) -> dict:
    """Convert a single-turn Q&A into chat messages format."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": record["question"]},
            {"role": "assistant", "content": record["answer"]},
        ],
        "metadata": {
            "category": record.get("category", ""),
            "type": record.get("type", "single_turn"),
            "source_id": record.get("source_id", ""),
            "avg_score": record.get("scores", {}).get("avg_score", 0),
        },
    }


def to_multiturn_chat(record: dict) -> dict:
    """Convert a multi-turn conversation into chat messages format."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in record["messages"]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    return {
        "messages": messages,
        "metadata": {
            "category": record.get("category", ""),
            "type": "multiturn",
            "source_id": record.get("source_id", ""),
            "avg_score": record.get("scores", {}).get("avg_score", 0),
        },
    }


def validate_record(chat_record: dict) -> bool:
    """Validate a chat-format record before writing."""
    msgs = chat_record.get("messages", [])
    if len(msgs) < 3:  # system + user + assistant minimum
        return False
    if msgs[0].get("role") != "system":
        return False
    for msg in msgs[1:]:
        if msg.get("role") not in ("user", "assistant"):
            return False
        if not msg.get("content") or len(msg["content"].strip()) < 5:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Assemble final fine-tuning dataset")
    parser.add_argument("--split", action="store_true", help="Create train/eval splits (90/10)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)

    records = load_scored_records()
    if not records:
        return

    log.info("Loaded %d scored records", len(records))

    # Convert to chat format
    chat_records = []
    type_counts = Counter()
    cat_counts = Counter()
    skipped = 0

    for record in records:
        if record.get("type") == "multiturn":
            chat = to_multiturn_chat(record)
        else:
            chat = to_single_turn_chat(record)

        if validate_record(chat):
            chat_records.append(chat)
            type_counts[record.get("type", "single_turn")] += 1
            cat_counts[record.get("category", "unknown")] += 1
        else:
            skipped += 1

    log.info("Converted %d records, skipped %d invalid", len(chat_records), skipped)

    # Shuffle for training
    random.shuffle(chat_records)

    # Write full dataset
    with open(FINAL_DATASET_PATH, "w", encoding="utf-8") as f:
        for record in chat_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    log.info("Wrote %d records to %s", len(chat_records), FINAL_DATASET_PATH)

    # Optional train/eval split
    if args.split and len(chat_records) > 100:
        split_idx = int(len(chat_records) * 0.9)
        train = chat_records[:split_idx]
        eval_set = chat_records[split_idx:]

        train_path = OUTPUT_DIR / "train.jsonl"
        eval_path = OUTPUT_DIR / "eval.jsonl"

        with open(train_path, "w", encoding="utf-8") as f:
            for r in train:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        with open(eval_path, "w", encoding="utf-8") as f:
            for r in eval_set:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        log.info("Train: %d records → %s", len(train), train_path)
        log.info("Eval:  %d records → %s", len(eval_set), eval_path)

    # Summary
    print("\n" + "=" * 60)
    print("FINAL DATASET SUMMARY")
    print("=" * 60)
    print(f"Total examples: {len(chat_records):,}")
    print(f"\nBy type:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:20s}: {c:>6,}")
    print(f"\nBy category:")
    for cat, c in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {c:>6,}")

    # Message length stats
    msg_lens = []
    for r in chat_records:
        total = sum(len(m["content"]) for m in r["messages"])
        msg_lens.append(total)
    print(f"\nTotal message length stats:")
    print(f"  Min: {min(msg_lens):,} chars")
    print(f"  Max: {max(msg_lens):,} chars")
    print(f"  Mean: {sum(msg_lens) // len(msg_lens):,} chars")

    fsize = FINAL_DATASET_PATH.stat().st_size / 1024 / 1024
    print(f"\nOutput: {FINAL_DATASET_PATH}")
    print(f"Size: {fsize:.1f} MB")

    if args.split:
        print(f"\nSplits:")
        print(f"  Train: {split_idx:,} examples")
        print(f"  Eval:  {len(chat_records) - split_idx:,} examples")


if __name__ == "__main__":
    main()
