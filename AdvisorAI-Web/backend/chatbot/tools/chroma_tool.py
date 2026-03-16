"""ChromaDB vector-search tool — entity-aware hybrid retrieval + query rewriting.

Replaces the old LLM-based collection router with a deterministic
HybridRetriever that uses regex entity detection, metadata filtering,
and semantic search.  Query rewriting is applied to follow-up and
ambiguous queries to produce standalone, retrieval-optimised queries.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from config.settings import settings
from core.llm_router import LLMRouter
from core.utils import sanitize_query

# backend/ must be on sys.path for the newprocessingdata import
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_DIR not in sys.path:
    sys.path.append(_BACKEND_DIR)

from newprocessingdata.hybrid_retriever import HybridRetriever

logger = logging.getLogger("chatbot")


class ChromaTool:
    """Entity-aware vector search across ChromaDB collections."""

    def __init__(self):
        self.llm_router = LLMRouter()

        # Resolve VECTORDB_DIR to an absolute path anchored to backend/
        vectordb_dir = settings.VECTORDB_DIR
        if not os.path.isabs(vectordb_dir):
            vectordb_dir = os.path.join(_BACKEND_DIR, vectordb_dir)
        vectordb_dir = os.path.realpath(vectordb_dir)

        logger.info("ChromaTool: resolved VECTORDB_DIR=%s", vectordb_dir)

        self.retriever = HybridRetriever(
            vectordb_dir=vectordb_dir,
            embedding_model=settings.EMBEDDING_MODEL,
            top_k=settings.TOP_K_PER_COLLECTION,
        )
        logger.info(
            "ChromaTool initialised with HybridRetriever "
            "(collections=%s, model=%s, top_k=%d)",
            self.retriever.get_collection_names(),
            settings.EMBEDDING_MODEL,
            settings.TOP_K_PER_COLLECTION,
        )

    # ------------------------------------------------------------------
    # Query rewriting (for follow-ups and ambiguous queries)
    # ------------------------------------------------------------------

    async def _rewrite_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Rewrite the query into a standalone, retrieval-optimised form.

        Only invoked for follow-up / context-dependent queries where the
        raw query (e.g. "what about that course?") would fail retrieval.
        Returns the original query unchanged if rewriting fails.
        """
        if not chat_history:
            return query

        history_text = "\n".join(
            f"Q: {h.get('query', '')[:200]}\nA: {h.get('response', '')[:300]}"
            for h in chat_history[-3:]
        )

        prompt = (
            "You are a query rewriter for a university knowledge base search.\n\n"
            "Given the conversation history and latest question, produce a SINGLE "
            "standalone search query that captures the user's full intent. "
            "Resolve all pronouns ('it', 'that', 'they') and implicit references.\n\n"
            f"=== Conversation History ===\n{history_text}\n\n"
            f"=== Latest Question ===\n{query}\n\n"
            "Rules:\n"
            "- Output ONLY the rewritten query, nothing else.\n"
            "- Keep course codes, professor names, and specific terms intact.\n"
            "- If the question is already standalone, return it as-is.\n"
            "- Do NOT answer the question. Only rewrite it.\n\n"
            "Rewritten query:"
        )

        try:
            llm = self.llm_router.get_llm()
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            rewritten = resp.content.strip().strip('"').strip("'")

            if rewritten and 5 < len(rewritten) < 500:
                logger.info(
                    "Query rewritten: '%s' → '%s'",
                    query[:60], rewritten[:60],
                )
                return rewritten
        except Exception as e:
            logger.warning("Query rewriting failed, using original: %s", e)

        return query

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_collections(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_follow_up: bool = False,
    ) -> Dict[str, Any]:
        """High-level search: entity detect → route → retrieve.

        Query rewriting is handled upstream by the orchestrator's
        _gather_all_node so that both chroma and web searches benefit
        from the rewritten query.  The query arriving here is already
        the effective (possibly rewritten) query.

        Return format is identical to the previous ChromaTool for
        drop-in compatibility with ChromaAgent and the generate node.
        """
        try:
            safe_query = sanitize_query(query)

            result = await self.retriever.search(
                safe_query, top_k=settings.MAX_TOTAL_DOCS
            )

            result["original_query"] = safe_query

            logger.info(
                "ChromaTool: %d docs, collections=%s, entities=%s",
                len(result.get("documents", [])),
                result.get("collections_used", []),
                {
                    k: v
                    for k, v in result.get("entities_detected", {}).items()
                    if k != "raw_query"
                },
            )

            return result

        except Exception as e:
            logger.error("ChromaTool search error: %s", e, exc_info=True)
            return {
                "documents": [],
                "collections_used": [],
                "success": False,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # Utility accessors (backward-compatible)
    # ------------------------------------------------------------------

    def get_collection_names(self) -> List[str]:
        return self.retriever.get_collection_names()

    def get_collection_stats(self) -> Dict[str, Any]:
        return self.retriever.get_collection_stats()
