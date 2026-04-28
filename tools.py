import asyncio
from ddgs import AsyncDDGS
from tavily import TavilyClient
from config import Config

tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary: DuckDuckGo (free & async). Fallback: Tavily (if key provided)."""
    try:
        async with AsyncDDGS() as ddgs:
            results = await ddgs.text(query, max_results=max_results)
            if results:
                formatted = "\n\n".join(
                    f"🔎 {r['title']}\n{r['body'][:300]}...\nSource: {r['href']}"
                    for r in results
                )
                return f"Web search results for '{query}':\n\n{formatted}"
    except Exception:
        pass  # silent fallback

    # Tavily fallback (high quality paid)
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
