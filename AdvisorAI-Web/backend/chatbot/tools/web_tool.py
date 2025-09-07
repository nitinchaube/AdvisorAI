import asyncio
import aiohttp
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from config.settings import settings
import sys
import os

# Add the parent directory to sys.path to import existing web_scrapper
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from web_scrapper import scrape_web_content, duckduckgo_search_urls, serpapi_search_urls
except ImportError:
    # Fallback if web_scrapper is not available
    print("Warning: web_scrapper module not found. Web search functionality will be limited.")
    scrape_web_content = None
    duckduckgo_search_urls = None
    serpapi_search_urls = None

class WebTool:
    """Tool for web search and content scraping using RAG service logic"""

    def __init__(self):
        self.search_enabled = settings.WEB_SEARCH_ENABLED
        self.max_results = settings.WEB_SEARCH_RESULTS

    def _enhance_query_with_stevens(self, query: str) -> str:
        """Enhance query by appending Stevens Institute of Technology context"""
        # Don't duplicate if already contains Stevens
        if "stevens" in query.lower():
            print(f"Web query already contains Stevens context: '{query}'")
            return query
    
        # Add Stevens Institute of Technology to the query
        enhanced_query = f"{query} Stevens Institute of Technology"
        
        print(f"Enhanced web query: '{query}' -> '{enhanced_query}'")
        return enhanced_query

    def _should_use_web_search(self, query: str, chroma_results: Dict = None) -> bool:
        """Smart decision on whether to use web search based on RAG service logic"""
        
        query_lower = query.lower()
        
        # Always use web search for current/recent information queries
        current_time_indicators = [
            "current", "recent", "latest", "now", "today", "this year", "2024", "2025",
            "upcoming", "next", "future", "new", "announcement", "update", "when", "deadline",
            "application", "admission", "enrollment", "registration", "semester", "term"
        ]
        
        if any(indicator in query_lower for indicator in current_time_indicators):
            print(f"Web search triggered: Query contains time indicator")
            return True
        
        # If we have good documents from Chroma, don't web search (but be less strict)
        if chroma_results and chroma_results.get("documents"):
            docs = chroma_results["documents"]
            # Check if any document has very good similarity score (more strict threshold)
            very_good_docs = [doc for doc in docs if doc.get("score", 1.0) < 0.6]
            if very_good_docs:
                print(f"No web search: Found very good documents (score < 0.6)")
                return False
            else:
                # If we have documents but they're not very good, still consider web search
                print(f"Web search considered: Documents found but similarity scores not very good")
                return True
        
        # If no documents found, definitely use web search
        if not chroma_results or not chroma_results.get("documents"):
            print(f"Web search triggered: No documents found")
            return True
        
        # Default to web search for better coverage
        print(f"Web search triggered: Default case for better coverage")
        return True

    async def search_web(self, query: str, chroma_results: Dict = None) -> Dict[str, Any]:
        """Search the web using RAG service logic with enhanced query"""
        if not self.search_enabled:
            return {"error": "Web search is disabled"}

        if not scrape_web_content:
            return {"error": "Web scraper not available"}

        # Check if we should use web search
        if not self._should_use_web_search(query, chroma_results):
            return {
                "results": [],
                "content": "",
                "query": query,
                "total_results": 0,
                "skipped": True,
                "reason": "Sufficient information available from vector database"
            }

        try:
            # Enhance query with Stevens Institute of Technology
            enhanced_query = self._enhance_query_with_stevens(query)
            
            # Use existing web scraper function with RAG service approach
            web_content = scrape_web_content(enhanced_query, self.max_results)
            
            # Extract content and URLs
            content = web_content.get("content", "")
            urls = web_content.get("urls", [])
            
            # Clean and format content for better use
            if content:
                # Remove excessive whitespace and format
                content = re.sub(r'\s+', ' ', content).strip()
                # Limit content length for processing
                content = content[:2000] if len(content) > 2000 else content

            return {
                "results": urls,
                "content": content,
                "query": enhanced_query,
                "original_query": query,
                "total_results": len(urls),
                "skipped": False,
                "web_search_performed": True
            }

        except Exception as e:
            return {"error": f"Web search failed: {str(e)}"}

    async def search_and_scrape(self, query: str, chroma_results: Dict = None) -> Dict[str, Any]:
        """Search web and scrape content from top results using improved RAG service logic"""
        if not scrape_web_content:
            return {
                "error": "Web scraper not available",
                "success": False
            }

        # Check if we should use web search
        if not self._should_use_web_search(query, chroma_results):
            return {
                "search_results": [],
                "scraped_content": "",
                "query": query,
                "success": True,
                "skipped": True,
                "reason": "Sufficient information available from vector database"
            }

        try:
            # Enhance query with Stevens Institute of Technology
            enhanced_query = self._enhance_query_with_stevens(query)
            
            print(f"🔍 WEB: Searching for: {enhanced_query}")
            
            # Use existing web scraper function with RAG service approach
            web_content = scrape_web_content(enhanced_query, self.max_results)
            
            # Handle the response properly - scrape_web_content returns a string
            if isinstance(web_content, str):
                content = web_content
                urls = []  # URLs not available in string format
            else:
                content = str(web_content)
                urls = []
            
            # Clean and format content for better use
            if content and len(content.strip()) > 100:  # Ensure we have meaningful content
                # Remove excessive whitespace and format
                content = re.sub(r'\s+', ' ', content).strip()
                # Remove HTML tags if any
                content = re.sub(r'<[^>]+>', '', content)
                # Remove JSON-like artifacts and special characters that might interfere
                content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', content)
                # Remove any remaining JSON artifacts
                content = re.sub(r'Source:\s*https?://[^\s]+\s*', '', content)
                content = re.sub(r'---\s*', ' ', content)
                # Clean up multiple spaces
                content = re.sub(r'\s+', ' ', content).strip()
                # Limit content length for processing but keep more content
                content = content[:5000] if len(content) > 5000 else content
                
                print(f"WEB: Successfully extracted {len(content)} characters of web content")
                print(f"WEB: Content preview: {content[:200]}...")
            else:
                print(f"WEB: No meaningful web content extracted (length: {len(content) if content else 0})")
                content = "No relevant web content found for this query."

            return {
                "search_results": urls,
                "scraped_content": content,
                "web_content": content,  # Add both keys for compatibility
                "query": enhanced_query,
                "original_query": query,
                "success": True,
                "skipped": False,
                "web_search_performed": True
            }

        except Exception as e:
            print(f"WEB: Error in web search and scrape: {str(e)}")
            return {
                "error": f"Web search and scrape failed: {str(e)}",
                "success": False
            }

    async def duckduckgo_search(self, query: str) -> Dict[str, Any]:
        """Use DuckDuckGo search directly with enhanced query"""
        if not duckduckgo_search_urls:
            return {"error": "DuckDuckGo search not available"}

        try:
            enhanced_query = self._enhance_query_with_stevens(query)
            urls = duckduckgo_search_urls(enhanced_query, self.max_results)
            return {
                "urls": urls,
                "query": enhanced_query,
                "original_query": query,
                "source": "duckduckgo"
            }
        except Exception as e:
            return {"error": f"DuckDuckGo search failed: {str(e)}"}

    async def serpapi_search(self, query: str) -> Dict[str, Any]:
        """Use SerpAPI search directly with enhanced query"""
        if not serpapi_search_urls:
            return {"error": "SerpAPI search not available"}

        try:
            enhanced_query = self._enhance_query_with_stevens(query)
            urls = serpapi_search_urls(enhanced_query, self.max_results)
            return {
                "urls": urls,
                "query": enhanced_query,
                "original_query": query,
                "source": "serpapi"
            }
        except Exception as e:
            return {"error": f"SerpAPI search failed: {str(e)}"} 