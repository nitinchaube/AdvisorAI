"""Chroma vector-search agent."""

import logging
from typing import Dict, Any

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

        try:
            results = await self.chroma_tool.search_collections(query)
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
