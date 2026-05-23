"""
agent/nodes/hindsight_recall.py

LangGraph node: HindsightRecall

This is the FIRST node in the VEDA graph. It runs before intent_router.

Responsibility:
  Query Hindsight memory for facts relevant to the user's current message
  and inject them into AgentState as hindsight_memories. Downstream nodes
  (synthesizer, writer) read this field to personalise their responses.

Why first:
  Every subsequent node benefits from knowing what VEDA has learned about
  this user. Placing recall here means zero changes to existing nodes —
  they simply read state['hindsight_memories'] if they need context.

Failure mode:
  If Hindsight is unavailable, hindsight_memories is set to [] and the
  graph continues normally. VEDA never crashes due to memory failure.
"""

from loguru import logger
from agent.state import AgentState
from memory.hindsight_store import hindsight_store


async def hindsight_recall(state: AgentState) -> AgentState:
    """
    Retrieve relevant long-term memories before processing the user query.

    Queries the Hindsight memory bank using the user's current message
    as the search query. Injects results into state['hindsight_memories']
    so all downstream nodes can access personalised context.

    Args:
        state: Current AgentState containing user_message and session_id.

    Returns:
        Updated AgentState with hindsight_memories populated (or [] on fail).
    """
    logger.info(
        f"[NODE: hindsight_recall] Starting | session={state['session_id']}"
    )

    try:
        memories = await hindsight_store.recall(
            query=state["user_message"],
            session_id=state["session_id"],
        )

        logger.info(
            f"[NODE: hindsight_recall] Complete | "
            f"memories_injected={len(memories)} | "
            f"session={state['session_id']}"
        )

        return {
            **state,
            "hindsight_memories": memories,
            "hindsight_retained": False,
            "hindsight_reflected": False,
        }

    except Exception as e:
        logger.error(
            f"[NODE: hindsight_recall] Unexpected error: {e} | "
            f"session={state['session_id']}",
            exc_info=True,
        )
        return {
            **state,
            "hindsight_memories": [],
            "hindsight_retained": False,
            "hindsight_reflected": False,
            "error": f"hindsight_recall failed: {str(e)}",
        }
