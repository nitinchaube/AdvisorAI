import os
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, quote_plus
import time
import random
import json

logger = logging.getLogger(__name__)


def _normalise_url(raw: str) -> str:
    """URL-decode and strip tracking query params so duplicates are caught."""
    url = unquote(raw).split("&")[0]   # remove trailing DDG params like &rut=…
    url = url.rstrip("/")
    return url


def _dedup_urls(urls, num_results=5):
    """Deduplicate URLs by domain + path."""
    seen = set()
    unique = []
    for url in urls:
        parsed = urlparse(url)
        key = f"{parsed.netloc}{parsed.path}".rstrip("/")
        if key not in seen:
            seen.add(key)
            unique.append(url)
            if len(unique) >= num_results:
                break
    return unique


def duckduckgo_search_urls(query, num_results=5):
    """Perform a DuckDuckGo search and return unique top result URLs.
    
    Tries multiple strategies:
    1. DuckDuckGo lite endpoint (most reliable for scraping)
    2. DuckDuckGo HTML endpoint (classic)
    3. DuckDuckGo JSON API (instant answers)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/",
    }

    links = []

    # Strategy 1: DuckDuckGo Lite (simpler HTML, harder to block)
    try:
        resp = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for a_tag in soup.find_all("a", class_="result-link"):
            href = a_tag.get("href", "")
            if href and href.startswith("http") and "duckduckgo.com" not in href:
                links.append(_normalise_url(href))

        # Also try plain links in the lite page
        if not links:
            for a_tag in soup.find_all("a"):
                href = a_tag.get("href", "")
                if href.startswith("http") and "duckduckgo.com" not in href:
                    links.append(_normalise_url(href))

        links = _dedup_urls(links, num_results)
        if links:
            logger.info(f"Found {len(links)} URLs from DuckDuckGo Lite: {links}")
            return links
    except Exception as e:
        logger.warning(f"DuckDuckGo Lite failed: {e}")

    # Strategy 2: DuckDuckGo HTML endpoint (classic)
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.select(".result__a"):
            href = result.get("href", "")
            if "/l/?uddg=" in href:
                raw = href.split("/l/?uddg=")[1]
                url = _normalise_url(raw)
            elif href.startswith("http"):
                url = _normalise_url(href)
            else:
                continue
            if url and "duckduckgo.com" not in url:
                links.append(url)

        # Fallback: any outbound links
        if not links:
            for a_tag in soup.select("a[href*='http']"):
                href = a_tag.get("href", "")
                url = _normalise_url(href)
                if url and "duckduckgo.com" not in url:
                    links.append(url)

        links = _dedup_urls(links, num_results)
        if links:
            logger.info(f"Found {len(links)} URLs from DuckDuckGo HTML: {links}")
            return links
        else:
            logger.warning("DuckDuckGo HTML returned 0 results (possible rate limit / CAPTCHA)")
    except Exception as e:
        logger.warning(f"DuckDuckGo HTML failed: {e}")

    # Strategy 3: DuckDuckGo JSON API (instant answers — limited but reliable)
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": "1"},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract URLs from related topics and results
        for topic in data.get("RelatedTopics", []):
            url = topic.get("FirstURL", "")
            if url and url.startswith("http") and "duckduckgo.com" not in url:
                links.append(_normalise_url(url))
            # Nested topics
            for sub in topic.get("Topics", []):
                url = sub.get("FirstURL", "")
                if url and url.startswith("http") and "duckduckgo.com" not in url:
                    links.append(_normalise_url(url))

        # Abstract URL
        abstract_url = data.get("AbstractURL", "")
        if abstract_url and abstract_url.startswith("http"):
            links.insert(0, _normalise_url(abstract_url))

        links = _dedup_urls(links, num_results)
        if links:
            logger.info(f"Found {len(links)} URLs from DuckDuckGo API: {links}")
            return links
    except Exception as e:
        logger.warning(f"DuckDuckGo API failed: {e}")

    logger.warning(f"All DuckDuckGo strategies failed for query: {query[:80]}")
    return []


def serpapi_search_urls(query, num_results=3, api_key=None):
    """Use SerpAPI to get Google search results as a backup."""
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key.startswith("your_") or api_key == "CHANGE_ME":
        logger.info("No SerpAPI key available. Set SERPAPI_API_KEY in your .env file.")
        return []
    try:
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": num_results,
            "gl": "us",
            "hl": "en"
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        seen = set()
        links = []
        for result in data.get("organic_results", []):
            url = result.get("link", "")
            if not url:
                continue
            parsed = urlparse(url)
            key = f"{parsed.netloc}{parsed.path}".rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            links.append(url)
            if len(links) >= num_results:
                break
        logger.info(f"Found {len(links)} unique URLs from SerpAPI (Google): {links}")
        return links
    except Exception as e:
        logger.error(f"Error in SerpAPI search: {e}")
        return []


def google_scrape_urls(query, num_results=5):
    """Last-resort: scrape Google search results directly."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": num_results + 2},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Google wraps URLs in /url?q=...
            if href.startswith("/url?q="):
                url = href.split("/url?q=")[1].split("&")[0]
                url = unquote(url)
                if url.startswith("http") and "google.com" not in url:
                    links.append(url)

        links = _dedup_urls(links, num_results)
        if links:
            logger.info(f"Found {len(links)} URLs from Google scrape: {links}")
        return links
    except Exception as e:
        logger.warning(f"Google scrape failed: {e}")
        return []


