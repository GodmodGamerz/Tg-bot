import asyncio
from ddgs import DDGS
from tavily import TavilyClient
from config import Config

tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else None

async def web_search(query: str, max_results: int = 8) -> str:
    """Primary search: DuckDuckGo (wrapped in thread for async compatibility) + Tavily fallback"""
    
    # DuckDuckGo synchronous search wrapped in asyncio thread
    def sync_search():
        try:
            with DDGS() as ddgs:
                results = ddgs.text(keywords=query, max_results=max_results)
                if results:
                    formatted = "\n\n".join(
                        f"🔎 {r.get('title', 'No title')}\n"
                        f"{r.get('body', r.get('snippet', ''))[:280]}...\n"
                        f"Source: {r.get('href', r.get('url', 'N/A'))}"
                        for r in results
                    )
                    return f"Web search results for '{query}':\n\n{formatted}"
        except Exception as e:
            print(f"DDGS error: {e}")
        return None

    try:
        result = await asyncio.to_thread(sync_search)
        if result:
            return result
    except Exception as e:
        print(f"Web search thread error: {e}")

    # Fallback to Tavily (high quality)
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
