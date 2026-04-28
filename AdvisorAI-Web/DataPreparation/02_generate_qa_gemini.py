#!/usr/bin/env python3
"""
Step 2: Generate Q&A training data from clean contexts using Gemini API.

Generates four types of data:
  A. Single-turn Q&A      (one question → one answer per context)
  B. Comparative Q&A       (cross-context reasoning questions)
  C. Multi-turn dialogues  (2-4 turn conversations)
  D. Boundary/refusal      (identity, off-topic, safety)

Outputs:
  output/single_turn_qa.jsonl
  output/comparative_qa.jsonl
  output/multiturn_qa.jsonl
  output/refusals.jsonl

Run:
  GEMINI_API_KEY=your_key python 02_generate_qa_gemini.py [--part A|B|C|D|all]

Each part can be run independently. Progress is saved incrementally so
you can resume after interruptions.
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import google.generativeai as genai

from config import (
    CLEAN_CONTEXTS_PATH,
    COMPARATIVE_QA_PATH,
    GEMINI_API_KEY,
    GEMINI_CALL_DELAY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
    MULTITURN_QA_PATH,
    OUTPUT_DIR,
    QA_COUNT_PER_CATEGORY,
    REFUSAL_QA_PATH,
    SINGLE_TURN_QA_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# Gemini client setup
# ═══════════════════════════════════════════════════════════════════════

API_KEY = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    sys.exit("ERROR: Set GEMINI_API_KEY environment variable or in config.py")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    GEMINI_MODEL,
    generation_config={
        "temperature": GEMINI_TEMPERATURE,
        "top_p": GEMINI_TOP_P,
        "response_mime_type": "application/json",
    },
)


def call_gemini(prompt: str, retries: int = 3) -> dict | list | None:
    """Call Gemini with retry logic and rate-limit delay."""
    for attempt in range(retries):
        try:
            resp = model.generate_content(prompt)
            time.sleep(GEMINI_CALL_DELAY)
            parsed = json.loads(resp.text)
            return parsed
        except json.JSONDecodeError:
            log.warning("JSON parse error (attempt %d), raw: %s", attempt + 1, resp.text[:200])
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            err = str(e)
            if "404" in err or "not found" in err.lower():
                log.error("MODEL NOT FOUND: %s — update GEMINI_MODEL in config.py", GEMINI_MODEL)
                sys.exit(1)
            if "API_KEY_INVALID" in err or "api key not valid" in err.lower():
                log.error("INVALID API KEY — set correct GEMINI_API_KEY (should start with AIzaSy...)")
                sys.exit(1)
            if "403" in err or "permission" in err.lower() or "service_disabled" in err.lower() or "disabled" in err.lower():
                log.error(
                    "403 PERMISSION DENIED — your API key is from a project that hasn't "
                    "enabled the Generative Language API, OR it's a service account key "
                    "(starts with AQ.) instead of an API key (starts with AIzaSy...).\n"
                    "Fix: use the API key from https://aistudio.google.com/apikey"
                )
                sys.exit(1)
            if "429" in err or "quota" in err.lower() or "resource" in err.lower():
                wait = 15 * (attempt + 1)
                log.warning("Rate limited, waiting %ds...", wait)
                time.sleep(wait)
            elif "500" in err or "503" in err:
                log.warning("Server error (attempt %d): %s", attempt + 1, err[:100])
                time.sleep(5 * (attempt + 1))
            else:
                log.error("Gemini error (attempt %d): %s", attempt + 1, err[:300])
                if attempt < retries - 1:
                    time.sleep(3)
    return None


def load_contexts() -> list[dict]:
    with open(CLEAN_CONTEXTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_progress(path: Path) -> set:
    """Load already-processed context IDs to support resume."""
    done = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    done.add(row.get("source_id", ""))
                except json.JSONDecodeError:
                    continue
    return done


def append_jsonl(path: Path, records: list[dict]):
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# Part A: Single-turn Q&A generation
# ═══════════════════════════════════════════════════════════════════════

SINGLE_TURN_PROMPT = """You are generating training data for AdvisorAI, an academic advisor chatbot for Stevens Institute of Technology.

Given the following information about Stevens, generate exactly {n} training examples (question + answer pairs).

CATEGORY: {category}

SOURCE INFORMATION:
{context}

REQUIREMENTS FOR QUESTIONS:
- Sound like real students typing in a chat — natural, sometimes informal, varying lengths
- Mix of types: direct factual, practical "how do I...", inferential, and conversational
- NEVER reference "the text" or "the passage" — students don't have the text
- Include both short ("credits for CS 590?") and longer questions ("I'm interested in machine learning — what courses should I take at Stevens?")

