"""
Reader Node for VEDA's LangGraph agent.
Extracts and cleans content from URLs.
Uses trafilatura for robust HTML parsing.
"""
from loguru import logger
from agent.state import AgentState

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.warning("[READER] Trafilatura not installed")


async def reader(state: AgentState) -> AgentState:
    """
    Read and extract content from URLs in search results.
    
    Args:
        state: Current agent state with raw_content (search results)
    
    Returns:
        Updated state with extracted and cleaned content
    """
    logger.info(
        f"[NODE: reader] START | "
        f"results={len(state.get('raw_content', []))}"
    )

    if not TRAFILATURA_AVAILABLE:
        logger.error("[NODE: reader] Trafilatura not available")
        return {
            **state,
            "synthesis": "Could not extract content - trafilatura not available"
        }

    try:
        extracted_content = []
        raw_results = state.get("raw_content", [])

        if not raw_results:
            logger.warning("[NODE: reader] No content to read")
            return {**state, "synthesis": "No search results found"}

        for result in raw_results[:10]:  # Limit to 10 URLs
            url = result.get("url", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            if not url:
                continue

            logger.info(f"[NODE: reader] Extracting: {url}")

            try:
                # Try to fetch and extract
                downloaded = trafilatura.fetch_url(url, timeout=5)
                
                if not downloaded:
                    logger.warning(f"[NODE: reader] Could not fetch: {url}")
                    # Use snippet instead
                    extracted_content.append({
                        "title": title,
                        "url": url,
                        "content": snippet,
                        "source": "snippet"
                    })
                    continue

                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    favor_precision=True
                )

                if extracted:
                    extracted_content.append({
                        "title": title,
                        "url": url,
                        "content": extracted[:500],  # First 500 chars
                        "source": "full"
                    })
                    logger.info(f"[NODE: reader] Extracted {len(extracted)} chars")
                else:
                    # Fallback to snippet
                    extracted_content.append({
                        "title": title,
                        "url": url,
                        "content": snippet,
                        "source": "snippet"
                    })

            except Exception as e:
                logger.warning(f"[NODE: reader] Extraction failed: {url} | {e}")
                extracted_content.append({
                    "title": title,
                    "url": url,
                    "content": snippet,
                    "source": "snippet"
                })
                continue

        logger.info(
            f"[NODE: reader] COMPLETE | "
            f"extracted={len(extracted_content)}"
        )

        # Format content for synthesis
        formatted = "\n---\n".join([
            f"Title: {item['title']}\nURL: {item['url']}\nContent: {item['content']}"
            for item in extracted_content
        ])

        return {
            **state,
            "raw_content": extracted_content,
            "synthesis": formatted
        }

    except Exception as e:
        logger.error(
            f"[NODE: reader] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "synthesis": f"Error reading content: {str(e)}",
            "error": f"reader failed: {str(e)}"
        }
