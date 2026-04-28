#!/usr/bin/env python3
"""
Step 3: Score and filter generated Q&A using Gemini or LM Studio as a judge.

Scores examples in BATCHES for speed improvement.
Supports two backends:
  - Gemini API (default) — batch size 10
  - LM Studio local (--lmstudio) — uses Qwen/any loaded model, batch size 3

Output:
  output/scored_qa.jsonl — filtered, high-quality examples with scores

Run:
  GEMINI_API_KEY=your_key python 03_score_and_filter.py
  python 03_score_and_filter.py --lmstudio         # use LM Studio local model
  python 03_score_and_filter.py --no-api            # fast filter only, no scoring
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import google.generativeai as genai

from config import (
    COMPARATIVE_QA_PATH,
    GEMINI_API_KEY,
    GEMINI_CALL_DELAY,
    GEMINI_SCORING_MODEL,
    LMSTUDIO_BASE_URL,
    LMSTUDIO_BATCH_SIZE,
    LMSTUDIO_CALL_DELAY,
    LMSTUDIO_TEMPERATURE,
    MIN_SCORE_THRESHOLD,
    MULTITURN_QA_PATH,
    OUTPUT_DIR,
    REFUSAL_QA_PATH,
    SCORED_QA_PATH,
    SCORING_BACKEND,
    SCORING_BATCH_SIZE,
    SINGLE_TURN_QA_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Gemini setup
# ═══════════════════════════════════════════════════════════════════════

def init_gemini():
    key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key:
        sys.exit("ERROR: Set GEMINI_API_KEY environment variable or in config.py")
    genai.configure(api_key=key)
    log.info("API key: %s...%s", key[:8], key[-4:])

    mdl = genai.GenerativeModel(
        GEMINI_SCORING_MODEL,
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )

    # Test call to verify model works
    log.info("Testing model %s with a simple call...", GEMINI_SCORING_MODEL)
    try:
        resp = mdl.generate_content('Return JSON: {"status": "ok"}')
        log.info("Test call succeeded: %s", resp.text[:100])
    except Exception as e:
        log.error("Test call FAILED — type=%s, error=%s", type(e).__name__, str(e)[:500])
        log.error("Try setting: export GEMINI_SCORING_MODEL=gemini-2.5-flash")
        sys.exit(1)

    return mdl


# ═══════════════════════════════════════════════════════════════════════
# LM Studio setup (local Qwen / any model via OpenAI-compatible API)
# ═══════════════════════════════════════════════════════════════════════

def init_lmstudio():
    """Initialise the LM Studio OpenAI-compatible client and verify connectivity."""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit(
            "ERROR: 'openai' package required for --lmstudio mode.\n"
            "       Install it: pip install openai"
        )

    client = OpenAI(base_url=LMSTUDIO_BASE_URL, api_key="lm-studio")

    log.info("Testing LM Studio connection at %s ...", LMSTUDIO_BASE_URL)
    try:
        resp = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": 'Return JSON: {"status": "ok"}'},
            ],
            temperature=LMSTUDIO_TEMPERATURE,
            max_tokens=32,
        )
        text = resp.choices[0].message.content.strip()
        log.info("LM Studio test succeeded: %s", text[:100])
    except Exception as e:
        log.error(
            "LM Studio connection FAILED: %s\n"
            "  → Make sure LM Studio is running with a model loaded\n"
            "  → Local Server tab → Start Server (default port 1234)",
            e,
        )
        sys.exit(1)

    return client


def _extract_json_array(text: str) -> list | None:
    """Best-effort extraction of a JSON array from potentially messy LLM output."""
    text = text.strip()

    # Strip markdown fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("results", "scores", "data", "items"):
                if isinstance(parsed.get(key), list):
                    return parsed[key]
            return [parsed]
    except json.JSONDecodeError:
        pass

    # Find the first [...] in the text
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        try:
            return json.loads(text[bracket_start:bracket_end + 1])
        except json.JSONDecodeError:
            pass

    return None


def call_lmstudio_batch(client, prompt: str, retries: int = 3) -> list | None:
    """Call LM Studio and return parsed JSON array."""
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model="local-model",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict JSON scorer. You MUST respond with "
                            "ONLY a valid JSON array. No explanation, no markdown "
                            "fences, no extra text — just the JSON array."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=LMSTUDIO_TEMPERATURE,
                max_tokens=1024,
            )
            text = resp.choices[0].message.content or ""
            time.sleep(LMSTUDIO_CALL_DELAY)

            result = _extract_json_array(text)
            if result is not None:
                return result

            log.warning(
                "LM Studio JSON parse failed (attempt %d), raw: %.200s",
                attempt + 1, text,
            )
            if attempt < retries - 1:
                time.sleep(1)

        except Exception as e:
            log.warning("LM Studio error (attempt %d): %s", attempt + 1, str(e)[:200])
            if attempt < retries - 1:
                time.sleep(2)

    return None


# ═══════════════════════════════════════════════════════════════════════
# Batch scoring prompt — scores N records in one API call
# ═══════════════════════════════════════════════════════════════════════

BATCH_SCORE_PROMPT = """You are a quality reviewer for an academic advisor chatbot training dataset at Stevens Institute of Technology.

