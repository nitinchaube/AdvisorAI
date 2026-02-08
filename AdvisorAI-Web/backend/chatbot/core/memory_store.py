from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

class MemoryStore(ABC):
    """Abstract base class for memory storage"""
    
    @abstractmethod
    async def save_conversation(self, user_id: str, query: str, response: str, metadata: Dict = None):
        """Save a conversation turn"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a user"""
        pass
    
    @abstractmethod
    async def clear_history(self, user_id: str):
        """Clear conversation history for a user"""
        pass

class InMemoryStore(MemoryStore):
    """In-memory implementation of memory store"""
    
    def __init__(self):
        self._conversations: Dict[str, List[Dict]] = {}
    
    async def save_conversation(self, user_id: str, query: str, response: str, metadata: Dict = None):
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata or {}
        }
        
        self._conversations[user_id].append(conversation)
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        if user_id not in self._conversations:
            return []
        
        return self._conversations[user_id][-limit:]
    
    async def clear_history(self, user_id: str):
        if user_id in self._conversations:
            del self._conversations[user_id]

def get_memory_store() -> MemoryStore:
    """Factory function to get the appropriate memory store"""
    return InMemoryStore() 