"""General-knowledge agent – delegates to GeneralTool without redundant classification."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from tools.general_tool import GeneralTool

logger = logging.getLogger("chatbot")


class GeneralAgent(BaseAgent):
    """Handles general knowledge questions.

    Note: The router has already classified this query as 'general',
    so we skip the redundant LLM classification call and go straight
    to answer generation.
    """

    def __init__(self):
        super().__init__("general_agent")
        self.general_tool = GeneralTool()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")

        result = await self.general_tool.answer_general_question(query)

        if result.get("success"):
            state["general_answer"] = result.get("answer")
            state["used_general_tool"] = True
        else:
            state["general_error"] = result.get("error")
            state["used_general_tool"] = False

        return state
