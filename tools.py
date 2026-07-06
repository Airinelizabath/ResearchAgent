import time
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

# State tracking for query reformulation limits
_searched_queries = []

def reset_search_state():
    """Resets the history of searched queries for testing or multiple runs in the same process."""
    global _searched_queries
    _searched_queries.clear()

def search_tool(query: str) -> list[dict]:
    """Searches the web for relevant sources using DuckDuckGo (via ddgs).

    Args:
        query: The search query to run.

    Returns:
        A list of dictionaries containing 'title', 'url', and 'snippet'.
        
    Raises:
        RuntimeError: If search fails, returns no results, or exceeds query reformulation limits.
    """
    global _searched_queries
    
    # 1. Enforce query reformulation limits (maximum 2 reformulations, i.e., 3 unique queries in total)
    if query not in _searched_queries:
        if len(_searched_queries) >= 3:
            raise RuntimeError(
                f"Query reformulation limit reached. Max 2 reformulations (3 unique queries) allowed. "
                f"Already attempted: {_searched_queries}"
            )
        _searched_queries.append(query)

    # 2. Add a 1.5-second delay between consecutive search calls to prevent rate limits
    if len(_searched_queries) > 1:
        time.sleep(1.5)

    # 3. Perform search with error handling and raise failures
    try:
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=6))
            
            if not ddg_results:
                raise RuntimeError(f"No search results returned for query: '{query}'")
                
            results = []
            for r in ddg_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
            return results
    except Exception as e:
        # Raise failure directly to surface it to the agent/user
        raise RuntimeError(f"Search failed for query '{query}': {e}")

def read_page_tool(url: str) -> str:
    """Fetches the webpage content from the given URL and extracts clean plain text.

    Args:
        url: The absolute URL of the webpage to read.

    Returns:
        A plain text string of the webpage content, truncated to 4000 characters.
    """
    try:
        # Proper browser-like headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0"
        }
        
        # Request with a 10s timeout
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Remove script, style, header, footer, navigation elements
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing whitespace on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Truncate to avoid context window issues
        return clean_text[:4000]
    except Exception as e:
        # Returns the error description so the runner skips this page but the agent continues
        return f"Error reading page {url}: {e}"
