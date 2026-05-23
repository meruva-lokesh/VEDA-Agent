"""
Master LangGraph definition for VEDA.
Connects all agent nodes into a directed graph with conditional routing.

Graph flow:
  hindsight_recall (memory injection)
    → intent_router (classify intent)
      → [conditional routing by intent]
        ├─ research: planner → searcher → reader → synthesizer → reflector
        ├─ recall: (direct to writer)
        └─ general/other: (direct to writer)
      → writer (format response)
        → hindsight_retain (memory storage & reflection)
          → END

All nodes run asynchronously with proper error handling and logging.
"""
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.hindsight_recall import hindsight_recall
from agent.nodes.hindsight_retain import hindsight_retain
from agent.nodes.intent_router import intent_router
from agent.nodes.writer import writer
from loguru import logger
from config.settings import settings
import os


def route_by_intent(state: AgentState) -> str:
    """
    Route to correct processing pipeline based on classified intent.
    
    Args:
        state: Current agent state with intent field set
    
    Returns:
        Node name to route to next
    """
    intent = state.get("intent", "general")
    logger.info(f"[GRAPH] route_by_intent | intent={intent}")
    
    # For MVP, route all intents to writer
    # In future, research intents will go through full pipeline
    return "writer"


def build_graph():
    """
    Construct and compile the VEDA LangGraph agent.
    
    Returns:
        Compiled LangGraph graph with SQLite checkpointing for persistence.
    """
    graph = StateGraph(AgentState)

    logger.info("[GRAPH] Building VEDA agent graph...")

    # ── Register all nodes ───────────────────────────────────────────────
    graph.add_node("hindsight_recall", hindsight_recall)
    graph.add_node("intent_router", intent_router)
    graph.add_node("writer", writer)
    graph.add_node("hindsight_retain", hindsight_retain)

    # TODO: Add future nodes
    # graph.add_node("planner", planner)
    # graph.add_node("searcher", searcher)
    # graph.add_node("reader", reader)
    # graph.add_node("synthesizer", synthesizer)
    # graph.add_node("reflector", reflector)

    # ── Define edges (node connections) ──────────────────────────────────
    graph.set_entry_point("hindsight_recall")
    
    # hindsight_recall always goes to intent_router
    graph.add_edge("hindsight_recall", "intent_router")
    
    # intent_router routes conditionally based on intent classification
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {"writer": "writer"}  # For MVP, all paths lead to writer
    )
    
    # writer always goes to hindsight_retain for memory storage
    graph.add_edge("writer", "hindsight_retain")
    
    # hindsight_retain is the final node before END
    graph.add_edge("hindsight_retain", END)

    logger.info("[GRAPH] Compiling graph (in-memory checkpointing)...")
    # Compile without external checkpointer for simplicity
    # In production, can add SqliteSaver or other persistence
    compiled_graph = graph.compile()
    logger.info("[GRAPH] ✓ Graph built and compiled successfully")
    
    return compiled_graph


# Build graph singleton at module load time
try:
    agent_graph = build_graph()
except Exception as e:
    logger.error(f"[GRAPH] ✗ Failed to build graph: {e}", exc_info=True)
    agent_graph = None
