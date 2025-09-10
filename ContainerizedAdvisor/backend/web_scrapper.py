import os
import requests
from bs4 import BeautifulSoup
import time
import random

def duckduckgo_search_urls(query, num_results=3):
    """Perform a DuckDuckGo search and return the top result URLs."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }
    
    search_url = "https://duckduckgo.com/html/"
    params = {"q": query}
    
    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for result in soup.select(".result__a"):
            href = result.get("href")
            if href and href.startswith("/l/?uddg="):
                url = href.split("/l/?uddg=")[1]
                if url and not url.startswith("duckduckgo.com"):
                    links.append(url)
                    if len(links) == num_results:
                        break
        if not links:
            for link in soup.select("a[href*='http']"):
                href = link.get("href")
                if href and "duckduckgo.com" not in href and href.startswith("http"):
                    links.append(href)
                    if len(links) == num_results:
                        break
        print(f"Found {len(links)} URLs from DuckDuckGo")
        return links
    except Exception as e:
        print(f"Error in DuckDuckGo search: {e}")
        return []

def serpapi_search_urls(query, num_results=3, api_key=None):
    """Use SerpAPI to get Google search results as a backup."""
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key == "your_serpapi_key_here":
        print("No SerpAPI key available.")
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
        links = []
        for result in data.get("organic_results", []):
            if result.get("link"):
                links.append(result["link"])
                if len(links) == num_results:
                    break
        print(f"Found {len(links)} URLs from SerpAPI (Google)")
        return links
    except Exception as e:
        print(f"Error in SerpAPI search: {e}")
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
    
    # Combine text
    combined_text = " ".join(text_elements)
    return " ".join(combined_text.split())  # Clean whitespace

def scrape_top3(query, num_results=5, api_key=None):
    """Search and fetch top 5 URLs, return their cleaned text."""
    
    print(f"Searching for: {query}")
    
    # Try DuckDuckGo first (more reliable for scraping)
    urls = duckduckgo_search_urls(query, num_results)
    if not urls:
        print("DuckDuckGo failed, trying SerpAPI (Google)...")
        urls = serpapi_search_urls(query, num_results, api_key=api_key)
    
    if not urls:
        print("No URLs found from any search engine")
        return []
    
    results = []
    for i, url in enumerate(urls, 1):
        try:
            print(f"Fetching content from {i}/{len(urls)}: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/91.0.4472.124 Safari/537.36"
            }
            
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            
            text = clean_html(resp.text)
            if text:
                results.append({"url": url, "content": text[:3000]})  # Increased from 2000 to 3000 chars
                print(f"Successfully extracted {len(text)} characters")
            else:
                results.append({"url": url, "content": "No text content found"})
                print("No text content found")
            
            # Random delay between requests
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            results.append({"url": url, "content": f"Failed to fetch: {e}"})
    
    return results

def scrape_web_content(query, num_results=5, api_key=None):
    """
    Simple function to scrape web content for a query.
    
    Args:
        query: The search query
        num_results: Number of results to process (increased from 3 to 5)
        
    Returns:
        Combined text content from web sources
    """
    results = scrape_top3(query, num_results=num_results, api_key=api_key)
    
    if not results:
        return "No relevant information found on the web."
    
    # Combine all content
    combined_content = []
    for result in results:
        combined_content.append(f"Source: {result['url']}\n{result['content']}\n")
    
    return "\n---\n".join(combined_content)

# Example usage:
if __name__ == "__main__":
    print("Testing Web Scraper with DuckDuckGo + SerpAPI fallback")
    print("=" * 40)
    
    query = "Python programming tutorials"
    print(f"Query: {query}")
    
    results = scrape_top3(query)
    
    if results:
        print(f"\nSuccessfully retrieved {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"URL: {result['url']}")
            print(f"Content: {result['content'][:300]}...")
    else:
        print("No results found")