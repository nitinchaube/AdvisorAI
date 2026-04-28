#!/usr/bin/env python3
"""
Interactive chat with the fine-tuned model — for quick sanity testing.

Run from Fine_tuning/ root:
    python src/test_chat.py                         # loads merged model
    python src/test_chat.py --model-path <path>     # specific model
    python src/test_chat.py --adapter <adapter-path>  # load adapter on base model

Type your question at the prompt. Type 'quit', 'exit', or Ctrl-C to stop.
Type 'clear' to reset the conversation.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.training_config import BASE_MODEL, CHECKPOINT_DIR, MERGED_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are AdvisorAI, a knowledgeable and friendly academic advisor for "
    "Stevens Institute of Technology. You help students with courses, programs, "
    "admissions, faculty, campus life, and academic advising. Be specific — cite "
    "course codes, professor names, and requirements when available. Format "
    "responses using markdown. If you don't have information about something, "
    "say so honestly and offer to help with other Stevens-related questions."
)


def load_model(model_path: str | None, adapter_path: str | None):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if adapter_path:
        from peft import PeftModel
        log.info("Loading base model %s ...", BASE_MODEL)
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        log.info("Loading adapter from %s ...", adapter_path)
        model = PeftModel.from_pretrained(base, adapter_path)
        model = model.merge_and_unload()
    else:
        mp = model_path or str(MERGED_DIR)
        log.info("Loading model from %s ...", mp)
        tokenizer = AutoTokenizer.from_pretrained(mp, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            mp,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    return model, tokenizer


def generate(model, tokenizer, messages, max_new_tokens=512, temperature=0.3, top_p=0.9):
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.05,
        )
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default=None,
                        help="Path to merged model (default: Fine_tuning/checkpoints/advisorai-qwen2.5-14b-merged)")
    parser.add_argument("--adapter", type=str, default=None,
                        help="Path to LoRA/DoRA adapter (applied to base model on-the-fly)")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    args = parser.parse_args()

    # If neither provided, try adapter from last checkpoint
    if not args.model_path and not args.adapter:
        final_adapter = CHECKPOINT_DIR / "final"
        if not Path(MERGED_DIR).exists() and final_adapter.exists():
            log.info("Merged model not found — falling back to adapter %s", final_adapter)
            args.adapter = str(final_adapter)

    model, tokenizer = load_model(args.model_path, args.adapter)
    log.info("Ready! Type a question, 'clear' to reset, or 'quit' to exit.")
    log.info("(temperature=%.2f, top_p=%.2f, max_new_tokens=%d)",
             args.temperature, args.top_p, args.max_new_tokens)
    print()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("(conversation reset)\n")
            continue

        messages.append({"role": "user", "content": user_input})
        print("AdvisorAI: ", end="", flush=True)
        response = generate(
            model, tokenizer, messages,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
        )
        print(response + "\n")
        messages.append({"role": "assistant", "content": response})

    print("Goodbye!")


if __name__ == "__main__":
    main()
