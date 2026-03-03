"""
LangGraph orchestrator – ReAct + Reflection pipeline for AdvisorAI.

Architecture
============

**Safety gate** – blocks harmful, inappropriate, or completely off-topic
queries before any tools run.

**ReAct (Reason → Act → Observe)** – the agent explicitly *thinks* about
what information it needs, *acts* by calling tools, and *observes* the
results before deciding the next step.

**Reflection** – after generating a draft answer the LLM performs a
self-critique.  If the score is below a threshold the answer is *refined*.

Graph
-----
::

    ┌────────┐
    │ router │  ← classify (general / domain / blocked) + chat name
    └───┬────┘
        │  blocked? ──► immediate polite decline → save → END
        ▼
    ┌────────┐
    │ gather │  ← always: history.  domain: + chroma.  general: + general_agent
    └───┬────┘
        ▼
    ┌──────────┐
    │ evaluate │  ← ReAct THINK: is gathered info sufficient?
    └───┬──────┘
        │  need_web? ──┐
        │              ▼
        │        ┌────────────┐
        │        │ web_search │  ← ReAct ACT: fallback scraper
        │        └─────┬──────┘
        │              │
        ▼              ▼
    ┌──────────┐
    │ generate │  ← synthesise answer from ALL context
    └───┬──────┘
        ▼
    ┌─────────┐
    │ reflect │  ← self-critique: score 1-10 + feedback
    └───┬─────┘
        │  quality_ok? ──┐
        │                ▼
        │          ┌────────┐
        │          │ refine │  ← improve answer using reflection feedback
        │          └───┬────┘
        │              │
        ▼              ▼
    ┌──────┐
    │ save │  ← persist conversation
    └──────┘
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List

from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph

from agents.chroma_agent import ChromaAgent
from agents.general_agent import GeneralAgent
from agents.history_agent import HistoryAgent
from agents.web_agent import WebAgent
from config.settings import settings
from core.llm_router import LLMRouter
from core.memory_store import get_memory_store
from core.utils import clean_response, parse_llm_json, sanitize_query

logger = logging.getLogger("chatbot")

# ═══════════════════════════════════════════════════════════════════════════
# State schema
# ═══════════════════════════════════════════════════════════════════════════


class ChatState(TypedDict, total=False):
    """Typed state flowing through the LangGraph workflow."""

    # ── Input ──
    query: str
    user_id: str
    chat_history: str

    # ── Router ──
    chat_name: str
    query_type: str  # "general" | "domain" | "blocked"
    is_follow_up: bool

    # ── Query rewriting ──
    rewritten_query: str

    # ── Tool outputs ──
    chroma_results: Dict[str, Any]
    collections_searched: List[str]
    chroma_error: str
    history_results: Dict[str, Any]
    general_answer: str
    general_error: str
    used_general_tool: bool
    web_results: Dict[str, Any]
    web_search_query: str

    # ── Evaluate (ReAct reasoning trace) ──
    react_thought: str
    need_web_search: bool

    # ── Generate ──
    draft_answer: str

    # ── Reflect ──
    reflection: Dict[str, Any]

    # ── Final ──
    answer: str
    saved: bool


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

# Short greetings / casual messages that should skip the full pipeline
_GREETING_PATTERNS = frozenset([
    "hello", "hi", "hey", "hii", "hiii", "helo",
    "good morning", "good afternoon", "good evening", "good night",
    "morning", "afternoon", "evening",
    "howdy", "yo", "sup", "whats up", "what's up",
    "how are you", "how r u", "how are u",
    "thanks", "thank you", "thank u", "thx", "ty",
    "ok", "okay", "cool", "great", "nice", "awesome",
    "bye", "goodbye", "good bye", "see you", "see ya", "later",
    "help", "help me",
])

_FOLLOW_UP_INDICATORS = frozenset([
    "try again", "check again", "again", "repeat",
    "what about", "how about", "tell me more", "more details",
    "elaborate", "expand", "continue", "go on",
    "previous question", "last question", "my previous question",
    "repeat that", "say that again", "can you repeat", "what was that",
    "remind me", "recall", "remember", "what did you say", "can you clarify",
    "previous questions", "my previous questions", "tell me about my previous",
    "what questions did i ask", "what did i ask", "show me my questions",
    "list my questions", "past questions", "conversation history", "chat history",
])

# Patterns that indicate harmful / inappropriate / off-topic queries.
# Matched case-insensitively against the query.
_BLOCKED_PATTERNS = [
    # Violence / harm
    r"\b(?:kill|murder|attack|bomb|weapon|gun|shoot|assault|terrorism|terrorist)\b",
    # Drugs / illegal
    r"\b(?:how\s+to\s+(?:make|cook|produce|manufacture)\s+(?:drug|meth|cocaine|heroin))\b",
    # Profanity / foul language
    r"\b(?:fuck|shit|bitch|asshole|bastard|damn|crap|dick|pussy|cunt|wtf|stfu)\b",
    # AdvisorAI internals / tech stack probing
    r"\b(?:what\s+(?:tech|stack|framework|database|model|llm|api|backend|frontend)\s+(?:do\s+you|are\s+you|is\s+advisorai))\b",
    r"\b(?:chromadb|chroma\s*db|langchain|langgraph|langsmith|vector\s*(?:db|database|store)|embedding\s+model)\b",
    r"\b(?:your\s+(?:source\s*code|codebase|backend|architecture|infrastructure|tech\s*stack|api\s*key))\b",
    # Hate speech
    r"\b(?:hate\s+(?:speech|group)|racist|racism|sexist|sexism|homophobic)\b",
    # Explicit / sexual
    r"\b(?:porn|pornograph|nude|naked|sexual\s+content|explicit)\b",
    # Hacking / malicious
    r"\b(?:hack(?:ing)?|exploit|malware|ransomware|ddos|phishing|crack\s+password)\b",
    # Self-harm
    r"\b(?:suicide|self[- ]?harm|cut\s+myself|end\s+my\s+life)\b",
    # Cheating
    r"\b(?:write\s+my\s+(?:essay|paper|assignment|homework)|do\s+my\s+homework)\b",
]
_COMPILED_BLOCKED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]

_DECLINE_MESSAGE = (
    "I appreciate you reaching out! However, I'm specifically designed to help "
    "with questions about Stevens Institute of Technology — things like courses, "
    "programs, admissions, faculty, campus life, and academic advising. "
    "I'm not able to help with that particular request. "
    "Feel free to ask me anything about Stevens and I'll do my best to help! 😊"
)


# ═══════════════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════════════


class LangGraphOrchestrator:
    """ReAct + Reflection orchestrator for the AdvisorAI chatbot."""

    _SIMILARITY_THRESHOLD = 1.2
    _MIN_GOOD_DOCS = 2

    def __init__(self):
        self.llm_router = LLMRouter()
        self.memory_store = get_memory_store()

        self.chroma_agent = ChromaAgent()
        self.web_agent = WebAgent()
        self.history_agent = HistoryAgent()
        self.general_agent = GeneralAgent()

        self.graph = self._build_graph()
        logger.info("LangGraph orchestrator initialised (ReAct + Reflection)")

    # ── Graph construction ────────────────────────────────────────────

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Pipeline (REFLECTION_ENABLED=true)
        ===================================
        General:  router → gather → generate → reflect → [refine] → save
        Domain:   router → gather_all → generate → reflect → [refine] → save
        Blocked:  router → save  (instant)

        Pipeline (REFLECTION_ENABLED=false)
        ====================================
        General:  router → gather → generate → save
        Domain:   router → gather_all → generate → save
        Blocked:  router → save
        """
        wf = StateGraph(ChatState)

        wf.add_node("router", self._router_node)
        wf.add_node("gather", self._gather_node)
        wf.add_node("gather_all", self._gather_all_node)
        wf.add_node("generate", self._generate_node)
        wf.add_node("save", self._save_node)

        wf.set_entry_point("router")

        wf.add_conditional_edges(
            "router",
            self._route_after_router_v2,
            {"blocked": "save", "gather": "gather", "gather_all": "gather_all"},
        )

        wf.add_edge("gather", "generate")
        wf.add_edge("gather_all", "generate")

        if settings.REFLECTION_ENABLED:
            wf.add_node("reflect", self._reflect_node)
            wf.add_node("refine", self._refine_node)

            wf.add_edge("generate", "reflect")
            wf.add_conditional_edges(
                "reflect",
                self._route_after_reflect,
                {"save": "save", "refine": "refine"},
            )
            wf.add_edge("refine", "save")
            logger.info("Graph: reflection pipeline ENABLED (threshold=%d)", settings.REFLECTION_THRESHOLD)
        else:
            wf.add_edge("generate", "save")
            logger.info("Graph: reflection pipeline DISABLED")

        wf.add_edge("save", END)

        return wf.compile()

    @staticmethod
    def _route_after_router_v2(state: Dict[str, Any]) -> str:
        qt = state.get("query_type", "domain")
        if qt == "blocked":
            return "blocked"
        if qt == "general":
            return "gather"
        return "gather_all"  # domain

    # ──────────────────────────────────────────────────────────────────
    # 1. ROUTER – classify + safety gate + chat name
    # ──────────────────────────────────────────────────────────────────

    async def _router_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = sanitize_query(state.get("query", ""))
        state["query"] = query
        q_lower = query.lower().strip()

        # ── Safety gate: block harmful / inappropriate queries ────────
        if self._is_blocked(q_lower):
            state["query_type"] = "blocked"
            state["chat_name"] = "Declined Request"
            state["answer"] = _DECLINE_MESSAGE
            logger.warning("Router: BLOCKED query — '%s'", query[:80])
            return state

        # ── Fast-track greetings / casual messages ─────────────────────
        if self._is_greeting(q_lower):
            state["query_type"] = "general"
            state["chat_name"] = "Greeting"
            state["general_answer"] = ""  # generate node will handle it
            logger.info("Router: greeting → general (fast path)")
            return state

        # ── Fast-track follow-ups ─────────────────────────────────────
        is_follow_up = any(ind in q_lower for ind in _FOLLOW_UP_INDICATORS)
        state["is_follow_up"] = is_follow_up
        if is_follow_up:
            state["query_type"] = "domain"
            state["chat_name"] = "Follow-up Question"
            logger.info("Router: follow-up → domain")
            return state

        # ── LLM classification ────────────────────────────────────────
        llm = self.llm_router.get_llm()
        prompt = (
            "You are AdvisorAI, an academic advisor for Stevens Institute of Technology.\n"
            "Classify the query and generate a chat name.\n\n"
            f'Query: "{query}"\n\n'
            "Rules:\n"
            '- "general" → greetings (hi, hello, hey, good morning, etc.), '
            "casual conversation, OR pure general knowledge NOT Stevens-specific "
            "but still appropriate (e.g. 'What is machine learning?', 'hello', "
            "'how are you?', 'thanks', 'goodbye')\n"
            '- "domain" → ANYTHING Stevens-related or that may be in university '
            "docs (courses, professors, admissions, campus, etc.).\n"
            '- "blocked" → query is harmful, inappropriate, offensive, contains '
            "violence, hate speech, explicit content, foul language, profanity, "
            "requests to cheat, asks about AdvisorAI's internal technology / "
            "backend / database / source code / architecture, or is "
            "completely unrelated to education / academics / university life.\n\n"
            "Return ONLY valid JSON:\n"
            '{"query_type":"general"|"domain"|"blocked",'
            '"chat_name":"3-8 words","reasoning":"one line"}'
        )

        try:
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            parsed = parse_llm_json(resp.content)
            if parsed:
                qt = parsed.get("query_type", "domain")
                if qt not in ("general", "domain", "blocked"):
                    qt = "domain"
                state["query_type"] = qt
                state["chat_name"] = parsed.get("chat_name", "New Chat")
                logger.info("Router: type=%s name='%s'", qt, state["chat_name"])

                # If LLM classified as blocked, set decline message
                if qt == "blocked":
                    state["answer"] = _DECLINE_MESSAGE
            else:
                state["query_type"] = self._fallback_classify(query)
                state["chat_name"] = "New Chat"
        except Exception as exc:
            logger.error("Router error: %s", exc, exc_info=True)
            state["query_type"] = self._fallback_classify(query)
            state["chat_name"] = "New Chat"

        return state

    @staticmethod
    def _is_blocked(query_lower: str) -> bool:
        """Fast regex-based safety check (runs before the LLM call)."""
        return any(p.search(query_lower) for p in _COMPILED_BLOCKED)

    @staticmethod
    def _is_greeting(query_lower: str) -> bool:
        """Detect short greetings / casual messages that don't need tools."""
        # Strip punctuation for matching
        clean = re.sub(r"[^\w\s]", "", query_lower).strip()
        # Exact match or very short query that matches a greeting
        if clean in _GREETING_PATTERNS:
            return True
        # Also match if the query is very short (≤ 4 words) and starts with a greeting
        words = clean.split()
        if len(words) <= 4:
            for g in _GREETING_PATTERNS:
                if clean.startswith(g):
                    return True
        return False

    @staticmethod
    def _fallback_classify(query: str) -> str:
        q = query.lower()
        kws = [
            "stevens", "course", "faculty", "professor", "program",
            "admission", "campus", "hoboken", "department", "degree",
            "major", "minor", "tuition", "scholarship", "housing",
            "registrar", "transcript", "gpa", "credit", "semester",
        ]
        return "domain" if any(k in q for k in kws) else "general"

    @staticmethod
    def _route_after_router(state: Dict[str, Any]) -> str:
        return "blocked" if state.get("query_type") == "blocked" else "gather"

    # ──────────────────────────────────────────────────────────────────
    # 2. GATHER – run tools (always history; chroma OR general)
    # ──────────────────────────────────────────────────────────────────

    async def _gather_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight gather for general queries — ONLY history.

        The generate node will answer directly from its own LLM call,
        so we skip the redundant general_agent LLM call (saves ~1.5s).
        """
        logger.info("Gather: running [history] only (general fast path)")
        try:
            res = await self.history_agent.process(state.copy())
            if isinstance(res, dict) and "history_results" in res:
                state["history_results"] = res["history_results"]
        except Exception as exc:
            logger.error("Gather: history failed: %s", exc)
            state["history_error"] = str(exc)

        return state

    # ──────────────────────────────────────────────────────────────────
    # 2b. GATHER_ALL – domain queries: history + chroma + web IN PARALLEL
    # ──────────────────────────────────────────────────────────────────

    async def _gather_all_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run history, chroma, AND web search all in parallel.

        This replaces the old sequential gather → evaluate → web_search flow
        and cuts ~5-8 seconds of wall-clock time by overlapping I/O.
        """
        query = state.get("query", "")

        # ── Query rewriting for follow-ups (runs BEFORE parallel dispatch) ──
        # This ensures both chroma and web get the rewritten query.
        effective_query = query
        is_follow_up = state.get("is_follow_up", False)
        if is_follow_up and state.get("chat_history"):
            try:
                rewritten = await self.chroma_agent.chroma_tool._rewrite_query(
                    sanitize_query(query),
                    self.chroma_agent._parse_history_string(
                        state.get("chat_history", "")
                    ),
                )
                if rewritten and rewritten != query:
                    effective_query = rewritten
                    state["rewritten_query"] = effective_query
                    logger.info(
                        "GatherAll: query rewritten '%s' → '%s'",
                        query[:60], effective_query[:60],
                    )
            except Exception as e:
                logger.warning("GatherAll: query rewriting failed: %s", e)

        # Build a web search query from the (possibly rewritten) query
        search_q = self._quick_search_query(effective_query)
        state["web_search_query"] = search_q

        # Prepare states — chroma and web both use the effective query
        chroma_state = state.copy()
        chroma_state["query"] = effective_query

        web_state = state.copy()
        web_state["query"] = search_q

        # Run all three in parallel
        tasks = [
            self.history_agent.process(state.copy()),
            self.chroma_agent.process(chroma_state),
            self.web_agent.process(web_state),
        ]
        names = ["history", "chroma", "web"]

        logger.info(
            "GatherAll: running %s in parallel (query='%s'%s)",
            names, effective_query[:60],
            f", rewritten from '{query[:40]}'" if effective_query != query else "",
        )
        results = await asyncio.gather(*tasks, return_exceptions=True)

        _KEYS = {
            "history": ("history_results",),
            "chroma": ("chroma_results", "collections_searched", "chroma_error"),
            "web": ("web_results",),
        }
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                logger.error("GatherAll: '%s' failed: %s", name, res)
                state[f"{name}_error"] = str(res)
            elif isinstance(res, dict):
                for key in _KEYS.get(name, ()):
                    if key in res:
                        val = res[key]
                        # Tag web results with original query info
                        if name == "web" and isinstance(val, dict):
                            val["original_query"] = query
                            val["search_query_used"] = search_q
                        state[key] = val

        # Log web search outcome
        web = state.get("web_results", {})
        web_ok = web.get("success", False)
        web_urls = web.get("search_results", []) or []
        wc = web.get("scraped_content") or web.get("web_content", "")
        logger.info(
            "GatherAll: web success=%s urls=%d content_len=%d",
            web_ok, len(web_urls), len(wc),
        )

        return state

    @staticmethod
    def _quick_search_query(query: str) -> str:
        """Build a web search query without an LLM call (instant).

        Simply appends 'Stevens Institute of Technology' if not already present.
        This saves an entire LLM round-trip (~1.5s).
        """
        q = sanitize_query(query).strip()
        if "stevens" not in q.lower():
            q = f"{q} Stevens Institute of Technology"
        return q

    # ──────────────────────────────────────────────────────────────────
    # 5. GENERATE – synthesise the draft answer
    # ──────────────────────────────────────────────────────────────────

    async def _generate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("rewritten_query") or state.get("query", "")
        history_results = state.get("history_results", {})
        llm = self.llm_router.get_llm()

        # ── Build context ────────────────────────────────────────────
        ctx: List[str] = []
        has_info = False

        # Keep last 3 history exchanges (not 10+) to reduce context
        hist = history_results.get("relevant_history", [])[-3:]
        if hist:
            ctx.append("=== Conversation History ===")
            for i, e in enumerate(hist, 1):
                ctx.append(f"Q{i}: {e.get('query', '')[:300]}")
                ctx.append(f"A{i}: {e.get('response', '')[:500]}")
            ctx.append("")

        # Limit to 3 chroma docs (not 5) to cut context size
        chroma = state.get("chroma_results", {})
        if chroma.get("documents"):
            ctx.append("=== University Database ===")
            for i, d in enumerate(chroma["documents"][:3], 1):
                ctx.append(f"[{i}]: {d['content'][:800]}")
            has_info = True

        web = state.get("web_results", {})
        wc = web.get("scraped_content") or web.get("web_content", "")
        web_urls = web.get("search_results", []) or []
        web_query_used = web.get("search_query_used") or web.get("query", "")
        web_context_included = False
        if wc and len(wc.strip()) > 20:
            web_context_included = True
            ctx.append("=== Web Search Results ===")
            if web_query_used:
                ctx.append(f"Web query used: {web_query_used}")
            if web_urls:
                ctx.append("Web URLs:")
                for i, url in enumerate(web_urls[:3], 1):
                    ctx.append(f"- [{i}] {url}")
            ctx.append("Web content:")
            ctx.append(wc[:settings.WEB_CONTENT_MAX_CHARS])
            has_info = True

        gen = state.get("general_answer")
        if gen and len(gen.strip()) > 20:
            ctx.append("=== General Knowledge ===")
            ctx.append(gen[:800])
            has_info = True

        context_text = "\n\n".join(ctx) if ctx else ""

        # ── Extra instructions based on context ──────────────────────
        extra = ""
        if hist:
            extra += (
                f"\nYou have {len(hist)} previous conversation(s). "
                "ALWAYS use them for context. NEVER claim you lack history.\n"
            )
        if not has_info and not hist:
            extra += (
                "\n⚠️ No specific information was found for this query. "
                "Let the student know you currently don't have that "
                "information but offer to help with other Stevens-related "
                "questions they may have.\n"
            )
        elif not has_info and hist:
            extra += (
                "\n⚠️ No new information found, but history is available. "
                "Answer from history context. If the current question is "
                "about something new, let the student know you don't have "
                "that specific information right now and offer to help with "
                "other questions.\n"
            )

        prompt = f"""You are **AdvisorAI**, a knowledgeable and friendly academic advisor built exclusively for Stevens Institute of Technology.
You have access to an extensive university database and live web search to find answers.

IDENTITY:
- Your name is **AdvisorAI**. You are NOT OpenAI, ChatGPT, GPT, Gemini, Google, Claude, or any other AI product.
- If asked "who are you?", "what are you?", or about your identity, always say: "I'm AdvisorAI, your personal academic advisor for Stevens Institute of Technology."
- NEVER reveal or mention the underlying AI model, API, or technology you are built on.
- NEVER say "as an AI language model" or "as a large language model" — instead say "as your academic advisor" or "as AdvisorAI".

STRICT BOUNDARIES:
- NEVER mention or reveal ANY internal technology: no database names (ChromaDB, MongoDB, etc.), no frameworks (LangChain, LangGraph, Flask, React, etc.), no embedding models, no vector stores, no APIs, no backend/frontend architecture.
- If asked about your technology, source code, how you work internally, or your architecture, politely say: "I'm AdvisorAI, built to help you with everything about Stevens! How can I assist you with your academics?"
- NEVER respond to foul language, profanity, or offensive content. Politely redirect: "I'm here to help with your Stevens-related questions! What can I assist you with?"
- ONLY answer questions related to Stevens Institute of Technology: courses, professors, programs, admissions, campus, academic policies, student life, career services, research, and general academic topics.
- For questions completely unrelated to Stevens or academics, politely decline and offer to help with Stevens-related topics instead.

Question: "{sanitize_query(query)}"

{context_text}
{extra}
INSTRUCTIONS:
1. Answer using ALL available information above — be thorough and specific.
2. Include concrete details: names, dates, requirements, course codes when available.
3. If you have partial information, share what you know and say you can look into it further.
4. Be conversational, warm, and actionable — give real answers students can act on.
5. For follow-up questions, reference conversation history directly.
6. If "=== Web Search Results ===" is present, you MUST use that information directly in your answer.
7. NEVER hallucinate or make up facts not present in the context above.
8. NEVER tell the student to "visit the website" or "check the website" or "go to stevens.edu" — YOU are their resource. If you don't have the info, simply say so and offer to help with other questions.
9. When web results are available, reference at least one concrete fact from that section.
10. NEVER suggest the student "contact the university" or "reach out to admissions" as a first response. Only mention contacting a specific office (with the office name) as a last resort for very specific personal matters (e.g. financial aid status, individual transcript issues).
11. NEVER mention OpenAI, GPT, ChatGPT, Gemini, Google AI, Claude, Anthropic, or any other AI product name in your responses.
12. NEVER mention any technical terms like database, vector store, ChromaDB, MongoDB, embeddings, LangChain, API, backend, frontend, retrieval, or any internal system detail in your response. Your answer must read as if it comes from a knowledgeable human advisor.
13. If the query contains profanity or foul language, do NOT engage with the content. Respond with a polite redirect to Stevens-related topics.

FORMATTING:
- Use **bold** for important terms, course names, professor names, and key concepts.
- Use *italic* for emphasis and to highlight important points.
- Use bullet points (-) or numbered lists (1.) when listing multiple items, requirements, or steps.
- Use `code formatting` for course codes, technical terms, or specific identifiers.
- Use headers (##) to organize longer responses into clear sections when appropriate.
- Format your response in markdown to make it visually appealing and easy to read.

Answer:"""

        # Log a truncated view of the prompt/context for observability
        logger.info(
            "Generate: prompt for query '%s' (len=%d, context_len=%d)",
            query[:80],
            len(prompt),
            len(context_text),
        )
        logger.info(
            "Generate: context sections → history=%s chroma=%s web=%s general=%s",
            bool(hist),
            bool(chroma.get("documents")),
            web_context_included,
            bool(gen and len(gen.strip()) > 20),
        )
        if web_context_included:
            logger.info(
                "Generate: web context included (query='%s', urls=%d, content_len=%d)",
                (web_query_used or "")[:120],
                len(web_urls),
                len(wc.strip()),
            )
            logger.info(
                "Generate: web content preview (first 400 chars): %s",
                wc[:400],
            )

        try:
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            raw_answer = resp.content.strip()
            logger.info(
                "Generate: LLM raw answer (first 500 chars): %s",
                raw_answer[:500],
            )
            answer = clean_response(raw_answer)
            state["draft_answer"] = answer
            if not settings.REFLECTION_ENABLED:
                state["answer"] = answer
            logger.info("Generate: draft %d chars", len(answer))
        except Exception as exc:
            logger.error("Generate error: %s", exc, exc_info=True)
            fallback = (
                "I'm sorry, I ran into an issue while looking that up. "
                "Could you try asking again? I'm here to help!"
            )
            state["draft_answer"] = fallback
            state["answer"] = fallback

        return state

    # ──────────────────────────────────────────────────────────────────
    # 6. REFLECT – self-critique the draft answer
    # ──────────────────────────────────────────────────────────────────

    async def _reflect_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Score the draft answer 1-10 and provide improvement feedback."""
        query = state.get("rewritten_query") or state.get("query", "")
        draft = state.get("draft_answer", "")
        llm = self.llm_router.get_llm()

        threshold = settings.REFLECTION_THRESHOLD

        sources: List[str] = []
        if state.get("chroma_results", {}).get("documents"):
            sources.append(f"{len(state['chroma_results']['documents'])} database docs")
        if state.get("web_results", {}).get("success"):
            sources.append("web search results")
        if state.get("general_answer"):
            sources.append("general LLM knowledge")
        if state.get("history_results", {}).get("relevant_history"):
            sources.append(f"{len(state['history_results']['relevant_history'])} history entries")

        prompt = f"""You are a quality-assurance reviewer for an academic advising chatbot