REQUIREMENTS FOR ANSWERS:
- Write as AdvisorAI — warm, knowledgeable, specific, helpful
- Include specific details: course codes, professor names, credit counts, dates when available
- Use markdown: **bold** for key terms, bullet points for lists, `backticks` for course codes
- 2-4 sentences for simple factual questions, up to a full paragraph for complex ones
- NEVER say "according to the text" or "the passage states" — speak as your own knowledge
- NEVER say "visit the website" or "check the website" — AdvisorAI IS the resource
- When natural, end with a brief follow-up offer ("Would you like more details on any of these?")

Return a JSON array of objects:
[{{"question": "...", "answer": "..."}}]"""


def generate_single_turn():
    """Generate single-turn Q&A for each clean context."""
    log.info("=== Part A: Single-turn Q&A generation ===")
    contexts = load_contexts()
    done = load_progress(SINGLE_TURN_QA_PATH)
    log.info("Loaded %d contexts, %d already processed", len(contexts), len(done))

    total_generated = len(done)
    for i, ctx in enumerate(contexts):
        if ctx["id"] in done:
            continue

        n = QA_COUNT_PER_CATEGORY.get(ctx["category"], 3)
        # Cap very long contexts to avoid token waste
        text = ctx["text"][:6000]

        prompt = SINGLE_TURN_PROMPT.format(n=n, category=ctx["category"], context=text)
        result = call_gemini(prompt)

        if not result or not isinstance(result, list):
            log.warning("Skipping context %s — invalid response", ctx["id"])
            continue

        records = []
        for qa in result:
            if isinstance(qa, dict) and qa.get("question") and qa.get("answer"):
                records.append({
                    "source_id": ctx["id"],
                    "category": ctx["category"],
                    "source_type": ctx["source"],
                    "question": qa["question"].strip(),
                    "answer": qa["answer"].strip(),
                    "type": "single_turn",
                })
        if records:
            append_jsonl(SINGLE_TURN_QA_PATH, records)
            total_generated += len(records)
            done.add(ctx["id"])

        if (i + 1) % 100 == 0:
            log.info("Progress: %d/%d contexts, %d Q&A generated", i + 1, len(contexts), total_generated)

    log.info("Part A complete: %d total Q&A pairs in %s", total_generated, SINGLE_TURN_QA_PATH)


# ═══════════════════════════════════════════════════════════════════════
# Part B: Comparative / cross-context Q&A
# ═══════════════════════════════════════════════════════════════════════

COMPARATIVE_PROMPT = """You are generating training data for AdvisorAI, an academic advisor chatbot for Stevens Institute of Technology.

Given these {n} related pieces of information, generate 3 questions a student would ask when COMPARING or CHOOSING between these options, plus detailed answers that reference information from multiple sources.

{contexts}

Questions should be like:
- "What's the difference between X and Y at Stevens?"
- "I'm interested in Z — which program/course is better for me?"
- "Can I combine X with Y?"
- "If I have background A, should I pick X or Y?"

Answers should compare/contrast specifically, citing details from BOTH sources.

Return JSON: [{{"question": "...", "answer": "..."}}]"""

COMPARISON_GROUPS = {
    "cs_programs": {"category": "program", "keywords": ["computer science", "software", "machine learning", "artificial intelligence", "data science"]},
    "engineering": {"category": "program", "keywords": ["engineering", "mechanical", "electrical", "civil", "chemical", "biomedical"]},
    "business": {"category": "program", "keywords": ["business", "mba", "finance", "analytics", "management"]},
    "math_programs": {"category": "program", "keywords": ["math", "applied math", "statistics"]},
    "ai_courses": {"category": "course", "keywords": ["machine learning", "deep learning", "ai", "artificial intelligence", "neural"]},
    "programming_courses": {"category": "course", "keywords": ["python", "java", "c++", "programming", "software"]},
    "data_courses": {"category": "course", "keywords": ["data mining", "data science", "database", "big data", "analytics"]},
}


def generate_comparative():
    """Generate cross-context comparative Q&A."""
    log.info("=== Part B: Comparative Q&A generation ===")
    contexts = load_contexts()
    done = load_progress(COMPARATIVE_QA_PATH)
    log.info("Already have %d comparative records", len(done))

    by_category = defaultdict(list)
    for ctx in contexts:
        by_category[ctx["category"]].append(ctx)

    total = 0
    for group_name, spec in COMPARISON_GROUPS.items():
        cat_contexts = by_category.get(spec["category"], [])
        matching = [
            c for c in cat_contexts
            if any(kw in c["text"].lower() for kw in spec["keywords"])
        ]

        if len(matching) < 2:
            log.info("Skipping group '%s' — only %d matching contexts", group_name, len(matching))
            continue

        random.shuffle(matching)
        # Generate comparisons from pairs/triples
        for i in range(0, min(len(matching) - 1, 20), 2):
            group = matching[i:i + 3]
            group_id = f"comp_{group_name}_{i}"
            if group_id in done:
                continue

            contexts_text = "\n\n---\n\n".join(
                [f"[Source {j + 1}]:\n{c['text'][:3000]}" for j, c in enumerate(group)]
            )
            prompt = COMPARATIVE_PROMPT.format(n=len(group), contexts=contexts_text)
            result = call_gemini(prompt)

            if not result or not isinstance(result, list):
                continue

            records = []
            for qa in result:
                if isinstance(qa, dict) and qa.get("question") and qa.get("answer"):
                    records.append({
                        "source_id": group_id,
                        "category": spec["category"],
                        "source_type": "comparative",
                        "question": qa["question"].strip(),
                        "answer": qa["answer"].strip(),
                        "type": "comparative",
                        "group": group_name,
                    })
            if records:
                append_jsonl(COMPARATIVE_QA_PATH, records)
                total += len(records)
                done.add(group_id)

    log.info("Part B complete: %d comparative Q&A pairs", total)


# ═══════════════════════════════════════════════════════════════════════
# Part C: Multi-turn conversations
# ═══════════════════════════════════════════════════════════════════════

MULTITURN_PROMPT = """You are generating training data for AdvisorAI, an academic advisor chatbot for Stevens Institute of Technology.

