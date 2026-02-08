"""History tool – retrieves and parses conversation history."""

import logging
from typing import Dict, Any, List

from core.memory_store import get_memory_store

logger = logging.getLogger("chatbot")

# Indicators that suggest a follow-up or history-referencing query
_FOLLOW_UP_INDICATORS = frozenset(
    [
        "check again", "again", "more", "what else", "tell me more",
        "expand", "elaborate", "details", "continue", "go on",
        "what about", "how about", "try again", "repeat", "rephrase",
        "clarify", "previous question", "last question", "my previous question",
        "repeat that", "say that again", "can you repeat", "what was that",
        "remind me", "recall", "remember", "what did you say",
        "previous questions", "my previous questions",
        "what questions did i ask", "what did i ask", "show me my questions",
        "list my questions", "past questions", "conversation history", "chat history",
    ]
)

_FOLLOW_UP_PATTERNS = (
    "try again with", "check again", "what about",
    "tell me more about", "can you repeat", "say that again",
    "remind me", "what was", "can you clarify",
)

_FOLLOW_UP_PRONOUNS = {"it", "this", "that", "these", "those", "them", "they"}


class HistoryTool:
    """Access and parse conversation history."""

    def __init__(self):
        self.memory_store = get_memory_store()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_relevant_history(
        self,
        user_id: str,
        current_query: str,
        limit: int = 3,
        provided_history: str = "",
    ) -> Dict[str, Any]:
        """Return recent conversation history for context."""
        try:
            if provided_history:
                history_entries = self._parse_provided_history(provided_history)
                logger.debug(
                    "Parsed %d history entries from provided text", len(history_entries)
                )
            else:
                history_entries = await self.memory_store.get_conversation_history(
                    user_id, limit=limit
                )

            relevant = history_entries[-limit:] if history_entries else []

            return {
                "relevant_history": relevant,
                "total_history": len(history_entries),
                "relevant_count": len(relevant),
                "current_query": current_query,
                "is_follow_up": self.is_follow_up_query(current_query),
                "source": "provided" if provided_history else "memory",
            }

        except Exception as e:
            logger.error("HistoryTool error: %s", e, exc_info=True)
            return {
                "relevant_history": [],
                "total_history": 0,
                "relevant_count": 0,
                "is_follow_up": False,
                "source": "error",
                "error": str(e),
            }

    async def save_conversation(
        self, user_id: str, query: str, response: str, metadata: Dict = None
    ):
        try:
            await self.memory_store.save_conversation(user_id, query, response, metadata)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def clear_history(self, user_id: str) -> Dict[str, Any]:
        try:
            await self.memory_store.clear_history(user_id)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_follow_up_query(query: str) -> bool:
        """Determine whether *query* is a follow-up / history question."""
        q = query.lower().strip()

        if any(ind in q for ind in _FOLLOW_UP_INDICATORS):
            return True

        for pattern in _FOLLOW_UP_PATTERNS:
            if pattern in q:
                return True

        words = q.split()
        if len(words) <= 3 and any(w in _FOLLOW_UP_PRONOUNS for w in words):
            return True

        if len(q) <= 20 and any(w in q for w in ("more", "else", "and", "what", "how", "why")):
            return True

        return False

    @staticmethod
    def _parse_provided_history(raw: str) -> List[Dict]:
        """Parse ``Q: … / A: …`` formatted history text into a list of dicts."""
        entries: List[Dict] = []
        current: Dict[str, str] = {}

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("Q: "):
                if current.get("query"):
                    entries.append(current)
                current = {"query": line[3:].strip(), "response": ""}
            elif line.startswith("A: ") and current:
                current["response"] = line[3:].strip()
            elif current.get("query"):
                # Multi-line response continuation
                if current.get("response"):
                    current["response"] += " " + line

        if current.get("query"):
            entries.append(current)

        return entries
