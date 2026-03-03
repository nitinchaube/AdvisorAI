"""Web search & scrape tool – leverages the existing web_scrapper module."""

import logging
import os
import re
import sys
from typing import Dict, Any

from config.settings import settings

logger = logging.getLogger("chatbot")

# Import the legacy web scraper from the backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from web_scrapper import scrape_web_content, duckduckgo_search_urls, serpapi_search_urls
except ImportError:
    logger.warning("web_scrapper module not found – web search will be unavailable")
    scrape_web_content = None
    duckduckgo_search_urls = None
    serpapi_search_urls = None

# Patterns that indicate non-informational noise in scraped pages.
_NOISE_PATTERNS = re.compile(
    r"(?i)"
    r"cookie\s*(?:policy|consent|settings|preferences)|"
    r"privacy\s*(?:policy|notice|statement)|"
    r"terms\s*(?:of\s*(?:use|service))|"
    r"accept\s*(?:all\s*)?cookies|"
    r"sign\s*(?:in|up)\s*(?:to|with|for)|"
    r"subscribe\s*(?:to\s*our|now)|"
    r"follow\s*us\s*on|"
    r"share\s*(?:on|this)|"
    r"©\s*\d{4}|"
    r"all\s*rights\s*reserved|"
    r"skip\s*to\s*(?:main\s*)?content|"
    r"toggle\s*(?:navigation|menu)|"
    r"breadcrumb|"
    r"back\s*to\s*top"
)


class WebTool:
    """Search the web and scrape content from top results."""

    def __init__(self):
        self.search_enabled = settings.WEB_SEARCH_ENABLED
        self.max_results = settings.WEB_SEARCH_RESULTS
        self.max_content_chars = settings.WEB_CONTENT_MAX_CHARS

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _enhance_query(query: str) -> str:
        """Append Stevens Institute context if not already present."""
        if "stevens" in query.lower():
            return query
        return f"{query} Stevens Institute of Technology"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_and_scrape(
        self, query: str, chroma_results: Dict = None
    ) -> Dict[str, Any]:
        """Search the web and return scraped content."""
        if not self.search_enabled or scrape_web_content is None:
            return {
                "success": False,
                "error": "Web search is disabled or unavailable",
                "web_content": "",
                "scraped_content": "",
            }

        try:
            enhanced = self._enhance_query(query)
            logger.debug("Web search: %s", enhanced)

            raw = scrape_web_content(enhanced, self.max_results)

            # scrape_web_content may return str or dict
            if isinstance(raw, str):
                content = raw
                urls = []
            elif isinstance(raw, dict):
                content = raw.get("content", "")
                urls = raw.get("urls", [])
            else:
                content = str(raw)
                urls = []

            content = self._clean_content(content, self.max_content_chars)

            if len(content) < 50:
                logger.debug("Web search returned very short content (%d chars)", len(content))
                content = ""

            return {
                "search_results": urls,
                "scraped_content": content,
                "web_content": content,
                "query": enhanced,
                "original_query": query,
                "success": bool(content),
                "skipped": False,
                "web_search_performed": True,
            }

        except Exception as e:
            logger.error("WebTool error: %s", e, exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "web_content": "",
                "scraped_content": "",
            }

    # ------------------------------------------------------------------
    # Content cleaning
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_content(text: str, max_chars: int = 3000) -> str:
        """Clean, de-noise, and truncate scraped web content."""
        if not text:
            return ""

        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"Source:\s*https?://\S+\s*", "", text)
        text = re.sub(r"---\s*", " ", text)

        # Remove noisy boilerplate lines
        lines = text.split("\n")
        cleaned: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if len(stripped) < 4:
                continue
            if _NOISE_PATTERNS.search(stripped):
                continue
            cleaned.append(stripped)

        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text[:max_chars].strip()
