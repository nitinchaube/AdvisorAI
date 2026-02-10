"""
Integration service – bridges the LangGraph chatbot with the Flask backend.
"""

import sys
import os
import asyncio
import logging
import time
from typing import Dict, Any, List

# Ensure the chatbot package is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "chatbot"))

from chatbot.core.langgraph_graph import LangGraphOrchestrator

logger = logging.getLogger("chatbot")


class ChatbotIntegrationService:
    """Wraps the LangGraph orchestrator for the Flask app."""

    def __init__(self):
        self.orchestrator: LangGraphOrchestrator = None  # type: ignore
        self._event_loop = None
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
        """Return a reusable event loop (avoids RuntimeError from nested asyncio.run)."""
        if self._event_loop is None or self._event_loop.is_closed():
            self._event_loop = asyncio.new_event_loop()
        return self._event_loop

    # ------------------------------------------------------------------
    # Query processing
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

        except Exception as e:
            logger.error("Integration error: %s", e, exc_info=True)
            return self._error_response(
                "I'm experiencing technical difficulties. Please try again.",
                start,
            )

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

    def stream_query(self, user_query: str, user_id: str = None,
                     chat_history: List[Dict] = None):
        """Generator that yields SSE-style dicts: status → tokens → done.

        Uses the orchestrator's ``stream_process_query`` so the frontend
        receives a live status update after every pipeline node completes,
        then streams the final answer word-by-word.
        """
        start = time.time()

        if not self.orchestrator:
            yield {"type": "token", "content": "The chatbot system is currently unavailable. Please try again later."}
            yield {"type": "done", "chat_name": "Error", "sources": {}, "processing_time": 0, "error": True}
            return

        formatted_history = self._format_chat_history(chat_history or [])
        loop = self._get_event_loop()

        # -- Iterate over the async generator from sync code ---------------
        async_gen = self.orchestrator.stream_process_query(
            query=user_query,
            user_id=user_id or "default",
            chat_history=formatted_history,
        )

        result = None  # will hold the final pipeline result

        while True:
            try:
                event = loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break

            if event.get("type") == "status":
                # Forward node status to the frontend
                yield {"type": "status", "content": event["content"]}
            elif event.get("type") == "result":
                result = event

        # -- Fallback if stream produced no result -------------------------
        if result is None or not result.get("success"):
            err_msg = (
                result.get("answer", "") if result
                else "I'm having trouble processing your request. Please try again."
            )
            yield {"type": "token", "content": err_msg}
            yield {"type": "done", "chat_name": "Error", "sources": {}, "processing_time": time.time() - start, "error": True}
            return

        metadata = result.get("metadata", {})
        reflection = metadata.get("reflection", {})
        reasoning = metadata.get("reasoning_result", {}) or {}
        web_meta = metadata.get("web_search", {}) or {}
        reasoning["web_search"] = web_meta

        # -- Stream the answer word-by-word --------------------------------
        answer = result.get("answer", "")
        words = answer.split(" ")
        CHUNK = 3
        for i in range(0, len(words), CHUNK):
            chunk_words = words[i : i + CHUNK]
            token = " ".join(chunk_words)
            if i > 0:
                token = " " + token
            yield {"type": "token", "content": token}

        # -- Send metadata so the frontend can finalise --------------------
        yield {
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