def clean_html(html):
    """Remove scripts/styles and extract visible text."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript", "iframe"]):
        tag.decompose()
    
    # Remove elements with common ad classes
    for tag in soup.find_all(class_=lambda x: x and any(word in x.lower() for word in 
        ['ad', 'ads', 'advertisement', 'banner', 'popup', 'modal', 'cookie'])):
        tag.decompose()
    
    # Extract text from paragraphs and headings
    text_elements = []
    
    # Get headings
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if text and len(text) > 10:
            text_elements.append(text)
    
    # Get paragraphs
    for tag in soup.find_all('p'):
        text = tag.get_text(strip=True)
        if text and len(text) > 20:
            text_elements.append(text)
    
    # Get list items (often contain useful info)
    for tag in soup.find_all('li'):
        text = tag.get_text(strip=True)
        if text and len(text) > 30:
            text_elements.append(text)
    
    # Combine text
    combined_text = " ".join(text_elements)
    return " ".join(combined_text.split())  # Clean whitespace


def scrape_top3(query, num_results=5, api_key=None):
    """Search and fetch top URLs, return their cleaned text."""
    
    logger.info(f"Searching for: {query}")
    
    # Try DuckDuckGo first (multiple strategies built in)
    urls = duckduckgo_search_urls(query, num_results)

    # Fallback to SerpAPI
    if not urls:
        logger.info("DuckDuckGo failed, trying SerpAPI (Google)...")
        urls = serpapi_search_urls(query, num_results, api_key=api_key)

    # Last resort: direct Google scrape
    if not urls:
        logger.info("SerpAPI unavailable, trying direct Google scrape...")
        urls = google_scrape_urls(query, num_results)
    
    if not urls:
        logger.warning("No URLs found from any search engine")
        return []

    logger.info(f"Scraping {len(urls)} URLs: {urls}")
    
    results = []
    for i, url in enumerate(urls, 1):
        try:
            logger.info(f"Fetching content from {i}/{len(urls)}: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36"
            }
            
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            
            text = clean_html(resp.text)
            if text:
                results.append({"url": url, "content": text[:3000]})
                logger.info(f"Successfully extracted {len(text)} characters")
            else:
                results.append({"url": url, "content": "No text content found"})
                logger.info("No text content found")
            
            # Random delay between requests
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            results.append({"url": url, "content": f"Failed to fetch: {e}"})
    
    return results


def scrape_web_content(query, num_results=5, api_key=None):
    """
    Scrape web content for a query.

    Returns:
        dict with keys:
          - content (str): combined text from all sources
          - urls (list[str]): the URLs that were successfully scraped
    """
    results = scrape_top3(query, num_results=num_results, api_key=api_key)

    if not results:
        return {"content": "", "urls": []}

    combined_content = []
    urls = []
    for result in results:
        combined_content.append(f"Source: {result['url']}\n{result['content']}\n")
        urls.append(result["url"])

    return {
        "content": "\n---\n".join(combined_content),
        "urls": urls,
    }


# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing Web Scraper with DuckDuckGo + SerpAPI fallback")
    logger.info("=" * 40)
    
    query = "Stevens Institute of Technology research areas"
    logger.info(f"Query: {query}")
    
    results = scrape_top3(query)
    
    if results:
        logger.info(f"\nSuccessfully retrieved {len(results)} results:")
        for i, result in enumerate(results, 1):
            logger.info(f"\n--- Result {i} ---")
            logger.info(f"URL: {result['url']}")
            logger.info(f"Content: {result['content'][:300]}...")
    else:
        logger.info("No results found")
