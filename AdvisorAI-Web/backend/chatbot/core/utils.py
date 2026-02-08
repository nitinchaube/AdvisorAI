"""
Shared utilities for the chatbot subsystem.
Provides JSON parsing, input sanitization, and response cleaning helpers.
"""

import json
import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("chatbot")


# ---------------------------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------------------------

def parse_llm_json(response_content: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from an LLM response with multiple fallback strategies.

    Strategy order:
    1. Direct JSON parse
    2. Extract JSON block from markdown fences
    3. Extract first {...} block via regex
    """
    if not response_content:
        return None

    text = response_content.strip()

    # Strategy 1 – direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2 – extract from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 3 – first {...} block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    logger.warning("Failed to parse JSON from LLM response: %s", text[:200])
    return None


def parse_llm_json_array(response_content: str) -> Optional[list]:
    """Parse a JSON array from an LLM response."""
    if not response_content:
        return None

    text = response_content.strip()

    # Direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # Extract from markdown fences
    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # First [...] block
    bracket_match = re.search(r"\[.*\]", text, re.DOTALL)
    if bracket_match:
        try:
            return json.loads(bracket_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------

_PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous",
    r"disregard\s+(all\s+)?above",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if",
    r"pretend\s+you\s+are",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"\[/INST\]",
]

_COMPILED_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in _PROMPT_INJECTION_PATTERNS
]


def sanitize_query(query: str, max_length: int = 2000) -> str:
    """
    Sanitize user input before embedding it in LLM prompts.

    - Truncates to *max_length* characters.
    - Strips control characters.
    - Removes known prompt-injection patterns (replaced with empty string).
    """
    if not query:
        return ""

    # Truncate
    text = query[:max_length]

    # Remove control characters (keep newlines & tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Strip injection patterns
    for pattern in _COMPILED_INJECTION_PATTERNS:
        text = pattern.sub("", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Response Cleaning
# ---------------------------------------------------------------------------

_REASONING_PREFIXES = re.compile(
    r"^(?:Let me think about this|I need to consider|Based on my analysis|"
    r"Let me analyze this|I should look into this|Let me check|"
    r"I'll need to|First, let me|To answer this|Looking at this|"
    r"I can see that|From what I can tell|It appears that|"
    r"I notice that|Based on the information|According to the data|"
    r"The information shows|I can determine that|After reviewing|"
    r"Upon examination)\.{0,3}\s*",
    re.IGNORECASE | re.MULTILINE,
)


def clean_response(text: str) -> str:
    """Remove reasoning artefacts and excessive whitespace from an LLM answer."""
    if not text:
        return ""

    text = _REASONING_PREFIXES.sub("", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    # Capitalise first letter if it became lowercase
    if text and text[0].islower():
        text = text[0].upper() + text[1:]

    return text
