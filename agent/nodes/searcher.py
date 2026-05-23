"""
Searcher Node for VEDA's LangGraph agent.
Performs web searches to find relevant content for research.
Uses DuckDuckGo for privacy and offline-first approach.
"""
from loguru import logger
from agent.state import AgentState
from config.settings import settings

try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    logger.warning("[SEARCH] DuckDuckGo not installed")


async def searcher(state: AgentState) -> AgentState:
    """
    Search the web for content related to research queries.
    
    Args:
        state: Current agent state with search_urls (queries) set
    
    Returns:
        Updated state with raw_content containing search results
    """
    logger.info(
        f"[NODE: searcher] START | "
        f"queries={len(state.get('search_urls', []))}"
    )

    if not SEARCH_AVAILABLE:
        logger.error("[NODE: searcher] DuckDuckGo not available")
        return {
            **state,
            "raw_content": [],
            "error": "DuckDuckGo search not available"
        }

    try:
        results = []
        queries = state.get("search_urls", [])
        
        if not queries:
            logger.warning("[NODE: searcher] No search queries provided")
            return {**state, "raw_content": []}

        ddgs = DDGS(timeout=settings.ollama_timeout)

        for query in queries[:5]:  # Limit to 5 queries
            logger.info(f"[NODE: searcher] Searching: '{query}'")
            
            try:
                # Perform DuckDuckGo search
                search_results = ddgs.text(
                    query,
                    max_results=5,
                    region="wt-wt",
                    safesearch="moderate"
                )
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("body", ""),
                        "query": query
                    })
                
                logger.info(f"[NODE: searcher] Found {len(search_results)} results")

            except Exception as e:
                logger.warning(f"[NODE: searcher] Query failed: {query} | {e}")
                continue

        logger.info(
            f"[NODE: searcher] COMPLETE | "
            f"total_results={len(results)}"
        )

        return {
            **state,
            "raw_content": results
        }

    except Exception as e:
        logger.error(
            f"[NODE: searcher] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "raw_content": [],
            "error": f"searcher failed: {str(e)}"
        }
