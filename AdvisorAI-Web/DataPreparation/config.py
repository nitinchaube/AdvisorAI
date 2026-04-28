"""
Shared configuration for the AdvisorAI data preparation pipeline.
All paths, constants, prompts, and API settings live here.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # AdvisorAI/
WEB_ROOT = PROJECT_ROOT / "AdvisorAI-Web"

# Raw data sources
RAW_JSONL = WEB_ROOT / "data" / "stevens_qa_finetuning.jsonl"
COURSE_CSV = PROJECT_ROOT / "DataScrapper" / "CourseData" / "stevens_courses_full_details.csv"
UNIDATA_JSON = PROJECT_ROOT / "DataScrapper" / "UniversityData" / "UniData.json"
FACULTY_GENERAL = PROJECT_ROOT / "DataScrapper" / "AllFacultyGeneralInformation.json"
FACULTY_RESEARCH = PROJECT_ROOT / "DataScrapper" / "AllFacultyResearchInformaion.json"
FACULTY_SCHOOLS = {
    "Schaefer School of Engineering & Science": PROJECT_ROOT / "DataScrapper" / "ProfessorData" / "Schafer_school" / "faculty_directory1.csv",
    "School of Business": PROJECT_ROOT / "DataScrapper" / "ProfessorData" / "Business_school" / "faculty_directory1.csv",
    "College of Arts & Letters": PROJECT_ROOT / "DataScrapper" / "ProfessorData" / "HASS_school" / "faculty_directory1.csv",
}

# Output paths (all inside DataPreparation/)
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CLEAN_CONTEXTS_PATH = OUTPUT_DIR / "clean_contexts.json"
SINGLE_TURN_QA_PATH = OUTPUT_DIR / "single_turn_qa.jsonl"
COMPARATIVE_QA_PATH = OUTPUT_DIR / "comparative_qa.jsonl"
MULTITURN_QA_PATH = OUTPUT_DIR / "multiturn_qa.jsonl"
REFUSAL_QA_PATH = OUTPUT_DIR / "refusals.jsonl"
SCORED_QA_PATH = OUTPUT_DIR / "scored_qa.jsonl"
FINAL_DATASET_PATH = OUTPUT_DIR / "advisorai_finetune_v2.jsonl"

# ── Cleaning thresholds ────────────────────────────────────────────────

MIN_CONTEXT_LENGTH = 150           # discard contexts shorter than this
MAX_QA_PER_CONTEXT = 5             # cap Q&A pairs per single context (for existing data)
PDF_ARTIFACT_PATTERN = r"\(cid:\d+\)"

# ── Categories ─────────────────────────────────────────────────────────

CATEGORIES = [
    "course",
    "program",
    "faculty",
    "admissions",
    "financial",
    "campus_life",
    "library",
    "news",
    "general",
]

QA_COUNT_PER_CATEGORY = {
    "course": 3,
    "program": 6,
    "faculty": 3,
    "admissions": 8,
    "financial": 6,
    "campus_life": 4,
    "library": 3,
    "news": 3,
    "general": 4,
}

# ── Scoring backend selector ───────────────────────────────────────────
# Set to "gemini" to use Gemini API, or "lmstudio" to use a local model.
# The --lmstudio / --gemini CLI flags override this at runtime.

SCORING_BACKEND = os.getenv("SCORING_BACKEND", "lmstudio")   # "gemini" | "lmstudio"

# ── Gemini API ─────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_SCORING_MODEL = os.getenv("GEMINI_SCORING_MODEL", "gemini-2.5-flash")
GEMINI_TEMPERATURE = 0.7
GEMINI_TOP_P = 0.95
GEMINI_RPM_LIMIT = 450        # stay under 500 RPM free-tier limit
GEMINI_CALL_DELAY = 60.0 / GEMINI_RPM_LIMIT  # seconds between calls
SCORING_BATCH_SIZE = 10        # score N records per Gemini API call

# ── LM Studio (local Qwen / any model) ───────────────────────────────

LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:8080/v1")
LMSTUDIO_BATCH_SIZE = 3        # smaller batches → much better JSON reliability
LMSTUDIO_TEMPERATURE = 0.1     # low temp for consistent scoring
LMSTUDIO_CALL_DELAY = 0.5      # short delay between local calls

# ── Quality scoring ────────────────────────────────────────────────────

MIN_SCORE_THRESHOLD = 4        # keep only examples rated >= this

# ── AdvisorAI system prompt (used in final dataset) ────────────────────

SYSTEM_PROMPT = (
    "You are AdvisorAI, a knowledgeable and friendly academic advisor for "
    "Stevens Institute of Technology. You help students with courses, programs, "
    "admissions, faculty, campus life, and academic advising. Be specific — cite "
    "course codes, professor names, and requirements when available. Format "
    "responses using markdown. If you don't have information about something, "
    "say so honestly and offer to help with other Stevens-related questions."
)
