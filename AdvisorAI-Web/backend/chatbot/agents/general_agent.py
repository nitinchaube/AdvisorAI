from typing import Dict, Any
from agents.base_agent import BaseAgent
from tools.general_tool import GeneralTool

class GeneralAgent(BaseAgent):
    """Agent for handling general knowledge questions"""
    
    def __init__(self):
        super().__init__("general_agent")
        self.general_tool = GeneralTool()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process general questions"""
        query = state.get("query", "")
        
        # First, classify the question type
        classification_result = await self.general_tool.classify_question_type(query)
        
        if classification_result.get("success") and classification_result.get("classification") == "general":
            # This is a general question, use the general tool
            general_result = await self.general_tool.answer_general_question(query)
            
            if general_result.get("success"):
                state["general_answer"] = general_result.get("answer")
                state["used_general_tool"] = True
                state["question_type"] = "general"
            else:
                state["general_error"] = general_result.get("error")
        else:
            # This is a domain-specific question, mark for other tools
            state["question_type"] = "domain_specific"
            state["used_general_tool"] = False
        
        return state
    
    async def get_general_knowledge(self, topic: str) -> Dict[str, Any]:
        """Get general knowledge about a specific topic"""
        return await self.general_tool.get_general_knowledge(topic) 