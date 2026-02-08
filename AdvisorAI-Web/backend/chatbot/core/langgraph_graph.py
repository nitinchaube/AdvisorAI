"""
LangGraph orchestrator – the central workflow that routes queries through
tools (Chroma, web, history, general) using a ReAct-style approach.

Optimisations over the original implementation
-----------------------------------------------
* **Merged LLM calls**: Chat-name generation + tool selection happen in a
  single LLM call (was 2-3 separate calls).
* **Removed redundant classification**: GeneralAgent no longer re-classifies
  queries the router already classified.
* **Deterministic web-search gating**: The "reason" node uses a rule-based
  check first, falling back to LLM only when necessary (saves 1 LLM call
  in the common case).
* **Input sanitization**: All user queries are sanitised before being
  embedded in prompts.
* **Structured logging**: print() replaced by the ``chatbot`` logger.
"""

from typing import Dict, Any, List
from typing_extensions import TypedDict
import asyncio
import logging

from langgraph.graph import StateGraph, END

from agents.chroma_agent import ChromaAgent
from agents.web_agent import WebAgent
from agents.history_agent import HistoryAgent
from agents.general_agent import GeneralAgent
from core.llm_router import LLMRouter
from core.memory_store import get_memory_store
from core.utils import parse_llm_json, sanitize_query, clean_response

logger = logging.getLogger("chatbot")


# ── State schema ─────────────────────────────────────────────────────────

class ChatState(TypedDict, total=False):
    """Typed state flowing through the LangGraph workflow."""
    query: str
    user_id: str
    chat_history: str
    chat_name: str
    tool_decision: Dict[str, Any]
    chroma_results: Dict[str, Any]
    collections_searched: List[str]
    chroma_error: str
    history_results: Dict[str, Any]
    general_answer: str
    general_error: str
    used_general_tool: bool
    question_type: str
    web_results: Dict[str, Any]
    web_search_query: str
    reasoning_result: Dict[str, Any]
    answer: str


# ── Follow-up detection (shared with HistoryTool) ────────────────────────

_FOLLOW_UP_INDICATORS = frozenset(
    [
        "try again", "check again", "again", "repeat", "what about", "how about",
        "previous question", "last question", "my previous question",
        "repeat that", "say that again", "can you repeat", "what was that",
        "remind me", "recall", "remember", "what did you say", "can you clarify",
        "previous questions", "my previous questions", "tell me about my previous",
        "what questions did i ask", "what did i ask", "show me my questions",
        "list my questions", "past questions", "conversation history", "chat history",
    ]
)


