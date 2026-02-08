"""History agent – retrieves conversation context."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from tools.history_tool import HistoryTool

logger = logging.getLogger("chatbot")


class HistoryAgent(BaseAgent):
    """Fetches relevant conversation history for context."""

    def __init__(self):
        super().__init__("history_agent")
        self.history_tool = HistoryTool()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_id = state.get("user_id", "default")
        query = state.get("query", "")
        provided_history = state.get("chat_history", "")

        results = await self.history_tool.get_relevant_history(
            user_id=user_id,
            current_query=query,
            provided_history=provided_history,
        )
        state["history_results"] = results

        return state
