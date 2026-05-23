"""
agent/state.py

LangGraph AgentState definition with Hindsight memory fields.

This TypedDict defines all state that flows through the VEDA LangGraph
agent graph. New fields are immutable at runtime but can be merged via
return statements from nodes.
"""

from typing import TypedDict, Optional, List, Any


class AgentState(TypedDict, total=False):
    """
    Mutable state dictionary shared across all VEDA agent nodes.

    The 'total=False' parameter makes all fields optional — nodes can
    choose which fields to return in their updates.

    Use 'state | {"key": value}' or 'return {**state, "key": value}'
    to merge updates.
    """

    # ── User Input ───────────────────────────────────────────────────────
    user_message: str  # Raw user input (text or transcribed voice)
    session_id: str  # Unique session identifier for persistence
    user_id: Optional[str]  # Optional user context for multi-user systems

    # ── Intent Classification ────────────────────────────────────────────
    intent: str  # "research", "recall", "general", "study_mode", etc.
    topic: Optional[str]  # Extracted topic from user_message
    tone: str  # Detected user tone: "calm", "stressed", "confused", "normal"
    confidence_score: float  # Confidence in the answer (0-10 scale)

    # ── Planning Phase ───────────────────────────────────────────────────
    query: str  # Refined search query for semantic search
    search_strategy: Optional[str]  # Strategy: "broad", "narrow", "follow_up"
    plan: Optional[str]  # High-level step-by-step plan
    sources: Optional[List[str]]  # URLs or document IDs to search

    # ── Search & Retrieval ───────────────────────────────────────────────
    search_results: Optional[List[dict]]  # Raw ChromaDB search results
    documents: Optional[List[dict]]  # Full document content retrieved

    # ── Analysis & Synthesis ─────────────────────────────────────────────
    synthesis: Optional[str]  # Synthesized response before reflection
    reflection_score: float  # Quality score from reflector node (0-10)
    reflection_loop_count: int  # How many rewrite loops have occurred
    reflection_feedback: Optional[str]  # Specific feedback for improvement

    # ── Response Generation ──────────────────────────────────────────────
    final_response: str  # Final response ready for user
    response_format: str  # "text", "voice", "code", "table", etc.
    citations: Optional[List[str]]  # Sources cited in response

    # ── Hindsight (Vectorize) Memory Fields ────────────────────────────────
    hindsight_memories: Optional[List[dict]]  # Recalled long-term memories
    hindsight_retained: bool  # Whether retain() succeeded this session
    hindsight_reflected: bool  # Whether reflect() was triggered

    # ── Error Handling ───────────────────────────────────────────────────
    error: Optional[str]  # Error message if any node fails gracefully


# Type aliases for convenience
SessionData = AgentState
