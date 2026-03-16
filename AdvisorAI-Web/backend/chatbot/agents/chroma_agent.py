"""Chroma vector-search agent."""

import logging
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from tools.chroma_tool import ChromaTool

logger = logging.getLogger("chatbot")


class ChromaAgent(BaseAgent):
    """Searches the ChromaDB vector database for Stevens-specific data."""

    def __init__(self):
        super().__init__("chroma_agent")
        self.chroma_tool = ChromaTool()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")

        # Extract context for query rewriting on follow-ups.
        # Note: we use the raw chat_history string from the state (set by
        # the caller) rather than history_results because history_agent
        # runs in parallel and hasn't populated results yet.
        is_follow_up = state.get("is_follow_up", False)
        chat_history = None
        if is_follow_up:
            raw_history = state.get("chat_history", "")
            if raw_history:
                chat_history = self._parse_history_string(raw_history)

        try:
            results = await self.chroma_tool.search_collections(
                query,
                chat_history=chat_history,
                is_follow_up=is_follow_up,
            )
            state["chroma_results"] = results
            state["collections_searched"] = results.get("collections_used", [])
            logger.info(
                "ChromaAgent: %d docs from %s",
                len(results.get("documents", [])),
                results.get("collections_used", []),
            )
        except Exception as e:
            logger.error("ChromaAgent error: %s", e, exc_info=True)
            state["chroma_error"] = str(e)
            state["chroma_results"] = {"documents": [], "collections_used": [], "total_docs": 0}

        return state

    @staticmethod
    def _parse_history_string(raw: str) -> List[Dict[str, str]]:
        """Parse the Q:/A: formatted history string into a list of dicts."""
        entries: List[Dict[str, str]] = []
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
        if current.get("query"):
            entries.append(current)
        return entries[-3:]
