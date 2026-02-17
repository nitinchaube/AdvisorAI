"""In-memory conversation store used for intra-session context."""

from typing import Dict, List
from datetime import datetime
from abc import ABC, abstractmethod


class MemoryStore(ABC):
    """Abstract base class for memory storage."""

    @abstractmethod
    async def save_conversation(
        self, user_id: str, query: str, response: str, metadata: Dict = None
    ):
        pass

    @abstractmethod
    async def get_conversation_history(
        self, user_id: str, limit: int = 10
    ) -> List[Dict]:
        pass

    @abstractmethod
    async def clear_history(self, user_id: str):
        pass


class InMemoryStore(MemoryStore):
    """Thread-safe in-memory implementation of memory store."""

    def __init__(self):
        self._conversations: Dict[str, List[Dict]] = {}

    async def save_conversation(
        self, user_id: str, query: str, response: str, metadata: Dict = None
    ):
        if user_id not in self._conversations:
            self._conversations[user_id] = []

        self._conversations[user_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "metadata": metadata or {},
            }
        )

    async def get_conversation_history(
        self, user_id: str, limit: int = 10
    ) -> List[Dict]:
        if user_id not in self._conversations:
            return []
        return self._conversations[user_id][-limit:]

    async def clear_history(self, user_id: str):
        self._conversations.pop(user_id, None)


def get_memory_store() -> MemoryStore:
    """Factory function – returns the configured memory store."""
    return InMemoryStore()
