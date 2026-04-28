#!/usr/bin/env python3
"""
Upsample safety / refusal examples in the training set.

Your dataset has only 102 refusal examples (0.13% of 79k) spread across
categories like 'harmful', 'identity', 'unknown_info', 'sensitive_redirect',
'off_topic'. This is too sparse to reliably teach safety behavior.

This script:
  1. Reads train.jsonl
  2. Identifies safety-category examples
  3. Appends N additional copies of each (default: 4, giving 5× total)
  4. Writes train_upsampled.jsonl (preserving original)

Run from Fine_tuning/ root:
    python src/upsample_safety.py                 # defaults (5x multiplier)
    python src/upsample_safety.py --multiplier 10 # even heavier upsampling
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.training_config import TRAIN_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SAFETY_CATEGORIES = frozenset([
    "harmful",
    "identity",
    "unknown_info",
    "sensitive_redirect",
    "off_topic",
    "refusal",
])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--multiplier", type=int, default=5,
        help="Total count multiplier for safety examples (default: 5 = 4 extra copies)"
    )
    parser.add_argument(
        "--input", type=str, default=str(TRAIN_FILE),
        help="Input train.jsonl path"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output path (default: overwrite input)"
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create a .bak backup of the input before modifying"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        sys.exit(f"ERROR: Input file not found: {input_path}")

    # ── Load ──────────────────────────────────────────────────────────
    log.info("Reading %s ...", input_path)
    records = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    log.warning("Skipped malformed line: %s", e)

    total = len(records)
    log.info("  Loaded %d total records", total)

    # ── Identify safety records ───────────────────────────────────────
    def get_category(r):
        return (r.get("metadata") or {}).get("category", "")

    safety = [r for r in records if get_category(r) in SAFETY_CATEGORIES]
    non_safety = [r for r in records if get_category(r) not in SAFETY_CATEGORIES]

    log.info("  Safety records:  %d (%.2f%%)", len(safety), 100 * len(safety) / total)
    log.info("  Other records:   %d", len(non_safety))

    if not safety:
        log.warning("No safety records found. Nothing to upsample. Exiting.")
        return

    # ── Show category breakdown ───────────────────────────────────────
    from collections import Counter
    by_cat = Counter(get_category(r) for r in safety)
    log.info("  Safety breakdown:")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        log.info("    %-25s: %d", cat, count)

    # ── Backup ────────────────────────────────────────────────────────
    if args.backup:
        backup = input_path.with_suffix(input_path.suffix + ".bak")
        backup.write_text(input_path.read_text(), encoding="utf-8")
        log.info("Backup written: %s", backup)

    # ── Upsample ──────────────────────────────────────────────────────
    extra_copies = max(0, args.multiplier - 1)
    log.info("Upsampling safety records %dx (adding %d extra copies)",
             args.multiplier, extra_copies)

    output_records = records[:]
    for _ in range(extra_copies):
        output_records.extend(safety)

    # Shuffle so safety examples don't cluster at the end
    import random
    random.seed(42)
    random.shuffle(output_records)

    # ── Write ─────────────────────────────────────────────────────────
    log.info("Writing %d records to %s", len(output_records), output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in output_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ── Summary ───────────────────────────────────────────────────────
    new_safety_count = args.multiplier * len(safety)
    new_total = len(output_records)
    log.info("=" * 60)
    log.info("UPSAMPLING COMPLETE")
    log.info("=" * 60)
    log.info("  Before: %d total, %d safety (%.2f%%)",
             total, len(safety), 100 * len(safety) / total)
    log.info("  After:  %d total, %d safety (%.2f%%)",
             new_total, new_safety_count, 100 * new_safety_count / new_total)
    log.info("  Output: %s", output_path)


if __name__ == "__main__":
    main()
