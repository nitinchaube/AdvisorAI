from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from config.settings import settings

class LLMRouter:
    """Router for different LLM providers with fallback logic"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        print(f"🔧 LLM Router initialized with provider: {self.provider}")
        self._validate_provider()

    def _validate_provider(self):
        """Validate that the required API keys are available"""
        if self.provider == "openai" and not settings.OPENAI_API_KEY:
            print("⚠️  Warning: OpenAI API key not found, falling back to available providers")
            self._try_fallback_provider()
        elif self.provider == "gemini" and not settings.GEMINI_API_KEY:
            print("⚠️  Warning: Gemini API key not found, falling back to available providers")
            self._try_fallback_provider()
        elif self.provider == "claude" and not settings.ANTHROPIC_API_KEY:
            print("⚠️  Warning: Anthropic API key not found, falling back to available providers")
            self._try_fallback_provider()

    def _try_fallback_provider(self):
        """Try to find an available provider"""
        fallback_providers = ["openai", "gemini", "claude"]

        for provider in fallback_providers:
            if provider != self.provider:
                try:
                    if provider == "openai" and settings.OPENAI_API_KEY:
                        self.provider = provider
                        print(f"🔄 Switched to {provider} provider")
                        return
                    elif provider == "gemini" and settings.GEMINI_API_KEY:
                        self.provider = provider
                        print(f"🔄 Switched to {provider} provider")
                        return
                    elif provider == "claude" and settings.ANTHROPIC_API_KEY:
                        self.provider = provider
                        print(f"🔄 Switched to {provider} provider")
                        return
                except Exception:
                    continue

        # If no provider is available, use a mock provider for testing
        print("⚠️  No API keys available, using mock provider for testing")
        self.provider = "mock"

    def get_llm(self, streaming: bool = False, callbacks: list = None, **kwargs) -> Any:
        """Get LLM instance based on provider configuration"""
        print(f"🤖 Getting LLM instance for provider: {self.provider}")

        if self.provider == "openai":
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                streaming=streaming,
                callbacks=callbacks or [],
                **kwargs
            )
        elif self.provider == "gemini":
            # Remove streaming parameter for Gemini as it doesn't support it the same way
            gemini_kwargs = {k: v for k, v in kwargs.items() if k != 'streaming'}
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                callbacks=callbacks or [],
                **gemini_kwargs
            )
        elif self.provider == "claude":
            return ChatAnthropic(
                model=settings.CLAUDE_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                streaming=streaming,
                callbacks=callbacks or [],
                **kwargs
            )
        elif self.provider == "mock":
            # Mock LLM for testing without API keys
            class MockLLM:
                def __init__(self):
                    self.model_name = "mock-model"

                async def ainvoke(self, messages):
                    class MockResponse:
                        def __init__(self, content):
                            self.content = content

                    # Simple mock response based on the query
                    query = messages[0]["content"] if messages else ""
                    if "computer science" in query.lower():
                        return MockResponse("Computer Science courses at Stevens Institute of Technology include programming, algorithms, data structures, and software engineering.")
                    elif "machine learning" in query.lower():
                        return MockResponse("Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.")
                    elif "admission" in query.lower():
                        return MockResponse("For current admission requirements, please visit the Stevens Institute of Technology website or contact the admissions office.")
                    else:
                        return MockResponse("I can help you with information about Stevens Institute of Technology. Please ask me about courses, faculty, admission requirements, or general academic topics.")

                def invoke(self, prompt):
                    return self.ainvoke([{"role": "user", "content": prompt}])

            return MockLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def get_fallback_llm(self) -> Any:
        """Get a fallback LLM if the primary one fails"""
        fallback_providers = ["openai", "gemini", "claude"]

        for provider in fallback_providers:
            if provider != self.provider:
                try:
                    if provider == "openai" and settings.OPENAI_API_KEY:
                        return ChatOpenAI(
                            model=settings.OPENAI_MODEL,
                            openai_api_key=settings.OPENAI_API_KEY
                        )
                    elif provider == "gemini" and settings.GEMINI_API_KEY:
                        return ChatGoogleGenerativeAI(
                            model=settings.GEMINI_MODEL,
                            google_api_key=settings.GEMINI_API_KEY
                        )
                    elif provider == "claude" and settings.ANTHROPIC_API_KEY:
                        return ChatAnthropic(
                            model=settings.CLAUDE_MODEL,
                            anthropic_api_key=settings.ANTHROPIC_API_KEY
                        )
                except Exception:
                    continue

        raise RuntimeError("No fallback LLM available") 