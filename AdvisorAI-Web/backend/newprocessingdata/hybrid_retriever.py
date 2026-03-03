"""
Hybrid Retriever — entity-aware routing + metadata filters + semantic fallback.

This module replaces the LLM-based collection router with a deterministic,
sub-millisecond entity detection layer that:

  1. Extracts course codes (FE 621, CS559, etc.) via regex
  2. Detects professor names via a prebuilt lookup of all known faculty
  3. Classifies query intent (professor_lookup, course_lookup, research, contact, general)
  4. Routes to the right ChromaDB collection with targeted metadata filters
  5. Falls back to multi-collection semantic search when no entities are detected

Usage:
    retriever = HybridRetriever()
    results = await retriever.search("Who teaches FE 621?")
"""

import json
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any

import chromadb
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger("chatbot")

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

VALID_COURSE_PREFIXES = {
    "AAI", "ACC", "BIA", "BIO", "BIOE", "BME", "BT", "CAL", "CE", "CH",
    "CHE", "CLK", "CM", "COMM", "COOP", "CPE", "CS", "DE", "DS", "ECON",
    "EE", "ELC", "EM", "EMT", "EN", "ENGR", "ES", "FA", "FE", "FIN",
    "GEN", "HAR", "HASS", "HHS", "HLI", "HMU", "HONR", "HPL", "HQSS",
    "HSSC", "HST", "HTH", "HUM", "IDE", "IPD", "ISE", "LCH", "LFR",
    "LSP", "LTL", "MA", "ME", "MGT", "MIS", "MT", "NANO", "NE", "OE",
    "PAE", "PEP", "PIN", "PME", "PRV", "QF", "SEF", "SES", "SM", "SOC",
    "SSES", "SSW", "SYS", "TE", "TG", "TM",
}

