from typing import Dict, Any
from agents.base_agent import BaseAgent
from tools.web_tool import WebTool

class WebAgent(BaseAgent):
    """Agent for handling web search operations"""

    def __init__(self):
        super().__init__("web_agent")
        self.web_tool = WebTool()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process web search operations"""
        query = state.get("query", "")
        chroma_results = state.get("chroma_results", {})
        
        # Perform web search with Chroma results for smart decision making
        web_results = await self.web_tool.search_and_scrape(query, chroma_results)
        state["web_results"] = web_results
        
        return state 