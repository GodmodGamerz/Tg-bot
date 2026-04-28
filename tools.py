import asyncio
import logging
from duckduckgo_search import DDGS 
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# --- HARDCODED KEY FOR TESTING ---
TAVILY_API_KEY = "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"

try:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Tavily: {e}")
    tavily_client = None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary: DuckDuckGo (Free). Fallback: Tavily (Premium)."""
    
    # 1. Try DuckDuckGo first
    try:
        def ddg_sync():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))

        # 10-second timeout to prevent infinite hanging
        results = await asyncio.wait_for(
            asyncio.to_thread(ddg_sync),
            timeout=10.0
        )
        
        if results:
            formatted = "\n\n".join(
                f"🔎 <b>{r['title']}</b>\n{r['body'][:300]}...\n<i>Source: {r['href']}</i>" 
                for r in results
            )
            return f"<b>DuckDuckGo Results for '{query}':</b>\n\n{formatted}"
            
    except asyncio.TimeoutError:
        logger.warning("DuckDuckGo search timed out after 10s! Falling back to Tavily.")
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        
    # 2. Fallback to Tavily if DDG fails
    if tavily_client:
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    tavily_client.search, 
                    query=query, 
                    search_depth="advanced", 
                    max_results=max_results
                ),
                timeout=10.0
            )
            
            if results.get("results"):
                formatted = "\n\n".join(
                    f"🔎 <b>{r['title']}</b>\n{r['content'][:300]}...\n<i>Source: {r['url']}</i>" 
                    for r in results.get("results", [])
                )
                return f"<b>Tavily Search Results for '{query}':</b>\n\n{formatted}"
                
        except asyncio.TimeoutError:
            logger.error("Tavily search also timed out!")
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
    
    return "❌ No search results available at the moment."