at Stevens Institute of Technology.

ORIGINAL QUESTION: "{sanitize_query(query)}"

AVAILABLE SOURCES: {', '.join(sources) if sources else 'None'}

DRAFT ANSWER:
\"\"\"
{draft[:2000]}
\"\"\"

Evaluate on these criteria:
1. **Relevance** – Does it directly answer the question?
2. **Completeness** – Does it address all parts of the question?
3. **Accuracy** – Is it grounded in sources (no hallucination)?
4. **Helpfulness** – Is it actionable and student-friendly?
5. **Tone** – Is it warm, conversational, and confident?
6. **Self-sufficiency** – Does it AVOID telling the student to "visit the website", "check the website", "go to stevens.edu", or "contact the university"? The chatbot should be the student's resource, not a redirect service. (Score lower if it deflects to a website.)
7. **Web source usage** – If web search results were available, does the answer actually USE specific facts from those results? (Score lower if it ignores web data.)
8. **No tech leakage** – Does the answer avoid mentioning ANY internal technology (database, ChromaDB, MongoDB, vector store, embeddings, LangChain, API, backend, frontend, retrieval system, etc.)? Score 1 if ANY internal tech detail is exposed.
9. **Appropriate content** – Does the answer refuse to engage with profanity, foul language, or off-topic non-academic queries? Score 1 if the answer entertains inappropriate content.