class LangGraphOrchestrator:
    """Main orchestrator using LangGraph with a ReAct-style workflow."""

    def __init__(self):
        self.llm_router = LLMRouter()
        self.memory_store = get_memory_store()

        # Agents
        self.chroma_agent = ChromaAgent()
        self.web_agent = WebAgent()
        self.history_agent = HistoryAgent()
        self.general_agent = GeneralAgent()

        self.graph = self._build_graph()

    # ── Graph construction ────────────────────────────────────────────

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(ChatState)

        workflow.add_node("router", self._router_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("final", self._final_node)
        workflow.add_node("save", self._save_node)

        workflow.set_entry_point("router")
        workflow.add_edge("router", "tools")
        workflow.add_edge("tools", "reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_web_search,
            {"web_search": "web_search", "final": "final"},
        )
        workflow.add_edge("web_search", "final")
        workflow.add_edge("final", "save")
        workflow.add_edge("save", END)

        return workflow.compile()

    # ── 1. Router node ────────────────────────────────────────────────

    async def _router_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Single LLM call that determines:
        - Which tools to invoke
        - A short chat-session name

        Follow-up queries are fast-tracked to the history tool.
        """
        raw_query = state.get("query", "")
        query = sanitize_query(raw_query)
        state["query"] = query  # store sanitised version
        query_lower = query.lower().strip()

        # Fast-track: follow-up queries always go to history
        if any(ind in query_lower for ind in _FOLLOW_UP_INDICATORS):
            logger.info("Router: follow-up detected → history tool")
            state["tool_decision"] = {
                "tools": ["history"],
                "primary_tool": "history",
                "reasoning": "Follow-up query detected",
                "confidence": "high",
                "is_follow_up": True,
            }
            state["chat_name"] = "Follow-up Question"
            return state

        # Combined LLM call: tool selection + chat name
        llm = self.llm_router.get_llm()

        combined_prompt = f"""You are an AI assistant for Stevens Institute of Technology.
Analyze the user query and return a JSON object with:
1. Which tools to use
2. A short chat session name (3-8 words)

Available tools:
- "general" – general knowledge, definitions, concepts (NOT Stevens-specific)
- "chroma" – Stevens-specific data (courses, faculty, programs, policies)
- "web" – current / recent information, contact details, updates
- "history" – conversation context, follow-up questions

User Query: "{query}"

Decision Guidelines:
- "general" for: what is, explain, define, concept, theory (non-Stevens)
- "chroma" for: courses, faculty, professors, programs, Stevens-specific info
- "web" for: current info, contact details, recent updates
- "history" for: follow-up questions, references to previous conversation

Return ONLY valid JSON:
{{
  "tools": ["tool1", "tool2"],
  "primary_tool": "main_tool",
  "reasoning": "brief analysis",
  "confidence": "high/medium/low",
  "chat_name": "Short Descriptive Name"
}}"""

        try:
            response = await llm.ainvoke([{"role": "user", "content": combined_prompt}])
            parsed = parse_llm_json(response.content)

            if parsed:
                tools = parsed.get("tools", ["chroma"])
                primary = parsed.get("primary_tool", tools[0] if tools else "chroma")
                valid_tools = {"general", "chroma", "web", "history"}
                tools = [t for t in tools if t in valid_tools] or ["chroma"]

                # Always include history for context
                if "history" not in tools:
                    tools.append("history")

                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": primary if primary in valid_tools else tools[0],
                    "reasoning": parsed.get("reasoning", ""),
                    "confidence": parsed.get("confidence", "medium"),
                    "simple_query": primary == "general" and len(tools) <= 2,
                }
                state["chat_name"] = parsed.get("chat_name", "New Chat")

                logger.info(
                    "Router: tools=%s primary=%s chat_name='%s'",
                    tools, primary, state["chat_name"],
                )
            else:
                # Fallback: rule-based
                tools = self._fallback_tool_selection(query)
                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": tools[0],
                    "reasoning": "Fallback – LLM response unparseable",
                    "confidence": "low",
                }
                state["chat_name"] = "New Chat"

        except Exception as e:
            logger.error("Router LLM error: %s", e, exc_info=True)
            tools = self._fallback_tool_selection(query)
            state["tool_decision"] = {
                "tools": tools,
                "primary_tool": tools[0],
                "reasoning": f"Fallback due to error: {e}",
                "confidence": "low",
            }
            state["chat_name"] = "New Chat"

        return state

    @staticmethod
    def _fallback_tool_selection(query: str) -> List[str]:
        """Rule-based fallback when LLM routing fails."""
        q = query.lower()
        tools = ["history"]

        stevens_keywords = [
            "stevens", "course", "faculty", "professor", "program",
            "admission", "campus", "hoboken", "department",
        ]
        if any(kw in q for kw in stevens_keywords):
            tools.insert(0, "chroma")
        else:
            tools.insert(0, "general")

        return tools

    # ── 2. Tools node ─────────────────────────────────────────────────

    async def _tools_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute selected tools in parallel."""
        decision = state.get("tool_decision", {})
        tools_to_use = decision.get("tools", ["chroma"])

        tasks = []
        tool_names = []

        if "chroma" in tools_to_use:
            tasks.append(self.chroma_agent.process(state.copy()))
            tool_names.append("chroma")
        if "history" in tools_to_use:
            tasks.append(self.history_agent.process(state.copy()))
            tool_names.append("history")
        if "general" in tools_to_use:
            tasks.append(self.general_agent.process(state.copy()))
            tool_names.append("general")

        if tasks:
            logger.info("Tools: executing %s in parallel", tool_names)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(tool_names, results):
                if isinstance(result, Exception):
                    logger.error("Tool %s failed: %s", name, result)
                    state[f"{name}_error"] = str(result)
                elif isinstance(result, dict):
                    # Merge only tool-specific keys to avoid overwriting
                    for key in (
                        "chroma_results", "collections_searched", "chroma_error",
                        "history_results",
                        "general_answer", "used_general_tool", "general_error",
                        "question_type",
                    ):
                        if key in result:
                            state[key] = result[key]

        return state

    # ── 3. Reason node ────────────────────────────────────────────────

    async def _reason_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether web search is needed – rule-based first, LLM fallback."""
        query = state.get("query", "")
        decision = state.get("tool_decision", {})

        # Simple / follow-up queries never need web search
        if decision.get("simple_query") or decision.get("is_follow_up"):
            state["reasoning_result"] = {
                "need_web_search": False,
                "reasoning": "Simple or follow-up query",
            }
            return state

        # If the router already selected "web", honour it
        if "web" in decision.get("tools", []):
            state["reasoning_result"] = {"need_web_search": True, "reasoning": "Router selected web tool"}
            web_query = await self._generate_web_search_query(query, state)
            state["web_search_query"] = web_query
            return state

        # Rule-based heuristic: check for time-sensitive indicators
        q_lower = query.lower()
        time_indicators = [
            "current", "recent", "latest", "2024", "2025", "2026",
            "upcoming", "deadline", "application", "admission",
            "enrollment", "registration", "semester", "contact",
            "email", "phone", "address", "schedule",
        ]
        if any(ind in q_lower for ind in time_indicators):
            logger.info("Reason: time-sensitive indicator detected → web search")
            state["reasoning_result"] = {
                "need_web_search": True,
                "reasoning": "Time-sensitive query detected",
            }
            web_query = await self._generate_web_search_query(query, state)
            state["web_search_query"] = web_query
            return state

        # Check if chroma returned enough good data
        chroma = state.get("chroma_results", {})
        docs = chroma.get("documents", [])
        if docs and len(docs) >= 2:
            state["reasoning_result"] = {
                "need_web_search": False,
                "reasoning": f"Sufficient vector-DB results ({len(docs)} docs)",
            }
            return state

        # Fallback: if we have very little data, do web search
        if not docs:
            state["reasoning_result"] = {
                "need_web_search": True,
                "reasoning": "No vector-DB results – web search as fallback",
            }
            web_query = await self._generate_web_search_query(query, state)
            state["web_search_query"] = web_query
            return state

        # Default: no web search
        state["reasoning_result"] = {
            "need_web_search": False,
            "reasoning": "Default – available data should suffice",
        }
        return state

    async def _generate_web_search_query(
        self, original_query: str, state: Dict[str, Any]
    ) -> str:
        """Generate a targeted web search query."""
        llm = self.llm_router.get_llm()

        prompt = (
            "Generate a specific web search query to find information about "
            "Stevens Institute of Technology related to the following user question.\n\n"
            f'User Question: "{sanitize_query(original_query)}"\n\n'
            "Return ONLY the search query (3-10 words). Include 'Stevens Institute of Technology' if relevant."
        )

        try:
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            query = response.content.strip().strip('"').strip("'")
            if len(query) < 5:
                raise ValueError("Generated query too short")
            return query
        except Exception:
            return f"{original_query} Stevens Institute of Technology"

    @staticmethod
    def _should_web_search(state: Dict[str, Any]) -> str:
        result = state.get("reasoning_result", {})
        return "web_search" if result.get("need_web_search") else "final"

    # ── 4. Web search node ────────────────────────────────────────────

    async def _web_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        original_query = state.get("query", "")
        search_query = state.get("web_search_query", original_query)

        logger.info("Web search: '%s'", search_query)

        try:
            web_state = state.copy()
            web_state["query"] = search_query
            web_results = await self.web_agent.process(web_state)

            if web_results.get("web_results"):
                web_results["web_results"]["original_query"] = original_query
                web_results["web_results"]["search_query_used"] = search_query
                state["web_results"] = web_results["web_results"]
            else:
                state["web_results"] = {"success": False, "web_content": ""}

        except Exception as e:
            logger.error("Web search error: %s", e, exc_info=True)
            state["web_results"] = {"success": False, "error": str(e), "web_content": ""}

        return state

    # ── 5. Final answer node ──────────────────────────────────────────

    async def _final_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        decision = state.get("tool_decision", {})
        history_results = state.get("history_results", {})
        is_follow_up = history_results.get("is_follow_up", False)

        llm = self.llm_router.get_llm()

        # ── Build context from all tools ──
        context_parts = []

        # Chroma results
        chroma = state.get("chroma_results", {})
        if chroma.get("documents"):
            context_parts.append("=== Database Information ===")
            for i, doc in enumerate(chroma["documents"][:5], 1):
                context_parts.append(f"[{i}]: {doc['content']}")

        # Web results
        web = state.get("web_results", {})
        web_content = web.get("scraped_content") or web.get("web_content", "")
        if web_content:
            context_parts.append("=== Web Search Results ===")
            context_parts.append(web_content[:2000])

        # General knowledge
        general = state.get("general_answer")
        if general:
            context_parts.append("=== General Knowledge ===")
            context_parts.append(general[:1000])

        # Conversation history
        history_text = ""
        if history_results.get("relevant_history"):
            history_text = "\n=== Conversation History ===\n"
            for i, entry in enumerate(history_results["relevant_history"], 1):
                history_text += f"Q{i}: {entry.get('query', '')}\n"
                history_text += f"A{i}: {entry.get('response', '')}\n\n"

        context = "\n\n".join(context_parts) if context_parts else "No specific information available."

        # ── Construct the final prompt ──
        history_instruction = ""
        if history_results.get("relevant_history"):
            count = len(history_results["relevant_history"])
            history_instruction = (
                f"\nYou have access to {count} previous conversation(s). "
                "NEVER claim you lack access to history. "
                "Use the conversation history to provide context-aware answers. "
                "For follow-up queries like 'try again' or 'repeat', reference previous Q&A.\n"
            )

        safe_query = sanitize_query(query)

        final_prompt = f"""You are a helpful academic advisor for Stevens Institute of Technology.

Current User Question: "{safe_query}"

Available Information:
{context}
{history_text}
{history_instruction}

INSTRUCTIONS:
1. Provide a complete, helpful answer using all available information.
2. Include specific details, dates, or requirements when available.
3. If information is partial, state what you know and suggest where to find more.
4. Be conversational and actionable – don't just redirect to websites.
5. For follow-up questions, use conversation history directly.
6. NEVER include reasoning, internal thoughts, or meta-commentary.

Answer:"""

        try:
            response = await llm.ainvoke([{"role": "user", "content": final_prompt}])
            state["answer"] = clean_response(response.content.strip())
            logger.info("Final answer: %d characters", len(state["answer"]))
        except Exception as e:
            logger.error("Final answer error: %s", e, exc_info=True)
            state["answer"] = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again."
            )

        return state

    # ── 6. Save node ──────────────────────────────────────────────────

    async def _save_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_id = state.get("user_id", "default")
        query = state.get("query", "")
        answer = state.get("answer", "")

        await self.memory_store.save_conversation(
            user_id=user_id,
            query=query,
            response=answer,
            metadata={
                "tools_used": state.get("tool_decision", {}).get("tools", []),
                "collections_searched": state.get("collections_searched", []),
                "web_search_performed": bool(state.get("web_results")),
                "used_general_tool": state.get("used_general_tool", False),
            },
        )
        return state

    # ── Public API ────────────────────────────────────────────────────

    async def process_query(
        self, query: str, user_id: str = "default", chat_history: str = ""
    ) -> Dict[str, Any]:
        initial_state = {
            "query": query,
            "user_id": user_id,
            "chat_history": chat_history,
        }

        try:
            logger.info("Processing query: '%s'", query[:100])
            final_state = await self.graph.ainvoke(initial_state)

            answer = final_state.get("answer", "")
            return {
                "success": True,
                "answer": answer,
                "metadata": {
                    "tools_used": final_state.get("tool_decision", {}).get("tools", []),
                    "collections_searched": final_state.get("collections_searched", []),
                    "web_search_performed": bool(final_state.get("web_results")),
                    "used_general_tool": final_state.get("used_general_tool", False),
                    "reasoning_result": final_state.get("reasoning_result", {}),
                    "chat_name": final_state.get("chat_name", "New Chat"),
                },
            }

        except Exception as e:
            logger.error("Query processing error: %s", e, exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "answer": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            }
