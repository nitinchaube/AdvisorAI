"""Web search agent."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from tools.web_tool import WebTool

logger = logging.getLogger("chatbot")


class WebAgent(BaseAgent):
    """Performs web searches for current / external information."""

    def __init__(self):
        super().__init__("web_agent")
        self.web_tool = WebTool()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        chroma_results = state.get("chroma_results", {})

        web_results = await self.web_tool.search_and_scrape(query, chroma_results)
        state["web_results"] = web_results

        return state
