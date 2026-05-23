"""
agent/nodes/hindsight_retain.py

LangGraph node: HindsightRetain

This is the LAST node in the VEDA graph. It runs after writer, before END.

Responsibility:
  Build a compact memory string from this session's exchange and store it
  in Hindsight so future sessions benefit from what was learned today.
  Also calls end_session() which triggers periodic reflect().

What gets retained:
  A single natural-language string summarising:
    - What the user asked (intent + topic)
    - What VEDA answered (final_response summary)
    - The user's tone (stressed / calm / confused / normal)
    - Confidence score for this answer

Why a summary instead of the raw transcript:
  Hindsight's reflect() works best on clean, atomic facts. Storing a
  distilled summary per session produces higher-quality reflections than
  dumping raw conversation text.

Failure mode:
  If retain fails, hindsight_retained is set to False and the graph ends
  normally. The session is not lost — it stays in ChromaDB via the writer.
"""

from loguru import logger
from agent.state import AgentState
from memory.hindsight_store import hindsight_store


def _build_memory_content(state: AgentState) -> str:
    """
    Build a compact, natural-language summary of this VEDA session.

    Extracts intent, topic, tone, confidence, and a truncated version
    of the final response to create a memory string Hindsight can use
    for future personalisation and reflection.

    Args:
        state: Completed AgentState after writer node has run.

    Returns:
        str: Single natural-language fact suitable for Hindsight retain().
    """
    intent = state.get("intent", "unknown")
    topic = state.get("topic") or state.get("user_message", "")[:80]
    tone = state.get("tone", "normal")
    confidence = state.get("confidence_score", "N/A")

    response_preview = ""
    if state.get("final_response"):
        response_preview = state["final_response"][:200].replace("\n", " ")

    return (
        f"User asked about '{topic}' with intent '{intent}' and tone '{tone}'. "
        f"VEDA responded with confidence {confidence}/10. "
        f"Response summary: {response_preview}"
    )


async def hindsight_retain(state: AgentState) -> AgentState:
    """
    Store this session's exchange in Hindsight long-term memory.

    Builds a compact memory string and retains it via the Hindsight
    client. Also calls end_session() to increment the session counter
    and trigger periodic reflect() automatically.

    Args:
        state: Fully completed AgentState after writer node has run.

    Returns:
        Updated AgentState with hindsight_retained and hindsight_reflected
        flags set to indicate what operations completed successfully.
    """
    logger.info(
        f"[NODE: hindsight_retain] Starting | session={state['session_id']}"
    )

    try:
        memory_content = _build_memory_content(state)

        retained = await hindsight_store.retain(
            content=memory_content,
            session_id=state["session_id"],
        )

        reflected = False
        if retained:
            reflected = await hindsight_store.end_session(
                session_id=state["session_id"],
            )

        logger.info(
            f"[NODE: hindsight_retain] Complete | "
            f"retained={retained} | reflected={reflected} | "
            f"session={state['session_id']}"
        )

        return {
            **state,
            "hindsight_retained": retained,
            "hindsight_reflected": reflected,
        }

    except Exception as e:
        logger.error(
            f"[NODE: hindsight_retain] Unexpected error: {e} | "
            f"session={state['session_id']}",
            exc_info=True,
        )
        return {
            **state,
            "hindsight_retained": False,
            "hindsight_reflected": False,
        }
