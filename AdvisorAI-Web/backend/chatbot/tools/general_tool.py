"""General-knowledge tool – answers questions via the LLM directly."""

import logging
from typing import Dict, Any

from core.llm_router import LLMRouter
from core.utils import sanitize_query

logger = logging.getLogger("chatbot")


class GeneralTool:
    """Answers general-knowledge questions that don't need vector DB or web search."""

    def __init__(self):
        self.llm_router = LLMRouter()

    async def answer_general_question(
        self, query: str, context: str = ""
    ) -> Dict[str, Any]:
        """Generate a direct LLM answer for a general question."""
        safe_query = sanitize_query(query)
        try:
            llm = self.llm_router.get_llm()

            prompt = (
                "You are **AdvisorAI**, a friendly and knowledgeable academic advisor "
                "built exclusively for Stevens Institute of Technology.\n\n"
                "IDENTITY: Your name is AdvisorAI. You are NOT OpenAI, ChatGPT, GPT, "
                "Gemini, Google, Claude, or any other AI product. Never mention or "
                "reveal the underlying model or API. If asked about your identity, "
                "say: 'I'm AdvisorAI, your academic advisor for Stevens.'\n\n"
                f"Question: {safe_query}\n\n"
                + (f"Context: {context}\n\n" if context else "")
                + "Instructions:\n"
                "1. Provide a clear, accurate, and helpful answer.\n"
                "2. If the question is about Stevens, use specific information.\n"
                "3. Be concise but thorough.\n"
                "4. If you don't know, say so clearly and offer to help with other questions.\n"
                "5. Never fabricate facts.\n"
                "6. NEVER tell the student to 'visit the website' or 'check stevens.edu' — you are their resource.\n"
                "7. NEVER say 'as an AI language model' — say 'as your academic advisor' instead.\n\n"
                "Answer:"
            )

            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            logger.debug("GeneralTool answered query successfully")

            return {
                "answer": response.content,
                "query": safe_query,
                "tool": "general",
                "success": True,
            }

        except Exception as e:
            logger.error("GeneralTool error: %s", e, exc_info=True)
            return {"error": f"General tool failed: {e}", "success": False}