Score EACH of the following {n} Q&A examples on a 1-5 scale.

For each example, evaluate:
- accuracy: Are facts plausible and non-fabricated? (5=grounded, 1=hallucinated)
- naturalness: Does it sound like a real student/advisor? (5=natural, 1=robotic)
- helpfulness: Is it specific and actionable? (5=helpful, 1=vague)
- formatting: Good markdown, right length? (5=excellent, 1=poor)

Flag these issues (true/false):
- bad_ref: answer says "the text", "the passage", "according to the provided"
- bad_website: answer says "visit the website" or "check stevens.edu"
- too_generic: answer could apply to any university, not Stevens-specific

EXAMPLES TO SCORE:
{examples}

Return a JSON array with EXACTLY {n} objects, one per example, in order:
[{{"id": 1, "accuracy": X, "naturalness": X, "helpfulness": X, "formatting": X, "avg_score": X.X, "bad_ref": bool, "bad_website": bool, "too_generic": bool}}]"""

BATCH_MULTITURN_PROMPT = """You are a quality reviewer for an academic advisor chatbot training dataset.

Score EACH of the following {n} multi-turn conversations on a 1-5 scale.

For each conversation, evaluate:
- coherence: Do turns flow naturally? (5=natural, 1=disjointed)
- informativeness: Does each advisor turn add NEW info? (5=informative, 1=repetitive)
- naturalness: Do messages sound real? (5=natural, 1=robotic)
- formatting: Good markdown, right lengths? (5=excellent, 1=poor)

CONVERSATIONS:
{examples}