Return ONLY valid JSON:
{{
  "score": <1-10>,
  "strengths": "what the answer does well",
  "weaknesses": "specific issues to fix (empty string if none)",
  "suggestion": "concrete instruction to improve the answer (empty string if none)"
}}"""

        try:
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            parsed = parse_llm_json(resp.content)

            if parsed:
                score = int(parsed.get("score", 10))
                score = max(1, min(10, score))
                reflection = {
                    "score": score,
                    "strengths": parsed.get("strengths", ""),
                    "weaknesses": parsed.get("weaknesses", ""),
                    "suggestion": parsed.get("suggestion", ""),
                    "is_acceptable": score >= threshold,
                }
            else:
                reflection = {
                    "score": 8, "is_acceptable": True,
                    "strengths": "", "weaknesses": "", "suggestion": "",
                }

            state["reflection"] = reflection

            if reflection["is_acceptable"]:
                state["answer"] = draft
                logger.info("Reflect: score=%d (threshold=%d) → ACCEPT", reflection["score"], threshold)
            else:
                logger.info(
                    "Reflect: score=%d (threshold=%d) → REFINE (weaknesses: %s)",
                    reflection["score"], threshold,
                    reflection.get("weaknesses", "")[:120],
                )
        except Exception as exc:
            logger.error("Reflect error: %s", exc, exc_info=True)
            state["reflection"] = {
                "score": 8, "is_acceptable": True,
                "strengths": "", "weaknesses": "", "suggestion": "",
            }
            state["answer"] = draft

        return state

    @staticmethod
    def _route_after_reflect(state: Dict[str, Any]) -> str:
        refl = state.get("reflection", {})
        return "save" if refl.get("is_acceptable", True) else "refine"

    # ──────────────────────────────────────────────────────────────────
    # 7. REFINE – improve the answer using reflection feedback
    # ──────────────────────────────────────────────────────────────────

    async def _refine_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Re-generate the answer incorporating reflection feedback."""
        query = state.get("rewritten_query") or state.get("query", "")
        draft = state.get("draft_answer", "")
        refl = state.get("reflection", {})
        llm = self.llm_router.get_llm()

        # Include web context in refine prompt so the LLM can use it
        web = state.get("web_results", {})
        wc = web.get("scraped_content") or web.get("web_content", "")
        web_section = ""
        if wc and len(wc.strip()) > 20:
            web_section = (
                f"\n\nAVAILABLE WEB DATA (use this to improve the answer):\n"
                f"{wc[:settings.WEB_CONTENT_MAX_CHARS]}\n"
            )

        prompt = f"""You are a friendly academic advisor at Stevens Institute of Technology.

QUESTION: "{sanitize_query(query)}"

Your previous answer had these issues:
- Weaknesses: {refl.get('weaknesses', 'None noted')}
- Suggestion: {refl.get('suggestion', 'None')}

PREVIOUS ANSWER:
\"\"\"
{draft[:2000]}
\"\"\"
{web_section}
Rewrite the answer to fix the issues above. Keep what was good:
- Strengths: {refl.get('strengths', 'N/A')}

RULES:
1. Fix the specific weaknesses identified.
2. Keep factual content that was correct.
3. If web data is provided above, use specific facts from it.
4. Be conversational, specific, and helpful.
5. NEVER tell the student to "visit the website" or "check stevens.edu" — YOU are their resource.
6. NEVER include meta-commentary like "here is my improved answer".
7. NEVER mention any internal technology (database, ChromaDB, MongoDB, vector store, embeddings, LangChain, API, backend, frontend, retrieval). Your answer must read as if from a knowledgeable human advisor.
8. If the question contains profanity or is off-topic, politely decline and redirect to Stevens-related topics.

Improved Answer:"""

        try:
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            state["answer"] = clean_response(resp.content.strip())
            logger.info(
                "Refine: improved answer %d chars (was %d)",
                len(state["answer"]), len(draft),
            )
        except Exception as exc:
            logger.error("Refine error: %s", exc, exc_info=True)
            state["answer"] = draft

        return state
            
    # ──────────────────────────────────────────────────────────────────
    # 8. SAVE – persist the conversation
    # ──────────────────────────────────────────────────────────────────
    
    async def _save_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        uid = state.get("user_id", "default")
        await self.memory_store.save_conversation(
            user_id=uid,
            query=state.get("query", ""),
            response=state.get("answer", ""),
            metadata={
                "query_type": state.get("query_type", "unknown"),
                "collections_searched": state.get("collections_searched", []),
                "web_search_performed": bool(
                    state.get("web_results", {}).get("success")
                ),
                "used_general_tool": state.get("used_general_tool", False),
                "is_follow_up": state.get("is_follow_up", False),
                "reflection_score": state.get("reflection", {}).get("score"),
                "was_refined": not state.get("reflection", {}).get(
                    "is_acceptable", True
                ),
            },
        )
        state["saved"] = True
        return state
    
    # ══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════

    # User-friendly labels for each graph node
    _NODE_STATUS = {
        "router":      "Understanding your question…",
        "gather":      "Searching knowledge base…",
        "gather_all":  "Searching database & web simultaneously…",
        "generate":    "Generating response…",
        "reflect":     "Reviewing answer quality…",
        "refine":      "Improving response…",
        "save":        "Finishing up…",
    }

    async def process_query(
        self, query: str, user_id: str = "default", chat_history: str = ""
    ) -> Dict[str, Any]:
        initial: Dict[str, Any] = {
            "query": query,
            "user_id": user_id,
            "chat_history": chat_history,
        }
        
        try:
            logger.info("Processing: '%s'", query[:100])
            fs = await self.graph.ainvoke(initial)

            return self._build_result(fs)
        except Exception as exc:
            logger.error("Pipeline error: %s", exc, exc_info=True)
            return {
                "success": False,
                "error": str(exc),
                "answer": (
                    "I'm sorry, I ran into a technical issue. "
                    "Could you try asking again? I'm here to help!"
                ),
            }

    async def stream_process_query(
        self, query: str, user_id: str = "default", chat_history: str = ""
    ):
        """Async generator: status → token → result.

        Yields:
            {"type": "status", "node": "<name>", "content": "<label>", ...}
            {"type": "token",  "content": "<text chunk>"}
            {"type": "result", ...}

        The pipeline runs normally through router → gather/gather_all,
        then we **stream tokens directly from the generate LLM** so
        the user sees text appearing in real-time (true streaming).
        """
        initial: Dict[str, Any] = {
            "query": query,
            "user_id": user_id,
            "chat_history": chat_history,
        }

        try:
            logger.info("Stream-processing: '%s'", query[:100])
            final_state: Dict[str, Any] = {}
            prev_nodes: set = set()

            # ── Phase 1: run pipeline up to (but NOT including) generate ──
            # We stream node-by-node and emit status events, stopping
            # before generate so we can stream its tokens ourselves.
            async for state_snapshot in self.graph.astream(
                initial, stream_mode="values"
            ):
                if hasattr(state_snapshot, "items"):
                    final_state = dict(state_snapshot)
                else:
                    final_state = state_snapshot

                completed = self._detect_completed_node(final_state, prev_nodes)
                if completed:
                    prev_nodes.add(completed)
                    label = self._NODE_STATUS.get(
                        completed, f"Processing ({completed})…"
                    )
                    logger.info("Stream node complete: %s", completed)

                    event = {"type": "status", "node": completed, "content": label}

                    if completed == "gather_all":
                        # Include rich source details for Perplexity-style UI
                        web = final_state.get("web_results", {}) or {}
                        urls = web.get("search_results", [])
                        chroma_docs = final_state.get("chroma_results", {}).get("documents", [])
                        hist_entries = final_state.get("history_results", {}).get("relevant_history", [])
                        sources_summary = {
                            "database_docs": len(chroma_docs),
                            "web_urls": urls,
                            "web_success": web.get("success", False),
                            "history_entries": len(hist_entries),
                            "collections": final_state.get("collections_searched", []),
                        }
                        event["sources"] = sources_summary
                        if urls:
                            event["urls"] = urls
                        parts = []
                        if chroma_docs:
                            parts.append(f"📚 {len(chroma_docs)} database docs")
                        if urls:
                            parts.append(f"🌐 {len(urls)} web pages")
                        if hist_entries:
                            parts.append(f"💬 {len(hist_entries)} past conversations")
                        event["content"] = "Found: " + ", ".join(parts) if parts else label

                    elif completed == "gather":
                        hist_entries = final_state.get("history_results", {}).get("relevant_history", [])
                        if hist_entries:
                            event["content"] = f"Found {len(hist_entries)} past conversations…"

                    yield event

            # ── Phase 2: if answer exists (generate already ran inside graph),
            #    stream its tokens word-by-word for a smooth UX ────────────
            answer = final_state.get("answer", "") or final_state.get("draft_answer", "")
            if answer:
                logger.info("Stream: answer ready (%d chars), streaming tokens", len(answer))
                # yield answer in small chunks for smooth display
                words = answer.split(" ")
                CHUNK = 2
                for i in range(0, len(words), CHUNK):
                    chunk_words = words[i:i + CHUNK]
                    token = " ".join(chunk_words)
                    if i > 0:
                        token = " " + token
                    yield {"type": "token", "content": token}

            # ── Phase 3: save conversation ────────────────────────────────
            # Save was already done by the graph, so just emit result
            logger.info(
                "Stream: final answer length=%d chars",
                len(final_state.get("answer", "")),
            )

            yield {"type": "result", **self._build_result(final_state)}

        except Exception as exc:
            logger.error("Stream pipeline error: %s", exc, exc_info=True)
            yield {
                "type": "result",
                "success": False,
                "error": str(exc),
                "answer": (
                    "I'm sorry, I ran into a technical issue. "
                    "Could you try asking again? I'm here to help!"
                ),
            }

    @staticmethod
    def _detect_completed_node(
        state: Dict[str, Any], already_seen: set
    ) -> str | None:
        """Infer which pipeline node just completed based on state keys.

        Markers are checked in reverse-pipeline order.  The ``already_seen``
        set ensures each node is only reported once; once a node is
        detected it is added to ``already_seen`` by the caller.
        """
        markers: list[tuple[str, Any]] = [
            ("router",      lambda s: "query_type" in s),
            ("gather",      lambda s: ("history_results" in s or "general_answer" in s)
                                       and s.get("query_type") == "general"),
            ("gather_all",  lambda s: ("web_results" in s or "chroma_results" in s)
                                       and "history_results" in s
                                       and s.get("query_type") != "general"),
            ("generate",    lambda s: "draft_answer" in s),
            ("reflect",     lambda s: "reflection" in s),
            ("refine",      lambda s: "reflection" in s
                                      and not s["reflection"].get("is_acceptable", True)
                                      and "answer" in s and s.get("answer")),
            ("save",        lambda s: s.get("saved")),
        ]
        detected = None
        for node, check in markers:
            if node not in already_seen and check(state):
                detected = node
        return detected

    # ── helpers ────────────────────────────────────────────────────────

    def _build_result(self, fs: Dict[str, Any]) -> Dict[str, Any]:
        web_results = fs.get("web_results", {}) or {}
        # Prefer answer; fall back to draft_answer if answer is empty
        answer = fs.get("answer", "") or fs.get("draft_answer", "")
        return {
            "success": True,
            "answer": answer,
            "metadata": {
                "query_type": fs.get("query_type", "unknown"),
                "tools_used": self._tools_used(fs),
                "collections_searched": fs.get("collections_searched", []),
                "web_search_performed": bool(web_results.get("success")),
                "used_general_tool": fs.get("used_general_tool", False),
                "reasoning_result": {
                    "react_thought": fs.get("react_thought", ""),
                    "need_web_search": fs.get("need_web_search", False),
                },
                "reflection": fs.get("reflection", {}),
                "chat_name": fs.get("chat_name", "New Chat"),
                "is_follow_up": fs.get("is_follow_up", False),
                # Expose web search details so the UI can show links
                "web_search": {
                    "query": web_results.get("query"),
                    "original_query": web_results.get("original_query"),
                    "urls": web_results.get("search_results", []),
                    "success": web_results.get("success", False),
                },
            },
        }

    @staticmethod
    def _tools_used(state: Dict[str, Any]) -> List[str]:
        used = ["history"]
        if state.get("chroma_results", {}).get("documents"):
            used.append("chroma")
        if state.get("web_results", {}).get("success"):
            used.append("web")
        if state.get("used_general_tool"):
            used.append("general")
        return used
