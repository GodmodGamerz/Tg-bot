import asyncio
from duckduckgo_search import AsyncDDGS
from tavily import TavilyClient
from config import Config

tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary: DuckDuckGo (free). Fallback: Tavily (if key provided)."""
    try:
        # DuckDuckGo is always available and async
        ddgs = AsyncDDGS()
        results = await ddgs.text(query, max_results=max_results)
        if results:
            formatted = "\n\n".join(
                f"🔎 {r['title']}\n{r['body'][:300]}...\nSource: {r['href']}"
                for r in results
            )
            return f"Web search results for '{query}':\n\n{formatted}"
    except Exception:
        pass  # fallback silently

    # Tavily fallback (paid but high quality)
    if tavily_client:
        try:
            results = tavily_client.search(query, max_results=max_results)
            formatted = "\n\n".join(
                f"🔎 {r['title']}\n{r['content'][:300]}...\nSource: {r['url']}"
                for r in results.get("results", [])
            )
            return f"Web search results for '{query}':\n\n{formatted}"
        except Exception as e:
            return f"Search error: {str(e)}"
    return "No search results available at the moment."
