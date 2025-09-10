from typing import Dict, Any
from agents.base_agent import BaseAgent
from tools.history_tool import HistoryTool

class HistoryAgent(BaseAgent):
    """Agent for handling conversation history"""
    
    def __init__(self):
        super().__init__("history_agent")
        self.history_tool = HistoryTool()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process history-related operations"""
        user_id = state.get("user_id", "default")
        query = state.get("query", "")
        provided_history = state.get("chat_history", "")  # Get provided history from state
        
        # Get relevant history
        history_results = await self.history_tool.get_relevant_history(
            user_id=user_id,
            current_query=query,
            provided_history=provided_history  # Pass the provided history
        )
        
        state["history_results"] = history_results
        
        return state 