COURSE_CODE_RE = re.compile(
    r'\b(' + '|'.join(sorted(VALID_COURSE_PREFIXES, key=len, reverse=True)) +
    r')[\s\-]?(\d{3})\b',
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════
# Entity Detector
# ═══════════════════════════════════════════════════════════════════════

class EntityDetector:
    """Extract structured entities and classify intent from a user query."""

    _PROFESSOR_PREFIXES = re.compile(
        r'\b(?:professor|prof\.?|dr\.?|instructor|faculty)\s+',
        re.IGNORECASE,
    )

    _INTENT_PATTERNS: list[tuple[str, list[str]]] = [
        ("professor_lookup", [
            "who teaches", "who is teaching", "taught by", "instructor for",
            "professor for", "teacher of", "who is the professor",
            "which professor", "who's teaching",
        ]),
        ("course_lookup", [
            "what courses", "which courses", "courses taught",
            "courses does", "classes does", "what does .* teach",
            "teach what", "teaching what",
        ]),
        ("research_lookup", [
            "research", "publications", "studies", "working on",
            "research interest", "research area", "published",
            "grants", "funding",
        ]),
        ("contact_lookup", [
            "contact", "email", "phone", "office", "reach",
            "how to contact", "how can i reach", "office hours",
            "office location", "where is .* office",
        ]),
        ("course_info", [
            "prerequisite", "prereq", "credits", "description",
            "what is .* about", "tell me about .* course",
            "course details", "syllabus", "offered",
        ]),
    ]

    _LEVEL_PATTERNS: list[tuple[str, re.Pattern]] = [
        ("undergraduate", re.compile(
            r'\b(?:undergraduate|undergrad|bachelor|bachelors|bachelor\'s|'
            r'ug|lower[\s-]?level|100[\s-]?level|200[\s-]?level|300[\s-]?level|400[\s-]?level)\b',
            re.IGNORECASE,
        )),
        ("graduate", re.compile(
            r'\b(?:graduate|grad|master|masters|master\'s|phd|doctoral|'
            r'ms|m\.s\.|advanced|upper[\s-]?level|500[\s-]?level|600[\s-]?level|700[\s-]?level)\b',
            re.IGNORECASE,
        )),
    ]

    def __init__(self, faculty_names: list[str]):
        self._faculty_last_names: dict[str, list[str]] = {}
        self._faculty_full_lower: dict[str, str] = {}

        for name in faculty_names:
            full_lower = name.lower()
            self._faculty_full_lower[full_lower] = name

            parts = name.split()
            if parts:
                last = parts[-1].lower()
                self._faculty_last_names.setdefault(last, []).append(name)

    def detect(self, query: str) -> dict[str, Any]:
        """Return {course_codes, professor_names, course_level, intent, raw_query}."""
        result: dict[str, Any] = {
            "course_codes": [],
            "professor_names": [],
            "course_level": None,
            "intent": "general",
            "raw_query": query,
        }

        q_lower = query.lower().strip()

        # ── Course codes ──────────────────────────────────────────────
        for match in COURSE_CODE_RE.finditer(query):
            prefix, number = match.group(1).upper(), match.group(2)
            code = f"{prefix} {number}"
            if code not in result["course_codes"]:
                result["course_codes"].append(code)

        # ── Course level (undergrad / graduate) ───────────────────────
        for level, pattern in self._LEVEL_PATTERNS:
            if pattern.search(q_lower):
                result["course_level"] = level
                break

        # ── Professor names ───────────────────────────────────────────
        # Strategy 1: "Professor X" / "Dr. X" patterns
        for m in self._PROFESSOR_PREFIXES.finditer(query):
            after = query[m.end():].strip()
            candidate = self._match_faculty_name(after)
            if candidate and candidate not in result["professor_names"]:
                result["professor_names"].append(candidate)

        # Strategy 2: scan for known last names in query
        if not result["professor_names"]:
            for last_lower, full_names in self._faculty_last_names.items():
                if len(last_lower) < 3:
                    continue
                pattern = r'\b' + re.escape(last_lower) + r'\b'
                if re.search(pattern, q_lower):
                    for fn in full_names:
                        if fn not in result["professor_names"]:
                            result["professor_names"].append(fn)

        # Strategy 3: scan for full names (first + last)
        if not result["professor_names"]:
            for full_lower, original in self._faculty_full_lower.items():
                if full_lower in q_lower:
                    if original not in result["professor_names"]:
                        result["professor_names"].append(original)

        # ── Intent classification ─────────────────────────────────────
        result["intent"] = self._classify_intent(
            q_lower, result["course_codes"], result["professor_names"]
        )

        return result

    def _match_faculty_name(self, text: str) -> str | None:
        """Try to match faculty from text immediately after a prefix like 'Professor'."""
        words = text.split()
        if not words:
            return None

        # Try 2-word match first (e.g., "Dragos Bozdog")
        if len(words) >= 2:
            two_word = f"{words[0]} {words[1]}".lower()
            if two_word in self._faculty_full_lower:
                return self._faculty_full_lower[two_word]

        # Try last-name match
        first_word = words[0].lower().rstrip(".,;:!?'\"")
        if first_word in self._faculty_last_names:
            matches = self._faculty_last_names[first_word]
            return matches[0] if len(matches) == 1 else matches[0]

        return None

    def _classify_intent(
        self,
        q_lower: str,
        course_codes: list[str],
        professor_names: list[str],
    ) -> str:
        """Classify user intent from query text + detected entities."""
        for intent, patterns in self._INTENT_PATTERNS:
            for pat in patterns:
                if re.search(pat, q_lower):
                    return intent

        if course_codes and professor_names:
            return "professor_lookup"
        if course_codes and not professor_names:
            if any(w in q_lower for w in ["who", "professor", "teach", "instructor"]):
                return "professor_lookup"
            return "course_info"
        if professor_names and not course_codes:
            if any(w in q_lower for w in ["course", "class", "teach"]):
                return "course_lookup"
            return "professor_lookup"

        return "general"


# ═══════════════════════════════════════════════════════════════════════
# Hybrid Retriever
# ═══════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """
    Entity-aware retrieval across multiple ChromaDB collections.

    Routing logic (no LLM call needed):
      - professor_lookup + course_code → FacultyCourseMapping (filter by course_code)
      - course_lookup + professor_name → FacultyCourseMapping (filter by professor_name_lower)
      - course_info + course_code → AllCourseData (filter by course_code)
      - research_lookup + professor → AllFacultyResearch (filter by professor_name_lower)
      - contact_lookup + professor → AllFacultyProfiles (filter by professor_name_lower)
      - general → semantic search across all collections
    """

    COLLECTION_NAMES = [
        "AllFacultyProfiles",
        "FacultyCourseMapping",
        "AllCourseData",
        "AllFacultyResearch",
    ]

    def __init__(
        self,
        vectordb_dir: str | None = None,
        embedding_model: str | None = None,
        top_k: int = 5,
    ):
        if vectordb_dir is None:
            vectordb_dir = os.getenv("VECTORDB_DIR", "./VectorDB_v2")
        if embedding_model is None:
            embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

        # Resolve relative paths against the backend directory, not CWD
        vdb_path = Path(vectordb_dir)
        if not vdb_path.is_absolute():
            vdb_path = (BACKEND_DIR / vdb_path).resolve()
        self.vectordb_dir = vdb_path
        self.top_k = top_k

        self.embedding = HuggingFaceEmbeddings(model_name=embedding_model)
        self.collections: dict[str, Chroma] = {}
        self._load_collections()

        faculty_names = self._extract_faculty_names()
        self.entity_detector = EntityDetector(faculty_names)

        logger.info(
            "HybridRetriever ready: %d collections, %d faculty names, "
            "model=%s, vectordb=%s",
            len(self.collections), len(faculty_names),
            embedding_model, self.vectordb_dir,
        )

    def _load_collections(self):
        vdb = self.vectordb_dir

        if not vdb.exists():
            # Try CWD-relative as last resort
            cwd_candidate = Path.cwd() / vdb.name
            if cwd_candidate.exists():
                logger.warning(
                    "Primary vectordb_dir %s not found; using fallback %s",
                    vdb, cwd_candidate,
                )
                vdb = cwd_candidate.resolve()
                self.vectordb_dir = vdb

        logger.info(
            "Loading collections from %s (exists=%s, cwd=%s)",
            vdb, vdb.exists(), Path.cwd(),
        )

        for name in self.COLLECTION_NAMES:
            path = vdb / name
            if not path.exists():
                logger.error(
                    "Collection dir NOT FOUND: %s", path,
                )
                continue
            try:
                client = chromadb.PersistentClient(path=str(path))
                store = Chroma(
                    client=client,
                    collection_name=name,
                    embedding_function=self.embedding,
                )
                count = store._collection.count()
                self.collections[name] = store
                logger.info("Loaded collection: %s (%d docs)", name, count)
            except Exception as e:
                logger.error("Failed to load %s: %s", name, e, exc_info=True)

    def _extract_faculty_names(self) -> list[str]:
        """Get all professor names from the FacultyCourseMapping collection metadata."""
        profiles_path = SCRIPT_DIR / "structured_faculty_profiles.json"
        if profiles_path.exists():
            with open(profiles_path) as f:
                profiles = json.load(f)
            return list({p["name"] for p in profiles})

        store = self.collections.get("AllFacultyProfiles")
        if not store:
            return []
        try:
            raw = store._collection.get(include=["metadatas"])
            names = {m.get("professor_name", "") for m in raw["metadatas"] if m.get("professor_name")}
            return list(names)
        except Exception as e:
            logger.error("Could not extract faculty names: %s", e)
            return []

    # ── Core retrieval strategies ─────────────────────────────────────

    def _filtered_search(
        self,
        collection_name: str,
        query: str,
        where_filter: dict,
        k: int | None = None,
    ) -> list[Document]:
        """Semantic search within a single collection, narrowed by metadata filter."""
        store = self.collections.get(collection_name)
        if not store:
            logger.warning("_filtered_search: collection '%s' not loaded", collection_name)
            return []
        try:
            results = store.similarity_search_with_score(
                query, k=k or self.top_k, filter=where_filter
            )
            docs = []
            for doc, score in results:
                doc.metadata["similarity_score"] = score
                doc.metadata["collection"] = collection_name
                doc.metadata["source"] = "vector_db"
                doc.metadata["retrieval_strategy"] = "filtered"
                docs.append(doc)
            return docs
        except Exception as e:
            logger.error(
                "Filtered search error in %s (filter=%s): %s",
                collection_name, where_filter, e, exc_info=True,
            )
            return []

    def _semantic_search(
        self,
        collection_name: str,
        query: str,
        k: int | None = None,
    ) -> list[Document]:
        """Pure semantic search, no metadata filter."""
        store = self.collections.get(collection_name)
        if not store:
            logger.warning("_semantic_search: collection '%s' not loaded", collection_name)
            return []
        try:
            results = store.similarity_search_with_score(
                query, k=k or self.top_k
            )
            docs = []
            for doc, score in results:
                doc.metadata["similarity_score"] = score
                doc.metadata["collection"] = collection_name
                doc.metadata["source"] = "vector_db"
                doc.metadata["retrieval_strategy"] = "semantic"
                docs.append(doc)
            return docs
        except Exception as e:
            logger.error(
                "Semantic search error in %s: %s",
                collection_name, e, exc_info=True,
            )
            return []

    def _deduplicate(self, docs: list[Document], limit: int) -> list[Document]:
        """Deduplicate by content hash and return top-N by score."""
        docs.sort(key=lambda d: d.metadata.get("similarity_score", 1e6))
        seen: set[str] = set()
        unique: list[Document] = []
        for doc in docs:
            h = hashlib.md5(doc.page_content.encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(doc)
        return unique[:limit]

    # ── Routing logic ─────────────────────────────────────────────────

    @staticmethod
    def _combine_filters(base_filter: dict, level: str | None) -> dict:
        """Merge a metadata filter with an optional course_level constraint."""
        if not level:
            return base_filter
        level_filter = {"course_level": level}
        if not base_filter:
            return level_filter
        return {"$and": [base_filter, level_filter]}

    async def search(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        """
        High-level search: detect entities → route → retrieve → serialize.

        Returns the same format as the old ChromaTool.search_collections()
        for drop-in compatibility.
        """
        k = top_k or self.top_k

        try:
            entities = self.entity_detector.detect(query)
            intent = entities["intent"]
            codes = entities["course_codes"]
            profs = entities["professor_names"]
            level = entities.get("course_level")

            logger.info(
                "HybridRetriever: intent=%s codes=%s profs=%s level=%s query='%s'",
                intent, codes, profs, level, query[:80],
            )

            docs = self._route_and_retrieve(query, intent, codes, profs, k, level)
            docs = self._deduplicate(docs, k)

            collections_used = list({d.metadata.get("collection", "") for d in docs})

            logger.info(
                "HybridRetriever: %d docs from %s (intent=%s)",
                len(docs), collections_used, intent,
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
                "collections_used": collections_used,
                "entities_detected": entities,
                "success": True,
            }

        except Exception as e:
            logger.error("HybridRetriever error: %s", e, exc_info=True)
            return {
                "documents": [],
                "collections_used": [],
                "entities_detected": {},
                "success": False,
                "error": str(e),
            }

    def _route_and_retrieve(
        self,
        query: str,
        intent: str,
        codes: list[str],
        profs: list[str],
        k: int,
        level: str | None = None,
    ) -> list[Document]:
        """Deterministic routing based on intent + detected entities.

        The `level` parameter ("undergraduate" / "graduate") is applied as
        a metadata filter on collections that carry course_level metadata
        (FacultyCourseMapping, AllCourseData). Profile and research
        collections are not level-filtered since faculty exist at both levels.
        """

        _cf = self._combine_filters
        all_docs: list[Document] = []

        # ── STRATEGY 1: professor_lookup with course code ─────────────
        if intent == "professor_lookup" and codes:
            for code in codes:
                all_docs.extend(self._filtered_search(
                    "FacultyCourseMapping", query,
                    _cf({"course_code": code}, level), k=k,
                ))
                all_docs.extend(self._filtered_search(
                    "AllCourseData", query,
                    _cf({"course_code": code}, level), k=2,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 2: course_lookup with professor name ─────────────
        if intent == "course_lookup" and profs:
            for prof in profs:
                all_docs.extend(self._filtered_search(
                    "FacultyCourseMapping", query,
                    _cf({"professor_name_lower": prof.lower()}, level), k=k,
                ))
                all_docs.extend(self._filtered_search(
                    "AllFacultyProfiles", query,
                    {"professor_name_lower": prof.lower()}, k=2,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 3: course_info with course code ──────────────────
        if intent == "course_info" and codes:
            for code in codes:
                all_docs.extend(self._filtered_search(
                    "AllCourseData", query,
                    _cf({"course_code": code}, level), k=k,
                ))
                all_docs.extend(self._filtered_search(
                    "FacultyCourseMapping", query,
                    _cf({"course_code": code}, level), k=3,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 4: research_lookup with professor name ───────────
        if intent == "research_lookup" and profs:
            for prof in profs:
                all_docs.extend(self._filtered_search(
                    "AllFacultyResearch", query,
                    {"professor_name_lower": prof.lower()}, k=k,
                ))
                all_docs.extend(self._filtered_search(
                    "AllFacultyProfiles", query,
                    {"professor_name_lower": prof.lower()}, k=2,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 5: contact_lookup with professor name ────────────
        if intent == "contact_lookup" and profs:
            for prof in profs:
                all_docs.extend(self._filtered_search(
                    "AllFacultyProfiles", query,
                    {"professor_name_lower": prof.lower()}, k=k,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 6: professor name detected, generic intent ───────
        if profs and not codes:
            for prof in profs:
                all_docs.extend(self._filtered_search(
                    "AllFacultyProfiles", query,
                    {"professor_name_lower": prof.lower()}, k=3,
                ))
                all_docs.extend(self._filtered_search(
                    "FacultyCourseMapping", query,
                    _cf({"professor_name_lower": prof.lower()}, level), k=3,
                ))
                all_docs.extend(self._filtered_search(
                    "AllFacultyResearch", query,
                    {"professor_name_lower": prof.lower()}, k=2,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 7: course code detected, generic intent ──────────
        if codes and not profs:
            for code in codes:
                all_docs.extend(self._filtered_search(
                    "AllCourseData", query,
                    _cf({"course_code": code}, level), k=3,
                ))
                all_docs.extend(self._filtered_search(
                    "FacultyCourseMapping", query,
                    _cf({"course_code": code}, level), k=3,
                ))
            if all_docs:
                return all_docs

        # ── STRATEGY 8: research_lookup, no specific professor ────────
        if intent == "research_lookup":
            all_docs.extend(self._semantic_search("AllFacultyResearch", query, k=k))
            if all_docs:
                return all_docs

        # ── STRATEGY 9: level-only query (no entities) ────────────────
        if level and not codes and not profs:
            all_docs.extend(self._filtered_search(
                "AllCourseData", query,
                {"course_level": level}, k=k,
            ))
            all_docs.extend(self._filtered_search(
                "FacultyCourseMapping", query,
                {"course_level": level}, k=max(2, k // 2),
            ))
            if all_docs:
                return all_docs

        # ── FALLBACK: broad semantic search across collections ────────
        logger.info("HybridRetriever: all strategies exhausted, running semantic fallback")
        per_collection_k = max(2, k // 3)
        for coll_name in ["AllCourseData", "AllFacultyProfiles", "FacultyCourseMapping"]:
            fallback_docs = self._semantic_search(coll_name, query, k=per_collection_k)
            logger.info("  fallback %s → %d docs", coll_name, len(fallback_docs))
            all_docs.extend(fallback_docs)

        return all_docs

    # ── Utility accessors ─────────────────────────────────────────────

    def get_collection_names(self) -> list[str]:
        return list(self.collections.keys())

    def get_collection_stats(self) -> dict[str, Any]:
        stats = {}
        for name, col in self.collections.items():
            try:
                stats[name] = {"document_count": col._collection.count()}
            except Exception as e:
                stats[name] = {"error": str(e)}
        return stats
