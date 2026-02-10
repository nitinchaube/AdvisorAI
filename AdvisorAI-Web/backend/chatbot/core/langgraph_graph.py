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


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

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
    _REFLECTION_THRESHOLD = 7

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
        wf = StateGraph(ChatState)

        wf.add_node("router", self._router_node)
        wf.add_node("gather", self._gather_node)
        wf.add_node("evaluate", self._evaluate_node)
        wf.add_node("web_search", self._web_search_node)
        wf.add_node("generate", self._generate_node)
        wf.add_node("reflect", self._reflect_node)
        wf.add_node("refine", self._refine_node)
        wf.add_node("save", self._save_node)

        wf.set_entry_point("router")

        # Safety gate: blocked queries go straight to save (answer already set)
        wf.add_conditional_edges(
            "router",
            self._route_after_router,
            {"blocked": "save", "gather": "gather"},
        )

        wf.add_edge("gather", "evaluate")
        wf.add_conditional_edges(
            "evaluate",
            self._route_after_evaluate,
            {"web_search": "web_search", "generate": "generate"},
        )
        wf.add_edge("web_search", "generate")

        wf.add_edge("generate", "reflect")
        wf.add_conditional_edges(
            "reflect",
            self._route_after_reflect,
            {"refine": "refine", "save": "save"},
        )
        wf.add_edge("refine", "save")
        wf.add_edge("save", END)

        return wf.compile()

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
            "You are an AI assistant for Stevens Institute of Technology.\n"
            "Classify the query and generate a chat name.\n\n"
            f'Query: "{query}"\n\n'
            "Rules:\n"
            '- "blocked" → query is harmful, inappropriate, offensive, contains '
            "violence, hate speech, explicit content, requests to cheat, or is "
            "completely unrelated to education / academics / university life.\n"
            '- "general" → pure general knowledge NOT Stevens-specific but still '
            "appropriate (e.g. 'What is machine learning?')\n"
            '- "domain" → ANYTHING Stevens-related or that may be in university '
            'docs. When in doubt pick "domain".\n\n'
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
        qt = state.get("query_type", "domain")
        tasks, names = [], []

        tasks.append(self.history_agent.process(state.copy()))
        names.append("history")

        if qt == "domain":
            tasks.append(self.chroma_agent.process(state.copy()))
            names.append("chroma")
        else:
            tasks.append(self.general_agent.process(state.copy()))
            names.append("general")

        logger.info("Gather: running %s (type=%s)", names, qt)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        _KEYS = {
            "history": ("history_results",),
            "chroma": ("chroma_results", "collections_searched", "chroma_error"),
            "general": ("general_answer", "used_general_tool", "general_error"),
        }
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                logger.error("Gather: '%s' failed: %s", name, res)
                state[f"{name}_error"] = str(res)
            elif isinstance(res, dict):
                for key in _KEYS.get(name, ()):
                    if key in res:
                        state[key] = res[key]
        
        return state
    
    # ──────────────────────────────────────────────────────────────────
    # 3. EVALUATE – ReAct THINK
    # ──────────────────────────────────────────────────────────────────

    async def _evaluate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ReAct *Think* step: examine gathered data and decide next action.

        Behaviour:
        - For **general** queries → rely on general LLM tool only (no web search)
        - For **non-general** (domain / follow-ups) → ALWAYS run web search
          in addition to history + chroma/general.
        """
        qt = state.get("query_type", "domain")
        query = state.get("query", "")

        # ── General queries: keep lightweight, no web search ─────────────
        if qt == "general":
            state["react_thought"] = (
                "THINK: General knowledge question. The general agent has "
                "already produced an answer. Skipping web search."
            )
            state["need_web_search"] = False
            logger.info("Evaluate: general → skip web")
            return state

        # ── Domain / follow-up queries: ALWAYS include web search ────────
        chroma = state.get("chroma_results", {})
        docs = chroma.get("documents", [])
        good_docs = [
            d
            for d in docs
            if d.get("metadata", {}).get("similarity_score", 999)
            < self._SIMILARITY_THRESHOLD
        ]
        history = state.get("history_results", {})
        hist_count = len(history.get("relevant_history", []))

        thought_lines = [
            f"THINK: Query is domain-specific: '{query[:80]}...'",
            f"  - Conversation history entries: {hist_count}",
            f"  - Chroma documents retrieved: {len(docs)}",
            f"  - Quality documents (score < {self._SIMILARITY_THRESHOLD}): {len(good_docs)}",
            f"  - Minimum quality docs needed: {self._MIN_GOOD_DOCS}",
            "DECIDE: For domain queries, ALWAYS include web search in parallel "
            "with vector DB and history to maximise coverage.",
        ]

        # Always request web search for non-general queries
        state["need_web_search"] = True
        state["web_search_query"] = await self._make_search_query(query, chroma, history)

        state["react_thought"] = "\n".join(thought_lines)
        logger.info(
            "Evaluate: docs=%d good=%d → web_search=%s (forced for domain)",
            len(docs),
            len(good_docs),
            state["need_web_search"],
        )
        return state

    async def _make_search_query(self, original: str, chroma: Dict[str, Any], history: Dict[str, Any]) -> str:
        """Generate a rich, Stevens-focused web search query via LLM.

        Uses the original question + a brief summary of what we ALREADY know
        from Chroma and conversation history so the web search can focus on
        missing details instead of repeating the same info.
        """
        llm = self.llm_router.get_llm()

        # Build short hints from Chroma documents (titles / first sentences)
        chroma_docs = chroma.get("documents", []) or []
        chroma_hints = []
        for d in chroma_docs[:3]:
            text = (d.get("content") or "").strip()
            if text:
                chroma_hints.append(text[:200])

        # Build short hints from recent history answers
        hist_entries = history.get("relevant_history", []) or []
        hist_hints = []
        for e in hist_entries[-3:]:
            ans = (e.get("response") or "").strip()
            if ans:
                hist_hints.append(ans[:200])

        hints_text = ""
        if chroma_hints:
            hints_text += "KNOWN FROM UNIVERSITY DATABASE:\n- " + "\n- ".join(chroma_hints) + "\n\n"
        if hist_hints:
            hints_text += "KNOWN FROM PREVIOUS ANSWERS:\n- " + "\n- ".join(hist_hints) + "\n\n"

        prompt = (
            "You are helping a Stevens Institute of Technology academic advisor "
            "craft a precise web search query.\n\n"
            f"STUDENT QUESTION:\n\"{sanitize_query(original)}\"\n\n"
            f"{hints_text if hints_text else 'There is little or no existing context.'}\n"
            "TASK:\n"
            "- Generate ONE short web search query (8–16 words)\n"
            "- It MUST include the phrase 'Stevens Institute of Technology'\n"
            "- Focus on the SPECIFIC missing facts the student is likely asking about "
            "(requirements, deadlines, policies, course details, etc.).\n"
            "- Do NOT include quotation marks or commentary.\n"
            "- Return ONLY the raw search query text."
        )

        # Log search-query prompt for debugging/observability
        logger.info(
            "MakeSearchQuery: original='%s' chroma_docs=%d hist_entries=%d",
            original[:80],
            len(chroma_docs),
            len(hist_entries),
        )

        try:
            resp = await llm.ainvoke([{"role": "user", "content": prompt}])
            q = resp.content.strip().strip('"').strip("'")
            logger.info("MakeSearchQuery: LLM raw search query='%s'", q)
            # Guarantee Stevens is in the query
            if "stevens" not in q.lower():
                q = f"{q} Stevens Institute of Technology"
            # Ensure it's not empty and has some length
            return q if len(q.split()) >= 4 else f"{original} Stevens Institute of Technology"
        except Exception:
            return f"{original} Stevens Institute of Technology"

    @staticmethod
    def _route_after_evaluate(state: Dict[str, Any]) -> str:
        return "web_search" if state.get("need_web_search") else "generate"

    # ──────────────────────────────────────────────────────────────────
    # 4. WEB SEARCH – ReAct ACT
    # ──────────────────────────────────────────────────────────────────
    
    async def _web_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        original = state.get("query", "")
        search_q = state.get("web_search_query", original)
        logger.info("Web search (ACT): '%s'", search_q)

        try:
            ws = state.copy()
            ws["query"] = search_q
            res = await self.web_agent.process(ws)

            web = res.get("web_results", {})
            if web:
                web["original_query"] = original
                web["search_query_used"] = search_q
                state["web_results"] = web
            else:
                state["web_results"] = {"success": False, "web_content": ""}
        except Exception as exc:
            logger.error("Web search error: %s", exc, exc_info=True)
            state["web_results"] = {
                "success": False, "error": str(exc), "web_content": "",
            }

        web_ok = state.get("web_results", {}).get("success", False)
        web_len = len(
            state.get("web_results", {}).get("scraped_content", "")
            or state.get("web_results", {}).get("web_content", "")
        )
        web_urls = state.get("web_results", {}).get("search_results", []) or []
        logger.info(
            "Web search observe: success=%s content_len=%d urls=%d",
            web_ok, web_len, len(web_urls)
        )
        state["react_thought"] = state.get("react_thought", "") + (
            f"\nACT: Executed web search with query '{search_q}'."
            f"\nOBSERVE: Web search {'succeeded' if web_ok else 'failed'}. "
            f"Content length: {web_len} chars."
        )
        return state

    # ──────────────────────────────────────────────────────────────────
    # 5. GENERATE – synthesise the draft answer
    # ──────────────────────────────────────────────────────────────────

    async def _generate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        history_results = state.get("history_results", {})
        llm = self.llm_router.get_llm()

        # ── Build context ────────────────────────────────────────────
        ctx: List[str] = []
        has_info = False

        hist = history_results.get("relevant_history", [])
        if hist:
            ctx.append("=== Conversation History ===")
            for i, e in enumerate(hist, 1):
                ctx.append(f"Q{i}: {e.get('query', '')}")
                ctx.append(f"A{i}: {e.get('response', '')}")
            ctx.append("")

        chroma = state.get("chroma_results", {})
        if chroma.get("documents"):
            ctx.append("=== University Database ===")
            for i, d in enumerate(chroma["documents"][:5], 1):
                ctx.append(f"[{i}]: {d['content']}")
            has_info = True

        web = state.get("web_results", {})
        wc = web.get("scraped_content") or web.get("web_content", "")
        web_urls = web.get("search_results", []) or []
        web_query_used = web.get("search_query_used") or web.get("query", "")
        web_context_included = False
        # Use web results even when content is modest, as long as it's non-trivial
        if wc and len(wc.strip()) > 20:
            web_context_included = True
            ctx.append("=== Web Search Results ===")
            if web_query_used:
                ctx.append(f"Web query used: {web_query_used}")
            if web_urls:
                ctx.append("Web URLs:")
                for i, url in enumerate(web_urls[:5], 1):
                    ctx.append(f"- [{i}] {url}")
            ctx.append("Web content:")
            ctx.append(wc[:3000])
            has_info = True

        gen = state.get("general_answer")
        if gen and len(gen.strip()) > 20:
            ctx.append("=== General Knowledge ===")
            ctx.append(gen[:1500])
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

        prompt = f"""You are a knowledgeable and friendly academic advisor at Stevens Institute of Technology.
