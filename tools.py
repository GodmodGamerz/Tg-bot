import asyncio
import logging
from duckduckgo_search import DDGS  # Changed from AsyncDDGS
from tavily import TavilyClient
from config import Config

logger = logging.getLogger(__name__)

# Initialize Tavily with your key from config
tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary: Tavily (Premium). Fallback: DuckDuckGo (Free)."""
    
    # 1. Try Tavily first (as it provides better RAG-optimized results)
    if tavily_client:
        try:
            # We run the synchronous Tavily search in a separate thread to keep the bot async
            results = await asyncio.to_thread(
                tavily_client.search, 
                query=query, 
                search_depth="advanced", 
                max_results=max_results
            )
            
            if results.get("results"):
                formatted = "\n\n".join(
                    f"🔎 <b>{r['title']}</b>\n{r['content'][:300]}...\n<i>Source: {r['url']}</i>" 
                    for r in results.get("results", [])
                )
                return f"<b>Tavily Search Results for '{query}':</b>\n\n{formatted}"
        except Exception as e:
            logger.warning(f"Tavily search failed, falling back to DuckDuckGo: {e}")
    
    # 2. Fallback to DuckDuckGo using the new DDGS 6.x/7.x logic
    try:
        # DDGS().text() now returns a generator/list directly. 
        # We wrap it in to_thread to prevent blocking the aiogram event loop.
        def ddg_sync():
            with DDGS() as ddgs:
                # We convert to a list immediately to capture the results
                return list(ddgs.text(query, max_results=max_results))

        results = await asyncio.to_thread(ddg_sync)
        
        if results:
            formatted = "\n\n".join(
                f"🔎 <b>{r['title']}</b>\n{r['body'][:300]}...\n<i>Source: {r['href']}</i>" 
                for r in results
            )
            return f"<b>DuckDuckGo Results for '{query}':</b>\n\n{formatted}"
            
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        
    return "❌ No search results available at the moment."
