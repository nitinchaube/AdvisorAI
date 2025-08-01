#!/usr/bin/env python3
"""
Integration service for LangGraph chatbot agents into AdvisorAI
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime

# Add the chatbot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatbot'))

from chatbot.core.langgraph_graph import LangGraphOrchestrator
from chatbot.core.memory_store import get_memory_store
from chatbot.tools.chroma_tool import ChromaTool
from chatbot.tools.web_tool import WebTool

class ChatbotIntegrationService:
    """Integration service that wraps LangGraph chatbot agents for AdvisorAI"""
    
    def __init__(self):
        """Initialize the chatbot integration service"""
        self.orchestrator = None
        self.memory_store = get_memory_store()
        self.chroma_tool = ChromaTool()
        self.web_tool = WebTool()
        self._initialize_orchestrator()
    
    def _initialize_orchestrator(self):
        """Initialize the LangGraph orchestrator"""
        try:
            self.orchestrator = LangGraphOrchestrator()
            print("✅ LangGraph orchestrator initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing LangGraph orchestrator: {e}")
            self.orchestrator = None
    
    def process_query(self, user_query: str, user_id: str = None, 
                     chat_history: List[Dict] = None) -> Dict:
        """Process a query using the LangGraph chatbot agents"""
        
        start_time = time.time()
        
        try:
            if not self.orchestrator:
                return {
                    "response": "I apologize, but the chatbot system is currently unavailable. Please try again later.",
                    "sources": {},
                    "processing_time": time.time() - start_time,
                    "error": True
                }
            
            # Convert chat history to the format expected by the chatbot
            formatted_history = self._format_chat_history(chat_history or [])
            
            # Process query with LangGraph orchestrator, passing chat history
            result = asyncio.run(self.orchestrator.process_query(
                query=user_query,
                user_id=user_id or "default",
                chat_history=formatted_history  # Pass the formatted history
            ))
            
            if result["success"]:
                # Save conversation to memory store
                asyncio.run(self.memory_store.save_conversation(
                    user_id=user_id or "default",
                    query=user_query,
                    response=result["answer"],
                    metadata=result.get("metadata", {})
                ))
                
                # Format response for AdvisorAI compatibility
                response = {
                    "response": result["answer"],
                    "sources": {
                        "collections_used": result.get("metadata", {}).get("tools_used", []),
                        "documents_retrieved": 0,  # Will be updated if available
                        "web_search_performed": result.get("metadata", {}).get("web_search_performed", False),
                        "user_info_included": bool(user_id),
                        "chat_history_included": bool(formatted_history),
                        "top_documents": []
                    },
                    "processing_time": time.time() - start_time,
                    "error": False
                }
                
                # Add metadata from LangGraph result
                if "metadata" in result:
                    metadata = result["metadata"]
                    if "collections_searched" in metadata:
                        response["sources"]["collections_used"] = metadata["collections_searched"]
                    if "used_general_tool" in metadata:
                        response["sources"]["general_tool_used"] = metadata["used_general_tool"]
                    if "reasoning_result" in metadata:
                        response["sources"]["reasoning"] = metadata["reasoning_result"]
                
                return response
            else:
                # Log the actual error for debugging but show user-friendly message
                print(f"❌ Chatbot error: {result.get('error', 'Unknown error')}")
                return {
                    "response": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                    "sources": {},
                    "processing_time": time.time() - start_time,
                    "error": True
                }
                
        except Exception as e:
            # Log the actual error for debugging but show user-friendly message
            print(f"❌ Error in chatbot integration: {e}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                "sources": {},
                "processing_time": time.time() - start_time,
                "error": True
            }
    
    def _format_chat_history(self, chat_history: List[Dict]) -> str:
        """Format chat history for the chatbot"""
        if not chat_history:
            return ""
        
        formatted_parts = []
        for entry in chat_history[-10:]:  # Last 10 entries for better context
            if isinstance(entry, dict):
                # Handle both formats: frontend format and legacy format
                if 'role' in entry and 'content' in entry:
                    # Frontend format: {role: 'user'/'assistant', content: '...'}
                    role = entry.get('role', '')
                    content = entry.get('content', '')
                    if role and content:
                        if role == 'user':
                            formatted_parts.append(f"Q: {content}")
                        elif role == 'assistant':
                            formatted_parts.append(f"A: {content}")
                elif 'query' in entry and 'response' in entry:
                    # Legacy format: {query: '...', response: '...'}
                    query = entry.get('query', '')
                    response = entry.get('response', '')
                    if query and response:
                        formatted_parts.append(f"Q: {query}")
                        formatted_parts.append(f"A: {response}")
                elif 'type' in entry and 'content' in entry:
                    # Another possible format: {type: 'user'/'ai', content: '...'}
                    msg_type = entry.get('type', '')
                    content = entry.get('content', '')
                    if msg_type and content:
                        if msg_type == 'user':
                            formatted_parts.append(f"Q: {content}")
                        elif msg_type == 'ai':
                            formatted_parts.append(f"A: {content}")
        
        return "\n\n".join(formatted_parts)
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        try:
            chroma_stats = self.chroma_tool.get_collection_stats()
            return {
                "collections": chroma_stats,
                "total_collections": len(chroma_stats),
                "web_search_enabled": self.web_tool.search_enabled,
                "orchestrator_available": self.orchestrator is not None
            }
        except Exception as e:
            return {
                "error": str(e),
                "orchestrator_available": self.orchestrator is not None
            }
    
    def stream_query(self, user_query: str, user_id: str = None,
                    chat_history: List[Dict] = None):
        """Stream query processing (placeholder for future implementation)"""
        # For now, return the same as process_query
        # In the future, this could be implemented with streaming
        return self.process_query(user_query, user_id, chat_history)

# Create a global instance
chatbot_integration = ChatbotIntegrationService()

def get_chatbot_integration():
    """Get the global chatbot integration instance"""
    return chatbot_integration 