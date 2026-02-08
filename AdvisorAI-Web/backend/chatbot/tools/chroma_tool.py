"""ChromaDB vector-search tool – routes queries to the right collections."""

import hashlib
import logging
import os
from typing import Dict, Any, List

import chromadb
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config.settings import settings
from core.llm_router import LLMRouter
from core.utils import parse_llm_json_array, sanitize_query

logger = logging.getLogger("chatbot")


class ChromaTool:
    """Search across ChromaDB vector collections using LLM-based routing."""

    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.llm_router = LLMRouter()
        self.collections = self._load_collections()
        logger.info(
            "ChromaTool initialised with %d collections: %s",
            len(self.collections),
            list(self.collections.keys()),
        )

    # ------------------------------------------------------------------
    # Collection loading
    # ------------------------------------------------------------------

    def _load_collections(self) -> Dict[str, Chroma]:
        """Discover and load all Chroma collections from VECTORDB_DIR."""
        collections: Dict[str, Chroma] = {}

        if not os.path.exists(settings.VECTORDB_DIR):
            logger.warning("VectorDB dir does not exist: %s", settings.VECTORDB_DIR)
            return collections

        for folder in os.listdir(settings.VECTORDB_DIR):
            full_path = os.path.join(settings.VECTORDB_DIR, folder)
            if not os.path.isdir(full_path):
                continue

            wrapper = self._try_load_collection(folder, full_path)
            if wrapper is not None:
                collections[folder] = wrapper

        return collections

    def _try_load_collection(self, name: str, path: str):
        """Attempt to load a single Chroma collection; returns wrapper or None."""
        # Primary approach – PersistentClient
        try:
            client = chromadb.PersistentClient(path=path)
            collection = client.get_collection(name=name)
            count = collection.count()
            if count == 0:
                logger.debug("Collection %s is empty, skipping", name)
                return None

            wrapper = Chroma(
                client=client,
                collection_name=name,
                embedding_function=self.embedding_model,
            )
            logger.info("Loaded collection %s (%d docs)", name, count)
            return wrapper

        except Exception as primary_err:
            logger.debug("Primary load failed for %s: %s", name, primary_err)

        # Fallback – simple Chroma constructor
        try:
            wrapper = Chroma(
                collection_name=name,
                persist_directory=path,
                embedding_function=self.embedding_model,
            )
            logger.info("Loaded collection %s via fallback", name)
            return wrapper
        except Exception as fallback_err:
            logger.error("Failed to load collection %s: %s", name, fallback_err)
            return None

    # ------------------------------------------------------------------
    # LLM-based collection routing
    # ------------------------------------------------------------------

    async def _select_collections(self, query: str) -> List[str]:
        """Ask the LLM which collections are relevant for *query*."""
        available = list(self.collections.keys())
        if not available:
            return []

        safe_query = sanitize_query(query)
        prompt = (
            "You are a smart router in a RAG system for Stevens Institute of Technology.\n\n"
            f"Available collections: {available}\n\n"
            f'User question: "{safe_query}"\n\n'
            "Return ONLY a valid JSON array of relevant collection names. No explanation.\n\n"
            "Examples:\n"
            '- Course questions → ["AllCourseRelatedData"]\n'
            '- Faculty questions → ["AllFacultyGeneralInformation", "AllFacultyResearchInformation"]\n'
            "- If unsure → return all collections"
        )

        try:
            llm = self.llm_router.get_llm()
            response = await llm.ainvoke([{"role": "user", "content": prompt}])

            selected = parse_llm_json_array(response.content) or []
            valid = [c for c in selected if c in available]

            if not valid:
                logger.debug("No valid collections selected, using all")
                return available

            logger.debug("Router selected collections: %s", valid)
            return valid

        except Exception as e:
            logger.warning("Collection routing error, using all: %s", e)
            return available

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def _retrieve_documents(
        self, query: str, collection_names: List[str]
    ) -> List[Document]:
        """Retrieve, de-duplicate, and rank documents from the given collections."""
        if not collection_names:
            return []

        all_docs: List[Document] = []

        for name in collection_names:
            store = self.collections.get(name)
            if store is None:
                continue
            try:
                docs_with_scores = store.similarity_search_with_score(
                    query, k=settings.TOP_K_PER_COLLECTION
                )
                for doc, score in docs_with_scores:
                    doc.metadata["collection"] = name
                    doc.metadata["source"] = "vector_db"
                    doc.metadata["similarity_score"] = score
                all_docs.extend(doc for doc, _ in docs_with_scores)
                logger.debug("Retrieved %d docs from %s", len(docs_with_scores), name)
            except Exception as e:
                logger.error("Retrieval error in %s: %s", name, e)

        # Sort by similarity (lower = better for cosine distance)
        all_docs.sort(key=lambda d: d.metadata.get("similarity_score", 1e6))

        # De-duplicate by content hash
        seen = set()
        unique: List[Document] = []
        for doc in all_docs:
            h = hashlib.md5(doc.page_content.encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(doc)

        return unique[: settings.MAX_TOTAL_DOCS]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_collections(self, query: str) -> Dict[str, Any]:
        """High-level search: route → retrieve → serialise."""
        try:
            if not self.collections:
                return {
                    "documents": [],
                    "collections_used": [],
                    "success": False,
                    "error": "No collections available",
                }

            selected = await self._select_collections(query)
            docs = await self._retrieve_documents(query, selected)

            logger.info(
                "Chroma search: %d docs from %s", len(docs), selected
            )

            return {
                "documents": [
                    {
                        "content": d.page_content,
                        "metadata": d.metadata,
                        "collection": d.metadata.get("collection", "unknown"),
                    }
                    for d in docs
                ],
                "collections_used": selected,
                "success": True,
            }

        except Exception as e:
            logger.error("ChromaTool search error: %s", e, exc_info=True)
            return {
                "documents": [],
                "collections_used": [],
                "success": False,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # Utility accessors
    # ------------------------------------------------------------------

    def get_collection(self, name: str):
        return self.collections.get(name)

    def get_collection_names(self) -> List[str]:
        return list(self.collections.keys())

    def get_collection_stats(self) -> Dict[str, Any]:
        stats = {}
        for name, col in self.collections.items():
            try:
                stats[name] = {"document_count": col._collection.count()}
            except Exception as e:
                stats[name] = {"error": str(e)}
        return stats