You have access to an extensive university database and live web search to find answers.

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
            state["draft_answer"] = clean_response(raw_answer)
            logger.info("Generate: draft answer %d chars", len(state["draft_answer"]))
        except Exception as exc:
            logger.error("Generate error: %s", exc, exc_info=True)
            state["draft_answer"] = (
                "I'm sorry, I ran into an issue while looking that up. "
                "Could you try asking again? I'm here to help!"
            )

        return state

    # ──────────────────────────────────────────────────────────────────
    # 6. REFLECT – self-critique the draft answer
    # ──────────────────────────────────────────────────────────────────

    async def _reflect_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Score the draft answer 1-10 and provide improvement feedback."""
        query = state.get("query", "")
        draft = state.get("draft_answer", "")
        llm = self.llm_router.get_llm()

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
                    "is_acceptable": score >= self._REFLECTION_THRESHOLD,
                }
            else:
                reflection = {
                    "score": 8, "is_acceptable": True,
                    "strengths": "", "weaknesses": "", "suggestion": "",
                }

            state["reflection"] = reflection

            if reflection["is_acceptable"]:
                state["answer"] = draft
                logger.info("Reflect: score=%d → ACCEPT", reflection["score"])
            else:
                logger.info(
                    "Reflect: score=%d → REFINE (weaknesses: %s)",
                    reflection["score"], reflection.get("weaknesses", "")[:120],
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
        query = state.get("query", "")
        draft = state.get("draft_answer", "")
        refl = state.get("reflection", {})
        llm = self.llm_router.get_llm()

        prompt = f"""You are a friendly academic advisor at Stevens Institute of Technology.

