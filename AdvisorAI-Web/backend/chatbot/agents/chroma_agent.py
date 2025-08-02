from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from tools.chroma_tool import ChromaTool
from core.llm_router import LLMRouter
import json

class ChromaAgent(BaseAgent):
    """Agent for handling Chroma vector database operations using RAG service logic"""

    def __init__(self):
        super().__init__("chroma_agent")
        self.chroma_tool = ChromaTool()
        self.llm_router = LLMRouter()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process Chroma-related operations using RAG service logic"""
        query = state.get("query", "")
        
        # Use RAG service logic for collection routing and document retrieval
        try:
            # Search collections using RAG service approach
            search_results = await self.chroma_tool.search_collections(query)
            
            # Update state with search results
            state["chroma_results"] = search_results
            state["collections_searched"] = search_results.get("collections_used", [])
            
            print(f"Chroma search completed: {len(search_results.get('documents', []))} documents from {len(search_results.get('collections_used', []))} collections")
            
        except Exception as e:
            state["chroma_error"] = str(e)
            state["chroma_results"] = {
                "documents": [],
                "collections_used": [],
                "total_docs": 0
            }
            print(f"Chroma search error: {e}")
        
        return state 