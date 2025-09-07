import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")  # Changed from GOOGLE_API_KEY
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Model Configuration
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")

    # Vector Database Configuration
    VECTORDB_DIR: str = os.getenv("VECTORDB_DIR", "/Users/nitinchaube/Studies/IMPS/ALLAboutAI/Project/AdvisorAI/AdvisorAI/AdvisorAI-Web/backend/VectorDB")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Retrieval Configuration
    TOP_K_PER_COLLECTION: int = int(os.getenv("TOP_K_PER_COLLECTION", "5"))
    MAX_TOTAL_DOCS: int = int(os.getenv("MAX_TOTAL_DOCS", "5"))

    # Web Search Configuration
    WEB_SEARCH_ENABLED: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    WEB_SEARCH_RESULTS: int = int(os.getenv("WEB_SEARCH_RESULTS", "3"))

    # Memory Configuration
    MEMORY_TYPE: str = os.getenv("MEMORY_TYPE", "in_memory")  # in_memory, redis, postgres
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Concurrency Configuration
    MAX_CONCURRENT_TOOLS: int = int(os.getenv("MAX_CONCURRENT_TOOLS", "3"))

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment

settings = Settings() 