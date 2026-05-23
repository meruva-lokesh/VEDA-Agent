"""
Basic end-to-end test for VEDA agent.
Tests the intent_router → writer → hindsight_retain flow.
"""
import asyncio
from datetime import datetime
import uuid
from loguru import logger
from agent.graph import build_graph
from agent.state import AgentState
from config.settings import settings

# Add file logging for tests
logger.add(
    f"{settings.logs_path}/test_{{time}}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)


async def test_basic_query():
    """Test a basic general query through the agent."""
    logger.info("\n" + "="*70)
    logger.info("TEST: Basic Query")
    logger.info("="*70)
    
    try:
        # Build graph
        graph = build_graph()
        if graph is None:
            logger.error("Failed to build graph")
            return False

        # Create initial state
        state = AgentState(
            user_message="What is LangGraph?",
            tone="normal",
            screen_context=None,
            intent="general",
            topic=None,
            subtopics=None,
            search_urls=None,
            raw_content=None,
            synthesis=None,
            reflection_score=None,
            reflection_critique=None,
            reflection_loop_count=0,
            confidence_score=None,
            confidence_reason=None,
            final_response=None,
            sources_used=None,
            session_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            memory_retrieved=None,
            memory_saved=False,
            journal_path=None,
            error=None,
            fallback_used=False,
            raw_audio_path=None
        )

        logger.info(f"[TEST] Input: {state['user_message']}")
        logger.info(f"[TEST] Session: {state['session_id']}")

        # Invoke graph
        config = {"configurable": {"thread_id": state["session_id"]}}
        logger.info("[TEST] Invoking agent graph...")
        
        result = await graph.ainvoke(state, config)
        
        logger.info(f"[TEST] Graph execution complete")
        logger.info(f"[TEST] Intent: {result.get('intent')}")
        logger.info(f"[TEST] Tone: {result.get('tone')}")
        logger.info(f"[TEST] Confidence: {result.get('confidence_score')}")

        response = result.get("final_response", "")
        if response:
            logger.info(f"\n[TEST] ✓ RESPONSE RECEIVED:\n{response}\n")
            return True
        else:
            logger.error("[TEST] ✗ No response generated")
            if result.get("error"):
                logger.error(f"[TEST] Error: {result['error']}")
            return False

    except Exception as e:
        logger.error(f"[TEST] ✗ Test failed: {e}", exc_info=True)
        return False


async def test_research_query():
    """Test a research-type query."""
    logger.info("\n" + "="*70)
    logger.info("TEST: Research Query")
    logger.info("="*70)
    
    try:
        graph = build_graph()
        if graph is None:
            logger.error("Failed to build graph")
            return False

        state = AgentState(
            user_message="Explain machine learning concepts",
            tone="calm",
            screen_context=None,
            intent="research",
            topic=None,
            subtopics=None,
            search_urls=None,
            raw_content=None,
            synthesis=None,
            reflection_score=None,
            reflection_critique=None,
            reflection_loop_count=0,
            confidence_score=None,
            confidence_reason=None,
            final_response=None,
            sources_used=None,
            session_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            memory_retrieved=None,
            memory_saved=False,
            journal_path=None,
            error=None,
            fallback_used=False,
            raw_audio_path=None
        )

        logger.info(f"[TEST] Input: {state['user_message']}")

        config = {"configurable": {"thread_id": state["session_id"]}}
        result = await graph.ainvoke(state, config)
        
        response = result.get("final_response", "")
        if response:
            logger.info(f"\n[TEST] ✓ RESPONSE RECEIVED:\n{response}\n")
            return True
        else:
            logger.error("[TEST] ✗ No response generated")
            return False

    except Exception as e:
        logger.error(f"[TEST] ✗ Test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n\n")
    logger.info("#" * 70)
    logger.info("# VEDA BASIC END-TO-END TESTS")
    logger.info("#" * 70)

    results = []
    
    # Test 1: Basic query
    try:
        result = await test_basic_query()
        results.append(("Basic Query", result))
    except Exception as e:
        logger.error(f"Test exception: {e}")
        results.append(("Basic Query", False))

    # Test 2: Research query
    try:
        result = await test_research_query()
        results.append(("Research Query", result))
    except Exception as e:
        logger.error(f"Test exception: {e}")
        results.append(("Research Query", False))

    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} | {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        logger.info("\n✓ ALL TESTS PASSED - VEDA AGENT WORKING!\n")
        return 0
    else:
        logger.error(f"\n✗ {total - passed} TESTS FAILED\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