Given the following information about a Stevens topic, create a realistic 3-4 turn conversation between a student and AdvisorAI.

TOPIC: {topic}

SOURCE INFORMATION:
{context}

CONVERSATION REQUIREMENTS:
- The student starts with a broad question, then drills down with follow-ups
- Student messages should sound natural — informal, sometimes short ("oh cool, what about the prereqs?")
- AdvisorAI responses should be warm, specific, and use markdown formatting
- Each AdvisorAI turn should add NEW information (not repeat previous answers)
- The conversation should feel like a real advising session, not a scripted Q&A

Return JSON:
{{"messages": [
  {{"role": "user", "content": "..."}},
  {{"role": "assistant", "content": "..."}},
  {{"role": "user", "content": "..."}},
  {{"role": "assistant", "content": "..."}}
]}}"""


def generate_multiturn():
    """Generate multi-turn conversation examples."""
    log.info("=== Part C: Multi-turn conversation generation ===")
    contexts = load_contexts()
    done = load_progress(MULTITURN_QA_PATH)
    log.info("Already have %d multi-turn records", len(done))

    # Pick rich contexts (longer text = more material for multi-turn)
    rich = [c for c in contexts if len(c["text"]) > 800 and c["category"] in (
        "program", "course", "admissions", "faculty", "financial", "campus_life"
    )]
    random.shuffle(rich)
    target = 4000
    total = len(done)

    for i, ctx in enumerate(rich):
        if total >= target:
            break
        if ctx["id"] in done:
            continue

        topic = ctx["category"].replace("_", " ").title()
        text = ctx["text"][:5000]
        prompt = MULTITURN_PROMPT.format(topic=topic, context=text)
        result = call_gemini(prompt)

        if not result or not isinstance(result, dict) or "messages" not in result:
            continue

        messages = result["messages"]
        if len(messages) < 4:
            continue

        valid = all(
            isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
            for m in messages
        )
        if not valid:
            continue

        record = {
            "source_id": ctx["id"],
            "category": ctx["category"],
            "source_type": "multiturn",
            "messages": messages,
            "type": "multiturn",
        }
        append_jsonl(MULTITURN_QA_PATH, [record])
        total += 1
        done.add(ctx["id"])

        if (i + 1) % 100 == 0:
            log.info("Progress: %d multi-turn conversations generated", total)

    log.info("Part C complete: %d multi-turn conversations", total)


# ═══════════════════════════════════════════════════════════════════════
# Part D: Boundary / refusal examples
# ═══════════════════════════════════════════════════════════════════════

REFUSAL_PROMPT = """You are generating training data for AdvisorAI, an academic advisor chatbot for Stevens Institute of Technology.

Generate {n} realistic examples where a student asks something that AdvisorAI should handle carefully.

CATEGORY: {category}
DESCRIPTION: {description}

EXAMPLE SEED QUESTIONS (generate MORE like these, with variations):
{examples}

ANSWER REQUIREMENTS:
- Be polite but firm
- NEVER reveal underlying technology (no mentions of AI models, databases, APIs, etc.)
- For identity questions: always say "I'm AdvisorAI, your personal academic advisor for Stevens Institute of Technology"
- For off-topic: gently redirect to Stevens-related topics
- For unknown info: honestly say you don't have that specific information, then offer what you CAN help with
- For harmful/inappropriate: politely decline and redirect to Stevens topics
- Keep responses 1-3 sentences — concise and warm