Return a JSON array with EXACTLY {n} objects, one per conversation, in order:
[{{"id": 1, "coherence": X, "informativeness": X, "naturalness": X, "formatting": X, "avg_score": X.X}}]"""


def call_gemini_batch(model, prompt: str, retries: int = 3):
    for attempt in range(retries):
        try:
            resp = model.generate_content(prompt)
            time.sleep(GEMINI_CALL_DELAY)
            return json.loads(resp.text)
        except json.JSONDecodeError:
            log.warning("JSON parse error (attempt %d)", attempt + 1)
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            err = str(e)
            etype = type(e).__name__
            log.debug("Exception type=%s msg=%s", etype, err[:300])

            if etype == "NotFound" or ("404" in err and "is not found for API version" in err):
                log.error("MODEL NOT FOUND: %s — update GEMINI_SCORING_MODEL in config.py", GEMINI_SCORING_MODEL)
                sys.exit(1)
            if "API_KEY_INVALID" in err:
                log.error("INVALID API KEY")
                sys.exit(1)
            if etype == "PermissionDenied" or ("403" in err and "SERVICE_DISABLED" in err):
                log.error("403 PERMISSION DENIED — enable Generative Language API or check key")
                sys.exit(1)
            if "429" in err or "quota" in err.lower() or "resource" in err.lower() or etype == "ResourceExhausted":
                wait = 30 * (attempt + 1)
                log.warning("Rate limited, waiting %ds... (%s)", wait, err[:100])
                time.sleep(wait)
            else:
                log.warning("Gemini error (attempt %d, %s): %s", attempt + 1, etype, err[:300])
                if attempt < retries - 1:
                    time.sleep(3)
    return None


# ═══════════════════════════════════════════════════════════════════════
# Data loading
# ═══════════════════════════════════════════════════════════════════════

def load_all_generated() -> list[dict]:
    records = []
    for path in [SINGLE_TURN_QA_PATH, COMPARATIVE_QA_PATH, REFUSAL_QA_PATH]:
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    log.info("Loaded %d single/comparative/refusal records", len(records))
    return records


def load_multiturn() -> list[dict]:
    records = []
    if MULTITURN_QA_PATH.exists():
        with open(MULTITURN_QA_PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    log.info("Loaded %d multi-turn records", len(records))
    return records


def load_scored_ids() -> set:
    scored = set()
    if SCORED_QA_PATH.exists():
        with open(SCORED_QA_PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    scored.add(score_key(r))
                except json.JSONDecodeError:
                    continue
    return scored


def score_key(record: dict) -> str:
    if record.get("type") == "multiturn":
        return record.get("source_id", "") + "|multiturn"
    return record.get("source_id", "") + "|" + record.get("question", "")[:50]


def quick_filter(record: dict) -> bool:
    """Fast pre-filter — no API calls."""
    if record.get("type") == "multiturn":
        return len(record.get("messages", [])) >= 4

    q = record.get("question", "")
    a = record.get("answer", "")
    if len(q) < 10 or len(a) < 30:
        return False

    a_lower = a.lower()
    bad = ["the text", "the passage", "the provided", "the snippet",
           "the context", "based on the given", "not specified in"]
    return not any(p in a_lower for p in bad)


def append_jsonl(path: Path, records: list[dict]):
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# Batch scoring logic
# ═══════════════════════════════════════════════════════════════════════

def _call_scorer(backend: str, model_or_client, prompt: str) -> list | None:
    """Dispatch a scoring call to the active backend."""
    if backend == "lmstudio":
        return call_lmstudio_batch(model_or_client, prompt)
    return call_gemini_batch(model_or_client, prompt)


def score_single_batch(backend: str, model_or_client, batch: list[dict]) -> list[dict | None]:
    """Score a batch of single-turn records in one API call."""
    examples_text = ""
    for i, rec in enumerate(batch, 1):
        examples_text += f"\n[{i}] Question: {rec['question'][:300]}\n    Answer: {rec['answer'][:500]}\n"

    prompt = BATCH_SCORE_PROMPT.format(n=len(batch), examples=examples_text)
    result = _call_scorer(backend, model_or_client, prompt)

    if not result or not isinstance(result, list):
        return [None] * len(batch)

    while len(result) < len(batch):
        result.append(None)

    return result[:len(batch)]


def score_multiturn_batch(backend: str, model_or_client, batch: list[dict]) -> list[dict | None]:
    """Score a batch of multi-turn conversations in one API call."""
    examples_text = ""
    for i, rec in enumerate(batch, 1):
        examples_text += f"\n--- Conversation [{i}] ---\n"
        for m in rec["messages"][:6]:
            role = "Student" if m["role"] == "user" else "AdvisorAI"
            examples_text += f"{role}: {m['content'][:200]}\n"

    prompt = BATCH_MULTITURN_PROMPT.format(n=len(batch), examples=examples_text)
    result = _call_scorer(backend, model_or_client, prompt)

    if not result or not isinstance(result, list):
        return [None] * len(batch)

    while len(result) < len(batch):
        result.append(None)

    return result[:len(batch)]


def passes_score(scores: dict, record_type: str = "single") -> bool:
    """Check if a scored record passes the quality threshold."""
    if not scores or not isinstance(scores, dict):
        return False

    avg = scores.get("avg_score", 0)
    if not avg:
        if record_type == "single":
            keys = ("accuracy", "naturalness", "helpfulness", "formatting")
        else:
            keys = ("coherence", "informativeness", "naturalness", "formatting")
        vals = [scores.get(k, 0) for k in keys if scores.get(k)]
        avg = sum(vals) / len(vals) if vals else 0
        scores["avg_score"] = round(avg, 1)

    if avg < MIN_SCORE_THRESHOLD:
        return False

    if record_type == "single":
        if scores.get("bad_ref") or scores.get("bad_website") or scores.get("too_generic"):
            return False

    return True


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def _resolve_backend(args) -> str:
    """Decide which scoring backend to use. CLI flags override config."""
    if args.no_api:
        return "no_api"
    if args.lmstudio:
        return "lmstudio"
    if args.gemini:
        return "gemini"
    # Fall back to config.py / env var
    return SCORING_BACKEND.lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-api", action="store_true",
                        help="Skip API scoring — only run fast local filter")
    parser.add_argument("--lmstudio", action="store_true",
                        help="Use LM Studio local model (Qwen) instead of Gemini")
    parser.add_argument("--gemini", action="store_true",
                        help="Use Gemini API (overrides SCORING_BACKEND config)")
    args = parser.parse_args()

    backend = _resolve_backend(args)
    log.info("Resolved scoring backend: %s (config default: %s)", backend, SCORING_BACKEND)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    single_records = load_all_generated()
    multi_records = load_multiturn()
    scored_ids = load_scored_ids()

    # Pre-filter (always runs — free, instant)
    pre_count = len(single_records) + len(multi_records)
    single_records = [r for r in single_records if quick_filter(r)]
    multi_records = [r for r in multi_records if quick_filter(r)]
    post_count = len(single_records) + len(multi_records)
    log.info("Pre-filter: %d → %d records (removed %d)", pre_count, post_count, pre_count - post_count)

    # Remove already-scored
    single_todo = [r for r in single_records if score_key(r) not in scored_ids]
    multi_todo = [r for r in multi_records if score_key(r) not in scored_ids]
    log.info("Already scored: %d — remaining: %d single + %d multi-turn",
             len(scored_ids), len(single_todo), len(multi_todo))

    if backend == "no_api":
        log.info("--no-api mode: writing all pre-filtered records without API scoring")
        for r in single_todo:
            r["scores"] = {"avg_score": 0, "mode": "no_api_filter"}
        for r in multi_todo:
            r["scores"] = {"avg_score": 0, "mode": "no_api_filter"}
        append_jsonl(SCORED_QA_PATH, single_todo + multi_todo)
        total = len(scored_ids) + len(single_todo) + len(multi_todo)
        log.info("Wrote %d records (no-api mode). Total in file: %d", len(single_todo) + len(multi_todo), total)
        print(f"\nDone! Total records in {SCORED_QA_PATH}: {total}")
        return

    # ── Initialise the selected backend ──
    if backend == "lmstudio":
        model_or_client = init_lmstudio()
        batch_size = LMSTUDIO_BATCH_SIZE
        model_label = f"LM Studio @ {LMSTUDIO_BASE_URL}"
    elif backend == "gemini":
        model_or_client = init_gemini()
        batch_size = SCORING_BATCH_SIZE
        model_label = GEMINI_SCORING_MODEL
    else:
        sys.exit(f"ERROR: Unknown SCORING_BACKEND '{backend}'. Use 'gemini' or 'lmstudio'.")

    log.info("Backend: %s | batch size: %d", model_label, batch_size)

    # Score single-turn in batches
    kept, dropped, errors = 0, 0, 0
    total_batches = (len(single_todo) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(single_todo), batch_size):
        batch = single_todo[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        results = score_single_batch(backend, model_or_client, batch)

        to_write = []
        for rec, scores in zip(batch, results):
            if scores and passes_score(scores, "single"):
                rec["scores"] = scores
                rec["scores"]["scored_by"] = backend
                to_write.append(rec)
                kept += 1
            elif scores:
                dropped += 1
            else:
                errors += 1

        if to_write:
            append_jsonl(SCORED_QA_PATH, to_write)

        if batch_num % 50 == 0 or batch_num == total_batches:
            log.info(
                "Batch %d/%d | kept=%d dropped=%d errors=%d | keep_rate=%.1f%%",
                batch_num, total_batches, kept, dropped, errors,
                kept / (kept + dropped) * 100 if (kept + dropped) > 0 else 0,
            )

    log.info("Single-turn done: kept=%d dropped=%d errors=%d", kept, dropped, errors)

    # Score multi-turn in batches
    mt_kept, mt_dropped, mt_errors = 0, 0, 0
    mt_batches = (len(multi_todo) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(multi_todo), batch_size):
        batch = multi_todo[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        results = score_multiturn_batch(backend, model_or_client, batch)

        to_write = []
        for rec, scores in zip(batch, results):
            if scores and passes_score(scores, "multiturn"):
                rec["scores"] = scores
                rec["scores"]["scored_by"] = backend
                to_write.append(rec)
                mt_kept += 1
            elif scores:
                mt_dropped += 1
            else:
                mt_errors += 1

        if to_write:
            append_jsonl(SCORED_QA_PATH, to_write)

        if batch_num % 50 == 0 or batch_num == mt_batches:
            log.info("Multi-turn batch %d/%d | kept=%d dropped=%d", batch_num, mt_batches, mt_kept, mt_dropped)

    log.info("Multi-turn done: kept=%d dropped=%d errors=%d", mt_kept, mt_dropped, mt_errors)

    # Final summary
    total_in_file = 0
    if SCORED_QA_PATH.exists():
        total_in_file = sum(1 for _ in open(SCORED_QA_PATH))

    print("\n" + "=" * 60)
    print("SCORING SUMMARY")
    print("=" * 60)
    print(f"  Backend: {model_label}")
    print(f"  Batch size: {batch_size}")
    print(f"  Single-turn: kept {kept}, dropped {dropped}, errors {errors}")
    print(f"  Multi-turn:  kept {mt_kept}, dropped {mt_dropped}, errors {mt_errors}")
    print(f"  Previously scored: {len(scored_ids)}")
    print(f"  Total in scored file: {total_in_file}")
    print(f"  Score threshold: >= {MIN_SCORE_THRESHOLD}")
    print(f"  Output: {SCORED_QA_PATH}")


if __name__ == "__main__":
    main()
