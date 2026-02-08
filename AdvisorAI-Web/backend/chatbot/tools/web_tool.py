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


class WebTool:
    """Search the web and scrape content from top results."""

    def __init__(self):
        self.search_enabled = settings.WEB_SEARCH_ENABLED
        self.max_results = settings.WEB_SEARCH_RESULTS

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

            content = self._clean_content(content)

            if len(content) < 100:
                logger.debug("Web search returned insufficient content")
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
    def _clean_content(text: str) -> str:
        """Normalise and truncate scraped web content."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
        text = re.sub(r"Source:\s*https?://\S+\s*", "", text)
        text = re.sub(r"---\s*", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:5000]