Return JSON: [{{"question": "...", "answer": "..."}}]"""

REFUSAL_CATEGORIES = {
    "identity": {
        "n": 40,
        "description": "Student asks about AdvisorAI's identity, what AI it uses, or its technology stack",
        "examples": [
            "Are you ChatGPT?", "What model powers you?", "Are you made by Google?",
            "What's your tech stack?", "Do you use LangChain?", "Are you an AI?",
            "Who created you?", "What database do you use?", "What LLM are you?",
        ],
    },
    "off_topic": {
        "n": 40,
        "description": "Student asks something completely unrelated to Stevens or academics",
        "examples": [
            "What's the weather today?", "Write me a poem", "Who won the Super Bowl?",
            "What's the capital of France?", "Tell me a joke", "What's Bitcoin price?",
            "Help me with my taxes", "What's the best Netflix show?",
        ],
    },
    "unknown_info": {
        "n": 50,
        "description": "Student asks about something Stevens-related but that AdvisorAI doesn't have specific information about (future dates, personal records, very specific policies)",
        "examples": [
            "What will tuition be in 2030?", "What's my GPA?", "When will I get my acceptance letter?",
            "Can you check my financial aid status?", "What grade did I get in CS 590?",
            "Will Stevens add a medical school?", "How many applicants this year?",
        ],
    },
    "harmful": {
        "n": 30,
        "description": "Student asks something inappropriate, harmful, or tries to misuse the chatbot (cheating, hacking, etc.)",
        "examples": [
            "Write my thesis for me", "How do I hack the grading system?",
            "Give me the exam answers for CS 590", "Write my application essay",
            "Help me plagiarize this paper", "How do I cheat on the online exam?",
        ],
    },
    "sensitive_redirect": {
        "n": 20,
        "description": "Student mentions mental health, self-harm, or crisis situations — AdvisorAI should express care and direct them to appropriate Stevens resources",
        "examples": [
            "I'm feeling really overwhelmed and depressed",
            "I don't know if I can handle the stress anymore",
            "I'm struggling with anxiety about my grades",
        ],
    },
}


def generate_refusals():
    """Generate boundary/refusal training examples."""
    log.info("=== Part D: Boundary/refusal generation ===")
    done = load_progress(REFUSAL_QA_PATH)
    log.info("Already have %d refusal records", len(done))

    total = len(done)
    for cat_name, spec in REFUSAL_CATEGORIES.items():
        cat_id = f"refusal_{cat_name}"
        if cat_id in done:
            log.info("Skipping '%s' — already generated", cat_name)
            continue

        prompt = REFUSAL_PROMPT.format(
            n=spec["n"],
            category=cat_name,
            description=spec["description"],
            examples=json.dumps(spec["examples"]),
        )
        result = call_gemini(prompt)

        if not result or not isinstance(result, list):
            log.warning("Failed to generate '%s' refusals", cat_name)
            continue

        records = []
        for qa in result:
            if isinstance(qa, dict) and qa.get("question") and qa.get("answer"):
                records.append({
                    "source_id": cat_id,
                    "category": cat_name,
                    "source_type": "refusal",
                    "question": qa["question"].strip(),
                    "answer": qa["answer"].strip(),
                    "type": "refusal",
                })
        if records:
            append_jsonl(REFUSAL_QA_PATH, records)
            total += len(records)
            done.add(cat_id)
            log.info("Generated %d '%s' refusal examples", len(records), cat_name)

    log.info("Part D complete: %d refusal examples total", total)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Generate Q&A data with Gemini")
    parser.add_argument(
        "--part",
        choices=["A", "B", "C", "D", "all"],
        default="all",
        help="Which part to run: A=single-turn, B=comparative, C=multi-turn, D=refusals, all=everything",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(42)

    parts = {
        "A": generate_single_turn,
        "B": generate_comparative,
        "C": generate_multiturn,
        "D": generate_refusals,
    }

    if args.part == "all":
        for name, fn in parts.items():
            log.info("Running Part %s...", name)
            fn()
    else:
        parts[args.part]()

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    for name, path in [
        ("Single-turn", SINGLE_TURN_QA_PATH),
        ("Comparative", COMPARATIVE_QA_PATH),
        ("Multi-turn", MULTITURN_QA_PATH),
        ("Refusals", REFUSAL_QA_PATH),
    ]:
        if path.exists():
            count = sum(1 for _ in open(path))
            size = path.stat().st_size / 1024
            print(f"  {name:15s}: {count:>6,} records ({size:.1f} KB)")
        else:
            print(f"  {name:15s}: not generated yet")


if __name__ == "__main__":
    main()
