"""LLM provider router with automatic fallback logic."""

import logging
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from config.settings import settings

logger = logging.getLogger("chatbot")

# Provider → (API-key attr, LLM factory)
_PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


class LLMRouter:
    """Router for different LLM providers with fallback logic."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._validate_provider()
        logger.info("LLM Router initialised with provider: %s", self.provider)

    # ------------------------------------------------------------------
    # Validation & fallback
    # ------------------------------------------------------------------

    def _validate_provider(self):
        """Ensure the configured provider has a valid API key; fall back otherwise."""
        key_attr = _PROVIDER_KEY_MAP.get(self.provider)
        if key_attr and not getattr(settings, key_attr, ""):
            logger.warning(
                "%s API key missing – attempting fallback", self.provider
            )
            self._try_fallback_provider()

    def _try_fallback_provider(self):
        for provider, key_attr in _PROVIDER_KEY_MAP.items():
            if provider != self.provider and getattr(settings, key_attr, ""):
                self.provider = provider
                logger.info("Switched to fallback provider: %s", provider)
                return
        logger.error("No LLM API keys available")
        raise RuntimeError(
            "No LLM API keys configured. Set at least one of "
            "OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY."
        )

    # ------------------------------------------------------------------
    # LLM instantiation
    # ------------------------------------------------------------------

    def get_llm(
        self,
        streaming: bool = False,
        callbacks: Optional[list] = None,
        **kwargs,
    ) -> Any:
        """Return an LLM instance for the active provider."""
        cb = callbacks or []

        if self.provider == "openai":
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                streaming=streaming,
                callbacks=cb,
                **kwargs,
            )

        if self.provider == "gemini":
            gemini_kwargs = {k: v for k, v in kwargs.items() if k != "streaming"}
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                callbacks=cb,
                **gemini_kwargs,
            )

        if self.provider == "claude":
            return ChatAnthropic(
                model=settings.CLAUDE_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                streaming=streaming,
                callbacks=cb,
                **kwargs,
            )

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def get_fallback_llm(self) -> Any:
        """Return an LLM from a different provider (for retry scenarios)."""
        for provider, key_attr in _PROVIDER_KEY_MAP.items():
            if provider != self.provider and getattr(settings, key_attr, ""):
                if provider == "openai":
                    return ChatOpenAI(
                        model=settings.OPENAI_MODEL,
                        openai_api_key=settings.OPENAI_API_KEY,
                    )
                if provider == "gemini":
                    return ChatGoogleGenerativeAI(
                        model=settings.GEMINI_MODEL,
                        google_api_key=settings.GEMINI_API_KEY,
                    )
                if provider == "claude":
                    return ChatAnthropic(
                        model=settings.CLAUDE_MODEL,
                        anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    )
        raise RuntimeError("No fallback LLM available")
