"""
Integration service – bridges the LangGraph chatbot with the Flask backend.

Concurrency-safe: uses threading.local() for per-thread event loops so
multiple gunicorn threads (or uvicorn threadpool tasks) can run LLM
queries simultaneously without event-loop collisions.

Also exposes native async methods for FastAPI endpoints.
"""

import sys
import os
import asyncio
import logging
import time
import threading
from typing import Dict, Any, List, AsyncGenerator

# Ensure the chatbot package is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "chatbot"))

from chatbot.core.langgraph_graph import LangGraphOrchestrator

logger = logging.getLogger("chatbot")


class ChatbotIntegrationService:
    """Wraps the LangGraph orchestrator for the Flask/FastAPI app.

    Thread-safe: each thread gets its own asyncio event loop via
    ``threading.local()``, so concurrent requests never collide.
    """

    def __init__(self):
        self.orchestrator: LangGraphOrchestrator = None  # type: ignore
        self._local = threading.local()  # Per-thread event loop storage
        self._initialize_orchestrator()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialize_orchestrator(self):
        try:
            self.orchestrator = LangGraphOrchestrator()
            logger.info("LangGraph orchestrator initialised successfully")
        except Exception as e:
            logger.error("Orchestrator init failed: %s", e, exc_info=True)
            self.orchestrator = None

    def _get_event_loop(self):
        """Return a per-thread event loop (thread-safe for gunicorn threads)."""
        loop = getattr(self._local, "event_loop", None)
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._local.event_loop = loop
        return loop

    # ------------------------------------------------------------------
    # Sync query processing (Flask routes)
    # ------------------------------------------------------------------

    def process_query(
        self,
        user_query: str,
        user_id: str = None,
        chat_history: List[Dict] = None,
    ) -> Dict:
        """Process a user query synchronously (called from Flask routes)."""
        start = time.time()

        if not self.orchestrator:
            return self._error_response(
                "The chatbot system is currently unavailable. Please try again later.",
                start,
            )

        try:
            formatted_history = self._format_chat_history(chat_history or [])

            loop = self._get_event_loop()
            result = loop.run_until_complete(
                self.orchestrator.process_query(
                    query=user_query,
                    user_id=user_id or "default",
                    chat_history=formatted_history,
                )
            )

            if not result.get("success"):
                logger.warning("Chatbot returned failure: %s", result.get("error"))
                return self._error_response(
                    "I'm having trouble processing your request. Please try again.",
                    start,
                )

            return self._build_sync_response(result, user_id, formatted_history, start)

        except Exception as e:
            logger.error("Integration error: %s", e, exc_info=True)
            return self._error_response(
                "I'm experiencing technical difficulties. Please try again.",
                start,
            )

    def stream_query(
        self,
        user_query: str,
        user_id: str = None,
        chat_history: List[Dict] = None,
    ):
        """Sync generator that yields SSE-style dicts (for Flask routes).

        Uses per-thread event loop to drive the async generator.
        """
        start = time.time()

        if not self.orchestrator:
            yield {
                "type": "token",
                "content": "The chatbot system is currently unavailable. Please try again later.",
            }
            yield {
                "type": "done",
                "chat_name": "Error",
                "sources": {},
                "processing_time": 0,
                "error": True,
            }
            return

        formatted_history = self._format_chat_history(chat_history or [])
        loop = self._get_event_loop()

        async_gen = self.orchestrator.stream_process_query(
            query=user_query,
            user_id=user_id or "default",
            chat_history=formatted_history,
        )

        result = None

        while True:
            try:
                event = loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break

            etype = event.get("type")
            if etype == "status":
                yield {
                    "type": "status",
                    "content": event.get("content", ""),
                    "node": event.get("node"),
                    "urls": event.get("urls"),
                    "sources": event.get("sources"),
                }
            elif etype == "token":
                yield {"type": "token", "content": event.get("content", "")}
            elif etype == "result":
                result = event

        # -- Fallback if no result -----------------------------------------
        if result is None or not result.get("success"):
            err_msg = (
                result.get("answer", "")
                if result
                else "I'm having trouble processing your request. Please try again."
            )
            yield {"type": "token", "content": err_msg}
            yield {
                "type": "done",
                "chat_name": "Error",
                "sources": {},
                "processing_time": time.time() - start,
                "error": True,
            }
            return

        yield self._build_done_event(result, user_id, formatted_history, start)

    # ------------------------------------------------------------------
    # Native async methods (FastAPI routes – no event-loop bridge)
    # ------------------------------------------------------------------

    async def async_process_query(
        self,
        user_query: str,
        user_id: str = None,
        chat_history: List[Dict] = None,
    ) -> Dict:
        """Process a user query natively async (called from FastAPI routes)."""
        start = time.time()

        if not self.orchestrator:
            return self._error_response(
                "The chatbot system is currently unavailable. Please try again later.",
                start,
            )

        try:
            formatted_history = self._format_chat_history(chat_history or [])

            result = await self.orchestrator.process_query(
                query=user_query,
                user_id=user_id or "default",
                chat_history=formatted_history,
            )

            if not result.get("success"):
                logger.warning("Chatbot returned failure: %s", result.get("error"))
                return self._error_response(
                    "I'm having trouble processing your request. Please try again.",
                    start,
                )

            return self._build_sync_response(result, user_id, formatted_history, start)

        except Exception as e:
            logger.error("Async integration error: %s", e, exc_info=True)
            return self._error_response(
                "I'm experiencing technical difficulties. Please try again.",
                start,
            )

    async def async_stream_query(
        self,
        user_query: str,
        user_id: str = None,
        chat_history: List[Dict] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Native async generator for FastAPI SSE streaming.

        No sync-to-async bridge — runs directly on the event loop.
        """
        start = time.time()

        if not self.orchestrator:
            yield {
                "type": "token",
                "content": "The chatbot system is currently unavailable. Please try again later.",
            }
            yield {
                "type": "done",
                "chat_name": "Error",
                "sources": {},
                "processing_time": 0,
                "error": True,
            }
            return

        formatted_history = self._format_chat_history(chat_history or [])

        result = None

        try:
            async for event in self.orchestrator.stream_process_query(
                query=user_query,
                user_id=user_id or "default",
                chat_history=formatted_history,
            ):
                etype = event.get("type")
                if etype == "status":
                    yield {
                        "type": "status",
                        "content": event.get("content", ""),
                        "node": event.get("node"),
                        "urls": event.get("urls"),
                        "sources": event.get("sources"),
                    }
                elif etype == "token":
                    yield {"type": "token", "content": event.get("content", "")}
                elif etype == "result":
                    result = event
        except Exception as exc:
            logger.error("Async stream error: %s", exc, exc_info=True)
            yield {
                "type": "token",
                "content": "I'm sorry, I ran into an issue. Please try again.",
            }
            yield {
                "type": "done",
                "chat_name": "Error",
                "sources": {},
                "processing_time": time.time() - start,
                "error": True,
            }
            return

        # -- Fallback if no result -----------------------------------------
        if result is None or not result.get("success"):
            err_msg = (
                result.get("answer", "")
                if result
                else "I'm having trouble processing your request. Please try again."
            )
            yield {"type": "token", "content": err_msg}
            yield {
                "type": "done",
                "chat_name": "Error",
                "sources": {},
                "processing_time": time.time() - start,
                "error": True,
            }
            return

        yield self._build_done_event(result, user_id, formatted_history, start)

    # ------------------------------------------------------------------
    # Chat history formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_chat_history(chat_history: List[Dict]) -> str:
        """Convert frontend chat messages into ``Q: … / A: …`` text."""
        if not chat_history:
            return ""

        parts: List[str] = []
        current_query = None

        for entry in chat_history[-10:]:
            if not isinstance(entry, dict):
                continue

            role = entry.get("role", "") or entry.get("type", "")
            content = (entry.get("content", "") or "").strip()

            # Legacy format: {query, response}
            if "query" in entry and "response" in entry:
                q = entry["query"].strip()
                a = entry["response"].strip()
                if q and a:
                    parts.append(f"Q: {q}")
                    parts.append(f"A: {a}")
                continue

            if not (role and content):
                continue

            if role in ("user",):
                if current_query:
                    parts.append(f"Q: {current_query}")
                current_query = content
            elif role in ("assistant", "ai") and current_query:
                parts.append(f"Q: {current_query}")
                parts.append(f"A: {content}")
                current_query = None
            elif role in ("assistant", "ai"):
                parts.append(f"A: {content}")

        if current_query:
            parts.append(f"Q: {current_query}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # System info
    # ------------------------------------------------------------------

    def get_system_stats(self) -> Dict:
        """Return basic health / stats about the chatbot subsystem."""
        if not self.orchestrator:
            return {"orchestrator_available": False}

        try:
            stats = self.orchestrator.chroma_agent.chroma_tool.get_collection_stats()
            return {
                "collections": stats,
                "collection_names": list(stats.keys()),
                "total_collections": len(stats),
                "orchestrator_available": True,
            }
        except Exception as e:
            return {"error": str(e), "orchestrator_available": True}

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_sync_response(
        result: Dict, user_id: str, formatted_history: str, start: float
    ) -> Dict:
        metadata = result.get("metadata", {})
        reflection = metadata.get("reflection", {})
        reasoning = metadata.get("reasoning_result", {}) or {}
        web_meta = metadata.get("web_search", {}) or {}
        reasoning["web_search"] = web_meta

        return {
            "response": result["answer"],
            "sources": {
                "collections_used": metadata.get("tools_used", []),
                "documents_retrieved": 0,
                "web_search_performed": metadata.get("web_search_performed", False),
                "user_info_included": bool(user_id),
                "chat_history_included": bool(formatted_history),
                "general_tool_used": metadata.get("used_general_tool", False),
                "reasoning": reasoning,
                "reflection": {
                    "score": reflection.get("score"),
                    "was_refined": not reflection.get("is_acceptable", True),
                },
                "top_documents": [],
            },
            "processing_time": time.time() - start,
            "error": False,
            "chat_name": metadata.get("chat_name", "New Chat"),
        }

    @staticmethod
    def _build_done_event(
        result: Dict, user_id: str, formatted_history: str, start: float
    ) -> Dict:
        metadata = result.get("metadata", {})
        reflection = metadata.get("reflection", {})
        reasoning = metadata.get("reasoning_result", {}) or {}
        web_meta = metadata.get("web_search", {}) or {}
        reasoning["web_search"] = web_meta

        return {
            "type": "done",
            "chat_name": metadata.get("chat_name", "New Chat"),
            "sources": {
                "collections_used": metadata.get("tools_used", []),
                "documents_retrieved": 0,
                "web_search_performed": metadata.get("web_search_performed", False),
                "user_info_included": bool(user_id),
                "chat_history_included": bool(formatted_history),
                "general_tool_used": metadata.get("used_general_tool", False),
                "reasoning": reasoning,
                "reflection": {
                    "score": reflection.get("score"),
                    "was_refined": not reflection.get("is_acceptable", True),
                },
                "top_documents": [],
            },
            "processing_time": time.time() - start,
            "error": False,
        }

    @staticmethod
    def _error_response(message: str, start_time: float) -> Dict:
        return {
            "response": message,
            "sources": {},
            "processing_time": time.time() - start_time,
            "error": True,
        }


# ── Module-level singleton ────────────────────────────────────────────────

chatbot_integration = ChatbotIntegrationService()


def get_chatbot_integration():
    """Return the global ChatbotIntegrationService instance."""
    return chatbot_integration
