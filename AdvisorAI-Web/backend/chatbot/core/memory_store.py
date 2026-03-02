"""In-memory conversation store used for intra-session context.

Thread-safe: all reads/writes are guarded by a threading.Lock so
concurrent gunicorn threads (or uvicorn threadpool tasks) cannot
corrupt the shared dictionary.

Singleton: ``get_memory_store()`` always returns the *same* instance
so conversation history persists across different code paths within
the same process.
"""

import threading
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
        self._lock = threading.Lock()

    async def save_conversation(
        self, user_id: str, query: str, response: str, metadata: Dict = None
    ):
        with self._lock:
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
        with self._lock:
            if user_id not in self._conversations:
                return []
            return list(self._conversations[user_id][-limit:])

    async def clear_history(self, user_id: str):
        with self._lock:
            self._conversations.pop(user_id, None)


# ── Singleton instance ────────────────────────────────────────────────────
_store_instance: MemoryStore = None  # type: ignore
_store_lock = threading.Lock()


def get_memory_store() -> MemoryStore:
    """Factory function – returns the singleton memory store."""
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = InMemoryStore()
    return _store_instance
