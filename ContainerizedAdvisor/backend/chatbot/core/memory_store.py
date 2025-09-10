from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio
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

class RedisMemoryStore(MemoryStore):
    """Redis implementation of memory store"""
    
    def __init__(self, redis_url: str):
        import redis
        self.redis_client = redis.from_url(redis_url)
    
    async def save_conversation(self, user_id: str, query: str, response: str, metadata: Dict = None):
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata or {}
        }
        
        key = f"conversation:{user_id}"
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.redis_client.lpush(key, json.dumps(conversation))
        )
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.redis_client.ltrim(key, 0, 99)  # Keep last 100 conversations
        )
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        key = f"conversation:{user_id}"
        conversations = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.redis_client.lrange(key, 0, limit - 1)
        )
        
        return [json.loads(conv) for conv in conversations]
    
    async def clear_history(self, user_id: str):
        key = f"conversation:{user_id}"
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.redis_client.delete(key)
        )

def get_memory_store() -> MemoryStore:
    """Factory function to get the appropriate memory store"""
    from config.settings import settings
    
    if settings.MEMORY_TYPE == "redis":
        return RedisMemoryStore(settings.REDIS_URL)
    else:
        return InMemoryStore() 