QUESTION: "{sanitize_query(query)}"

Your previous answer had these issues:
- Weaknesses: {refl.get('weaknesses', 'None noted')}
- Suggestion: {refl.get('suggestion', 'None')}

PREVIOUS ANSWER:
\"\"\"
{draft[:2000]}
\"\"\"

Rewrite the answer to fix the issues above. Keep what was good:
- Strengths: {refl.get('strengths', 'N/A')}

RULES:
1. Fix the specific weaknesses identified.
2. Keep factual content that was correct.
3. Do NOT add information not present in the original answer's sources.
4. Be conversational, specific, and helpful.
5. NEVER tell the student to "visit the website" or "check stevens.edu" — YOU are their resource.
6. NEVER include meta-commentary like "here is my improved answer".

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
        return state
    
    # ══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════

    # User-friendly labels for each graph node
    _NODE_STATUS = {
        "router":     "Understanding your question…",
        "gather":     "Searching knowledge base…",
        "evaluate":   "Analyzing information…",
        "web_search": "Searching the web for more info…",
        "generate":   "Generating response…",
        "reflect":    "Reviewing answer quality…",
        "refine":     "Polishing the response…",
        "save":       "Finishing up…",
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
        """Async generator that yields status events per node, then the result.

        Yields dicts of the form:
            {"type": "status", "node": "<name>", "content": "<user label>"}
            {"type": "result", ...}   (same shape as process_query return)

        Uses ``stream_mode="values"`` so each yield is the **full accumulated
        state** after a node completes — no manual merge needed.
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

            async for state_snapshot in self.graph.astream(
                initial, stream_mode="values"
            ):
                # state_snapshot is the full accumulated state after a node.
                # Convert to plain dict in case LangGraph wraps it.
                if hasattr(state_snapshot, "items"):
                    final_state = dict(state_snapshot)
                else:
                    final_state = state_snapshot

                # Detect which node just ran by checking new keys / changes
                # We use a heuristic: emit status for nodes whose marker keys
                # appeared since the last snapshot.
                completed = self._detect_completed_node(final_state, prev_nodes)
                if completed:
                    prev_nodes.add(completed)
                    label = self._NODE_STATUS.get(
                        completed, f"Processing ({completed})…"
                    )
                    logger.info("Stream node complete: %s", completed)

                    event = {"type": "status", "node": completed, "content": label}

                    # For web_search, include the URLs so the UI can show them
                    if completed == "web_search":
                        web = final_state.get("web_results", {}) or {}
                        urls = web.get("search_results", [])
                        if urls:
                            event["urls"] = urls
                            event["content"] = f"Reading {len(urls)} web pages…"

                    yield event

            # ── Safeguard: if answer is missing, fall back to draft ────
            if not final_state.get("answer") and final_state.get("draft_answer"):
                logger.warning(
                    "Stream: 'answer' empty but 'draft_answer' exists (%d chars) – using draft",
                    len(final_state["draft_answer"]),
                )
                final_state["answer"] = final_state["draft_answer"]

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
        """Infer which pipeline node just completed based on state keys."""
        # Order matters: check from last to first so we detect the latest node.
        _NODE_MARKERS = [
            ("save",       lambda s: "answer" in s and s.get("answer")),
            ("refine",     lambda s: s.get("reflection", {}).get("is_acceptable") is False
                                     and "answer" in s and s.get("answer")),
            ("reflect",    lambda s: "reflection" in s),
            ("generate",   lambda s: "draft_answer" in s),
            ("web_search", lambda s: "web_results" in s),
            ("evaluate",   lambda s: "react_thought" in s),
            ("gather",     lambda s: "history_results" in s or "chroma_results" in s),
            ("router",     lambda s: "query_type" in s),
        ]
        for node, check in _NODE_MARKERS:
            if node not in already_seen and check(state):
                return node
        return None

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
