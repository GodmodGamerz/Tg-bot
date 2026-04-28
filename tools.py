import asyncio
import logging
from duckduckgo_search import AsyncDDGS
from tavily import TavilyClient
from config import Config

logger = logging.getLogger(__name__)

tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary: Tavily (Premium). Fallback: DuckDuckGo (Free)."""
    
    # 1. Try Tavily first if key is available
    if tavily_client:
        try:
            # Tavily is synchronous, so we run it in a thread to keep the bot async
            results = await asyncio.to_thread(
                tavily_client.search, 
                query=query, 
                search_depth="advanced", 
                max_results=max_results
            )
            formatted = "\n\n".join(
                f"🔎 <b>{r['title']}</b>\n{r['content'][:300]}...\n<i>Source: {r['url']}</i>" 
                for r in results.get("results", [])
            )
            return f"<b>Tavily Search Results for '{query}':</b>\n\n{formatted}"
        except Exception as e:
            logger.warning(f"Tavily search failed, falling back to DuckDuckGo: {e}")
    
    # 2. Fallback to DuckDuckGo
    try:
        ddgs = AsyncDDGS()
        results = await ddgs.text(query, max_results=max_results)
        if results:
            formatted = "\n\n".join(
                f"🔎 <b>{r['title']}</b>\n{r['body'][:300]}...\n<i>Source: {r['href']}</i>" 
                for r in results
            )
            return f"<b>DuckDuckGo Results for '{query}':</b>\n\n{formatted}"
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        
    return "❌ No search results available at the moment."
