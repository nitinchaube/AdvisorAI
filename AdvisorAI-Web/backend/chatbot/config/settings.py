import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Centralized configuration for the chatbot subsystem."""

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Model Configuration
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")

    # Vector Database Configuration
    VECTORDB_DIR: str = os.getenv("VECTORDB_DIR", "./VectorDB")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Retrieval Configuration
    TOP_K_PER_COLLECTION: int = int(os.getenv("TOP_K_PER_COLLECTION", "3"))
    MAX_TOTAL_DOCS: int = int(os.getenv("MAX_TOTAL_DOCS", "3"))

    # Web Search Configuration
    WEB_SEARCH_ENABLED: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    WEB_SEARCH_RESULTS: int = int(os.getenv("WEB_SEARCH_RESULTS", "3"))

    # Memory Configuration
    MEMORY_TYPE: str = os.getenv("MEMORY_TYPE", "in_memory")

    # Concurrency Configuration
    MAX_CONCURRENT_TOOLS: int = int(os.getenv("MAX_CONCURRENT_TOOLS", "3"))

    # Input Sanitization
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
