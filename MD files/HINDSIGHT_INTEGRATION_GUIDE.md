# Hindsight Integration Guide for VEDA

This guide explains how to integrate Hindsight memory into an existing VEDA codebase.

---

## Overview

Hindsight provides **persistent cross-session agent memory** that learns and improves over time. It works alongside (not replacing) ChromaDB:

- **ChromaDB**: Stores research documents for retrieval during sessions
- **Hindsight**: Stores learned facts about users and synthesizes patterns

---

## Installation

### 1. Add Hindsight Client Dependency

**requirements.txt:**
```
hindsight-client==0.6.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## Integration Steps

### Step 1: Settings Configuration

**config/settings.py** — Add this block inside the `Settings` class:

```python
# ── Hindsight (Vectorize) Agent Memory ──────────────────────────────
hindsight_mode: str = "local"           # "local" or "cloud"
hindsight_local_url: str = "http://localhost:8888"
hindsight_cloud_url: str = "https://api.hindsight.vectorize.io"
hindsight_api_key: str = ""             # Only needed for cloud mode
hindsight_bank_id: str = "veda"         # One memory bank per assistant
hindsight_recall_top_k: int = 5         # How many memories to inject
hindsight_reflect_every_n: int = 10     # Reflect after every N sessions
hindsight_enabled: bool = True          # Master on/off switch
hindsight_session_counter_file: str = "./memory/hindsight_session_count.json"
```

**Also update .env.example:**
```env
HINDSIGHT_MODE=local
HINDSIGHT_LOCAL_URL=http://localhost:8888
HINDSIGHT_CLOUD_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=
HINDSIGHT_BANK_ID=veda
HINDSIGHT_RECALL_TOP_K=5
HINDSIGHT_REFLECT_EVERY_N=10
HINDSIGHT_ENABLED=true
```

---

### Step 2: Extend AgentState

**agent/state.py** — Add these fields to `AgentState` TypedDict:

```python
# ── Hindsight Memory Fields ──────────────────────────────────────────
hindsight_memories: Optional[List[dict]]   # Recalled memories injected before response
hindsight_retained: bool                   # Whether retain() succeeded this session
hindsight_reflected: bool                  # Whether reflect() ran this session
```

---

### Step 3: Create Hindsight Store

Create **memory/hindsight_store.py** — The core client wrapper. See the file in this repository for complete implementation.

This file provides:
- `retain(content, session_id)` — Store session summary
- `recall(query, session_id)` — Retrieve relevant memories
- `reflect(session_id)` — Synthesize patterns
- `is_healthy()` — Health check for monitoring

---

### Step 4: Create Hindsight Nodes

Create two new LangGraph nodes:

**agent/nodes/hindsight_recall.py** — FIRST node in the graph
```python
async def hindsight_recall(state: AgentState) -> AgentState:
    """Query Hindsight and inject memories into state."""
    memories = await hindsight_store.recall(
        query=state["user_message"],
        session_id=state["session_id"],
    )
    return {
        **state,
        "hindsight_memories": memories,
        "hindsight_retained": False,
        "hindsight_reflected": False,
    }
```

**agent/nodes/hindsight_retain.py** — LAST node in the graph
```python
async def hindsight_retain(state: AgentState) -> AgentState:
    """Store session summary to Hindsight and trigger reflection."""
    memory_content = _build_memory_content(state)
    retained = await hindsight_store.retain(
        content=memory_content,
        session_id=state["session_id"],
    )
    reflected = await hindsight_store.end_session(
        session_id=state["session_id"],
    )
    return {
        **state,
        "hindsight_retained": retained,
        "hindsight_reflected": reflected,
    }
```

---

### Step 5: Rewire LangGraph

**agent/graph.py** — Modify `build_graph()` to include Hindsight nodes:

```python
from agent.nodes.hindsight_recall import hindsight_recall
from agent.nodes.hindsight_retain import hindsight_retain

def build_graph():
    graph = StateGraph(AgentState)
    
    # ── Register Hindsight nodes ───────────────────────────────────────
    graph.add_node("hindsight_recall", hindsight_recall)   # FIRST
    graph.add_node("hindsight_retain", hindsight_retain)   # LAST
    
    # ── Register all existing nodes ────────────────────────────────────
    graph.add_node("intent_router", intent_router)
    graph.add_node("planner", planner)
    graph.add_node("searcher", searcher)
    graph.add_node("reader", reader)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("reflector", reflector)
    graph.add_node("writer", writer)
    
    # ── Entry point: hindsight_recall ──────────────────────────────────
    graph.set_entry_point("hindsight_recall")
    
    # ── hindsight_recall → intent_router ───────────────────────────────
    graph.add_edge("hindsight_recall", "intent_router")
    
    # ── Conditional routing from intent_router ─────────────────────────
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "research": "planner",
            "recall": "writer",
            "general": "synthesizer",
            "study_mode": "writer",
            "file_op": "writer",
            "app_control": "writer",
            "schedule": "writer",
        }
    )
    
    # ── Existing pipeline edges (unchanged) ────────────────────────────
    graph.add_edge("planner", "searcher")
    graph.add_edge("searcher", "reader")
    graph.add_edge("reader", "synthesizer")
    graph.add_edge("synthesizer", "reflector")
    
    graph.add_conditional_edges(
        "reflector",
        should_rewrite,
        {
            "rewrite": "planner",
            "accept": "writer",
        }
    )
    
    # ── writer → hindsight_retain → END (CHANGED) ──────────────────────
    graph.add_edge("writer", "hindsight_retain")
    graph.add_edge("hindsight_retain", END)
    
    # ── Checkpointer ───────────────────────────────────────────────────
    memory = SqliteSaver.from_conn_string(settings.checkpoint_db_path)
    return graph.compile(checkpointer=memory)
```

---

### Step 6: Use Memories in Existing Nodes (Optional)

In **synthesizer.py** or **writer.py**, inject recalled memories into the LLM prompt:

```python
async def synthesizer(state: AgentState) -> AgentState:
    # ── Retrieve recalled memories ─────────────────────────────────────
    memories = state.get("hindsight_memories") or []
    
    memory_context = ""
    if memories:
        memory_lines = []
        for m in memories:
            content = m.get("content", "") if isinstance(m, dict) else str(m)
            if content:
                memory_lines.append(f"- {content}")
        if memory_lines:
            memory_context = (
                "LONG-TERM MEMORY (from past sessions with this user):\n"
                + "\n".join(memory_lines)
                + "\n\nUse the above context to personalise your response "
                  "if relevant. Do not mention that you are using memory.\n\n"
            )
    
    # ── Build full prompt with memory context ──────────────────────────
    full_prompt = memory_context + your_existing_prompt_template
    
    # ── Call LLM as usual ──────────────────────────────────────────────
    response = await llm.agenerate([full_prompt])
    
    return {
        **state,
        "synthesis": response.text,
    }
```

---

### Step 7: Add Health Monitoring

In your health monitor (or **main.py**), add this method:

```python
async def _check_hindsight(self) -> bool:
    """Check if Hindsight memory server is reachable."""
    from memory.hindsight_store import hindsight_store
    healthy = await hindsight_store.is_healthy()
    if healthy:
        logger.debug("[HEALTH] Hindsight OK")
    else:
        logger.warning(
            "[HEALTH] Hindsight unreachable — "
            "VEDA running without long-term memory. "
            "Start Docker: docker run -p 8888:8888 "
            "-e HINDSIGHT_API_LLM_API_KEY=ollama "
            "-e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 "
            "-e HINDSIGHT_API_LLM_MODEL=gemma2:2b "
            "ghcr.io/vectorize-io/hindsight"
        )
    return healthy
```

Also call it in your health check loop:
```python
async def check_all(self):
    # ... existing checks ...
    results["hindsight"] = await self._check_hindsight()
    return results
```

---

### Step 8: Docker Setup

Create **start_veda.bat** (for Windows) or **start_veda.sh** (for Linux/Mac):

```batch
@echo off
echo [VEDA] Starting Hindsight memory server...

REM Start or create Hindsight container
docker start hindsight-veda 2>nul || (
    echo [VEDA] Creating Hindsight container...
    docker run -d ^
      --name hindsight-veda ^
      -p 8888:8888 ^
      -e HINDSIGHT_API_LLM_API_KEY=ollama ^
      -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 ^
      -e HINDSIGHT_API_LLM_MODEL=gemma2:2b ^
      ghcr.io/vectorize-io/hindsight
)

echo [VEDA] Starting VEDA Python application...
python main.py
```

---

## Configuration Modes

### Local Mode (Default — Offline)

```env
HINDSIGHT_MODE=local
HINDSIGHT_LOCAL_URL=http://localhost:8888
```

Requires Docker with local LLM (Ollama). 100% offline, fully private.

### Cloud Mode (Free Tier Available)

```env
HINDSIGHT_MODE=cloud
HINDSIGHT_CLOUD_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_api_key
```

Sign up at [hindsight.vectorize.io](https://hindsight.vectorize.io). No Docker needed.

---

## Testing the Integration

### 1. Verify Installation

```bash
python -c "from memory.hindsight_store import hindsight_store; print('✓ Hindsight imported')"
```

### 2. Check Health

```bash
python -c "
import asyncio
from memory.hindsight_store import hindsight_store
print('Health:', asyncio.run(hindsight_store.is_healthy()))
"
```

### 3. Test Retain & Recall

```bash
python -c "
import asyncio
from memory.hindsight_store import hindsight_store

async def test():
    # Retain
    retained = await hindsight_store.retain(
        content='User prefers Python tutorials',
        session_id='test-123'
    )
    print(f'Retained: {retained}')
    
    # Recall
    memories = await hindsight_store.recall(
        query='Python tutorials',
        session_id='test-123'
    )
    print(f'Recalled {len(memories)} memories')

asyncio.run(test())
"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `hindsight_client not installed` | `pip install hindsight-client==0.6.0` |
| Docker connection refused (local mode) | `docker run -d -p 8888:8888 ghcr.io/vectorize-io/hindsight` |
| Memories not being recalled | Check `.env`: `HINDSIGHT_ENABLED=true` |
| `[HEALTH] Hindsight unreachable` | Verify Docker container is running or cloud API key is valid |
| Reflection not triggering | Complete at least 10 sessions (default threshold) |

---

## Performance Considerations

- **Recall latency**: ~100-200ms per query (network dependent)
- **Reflect latency**: ~1-2s per reflect operation (async, no blocking)
- **Memory overhead**: ~10MB per 1000 facts stored
- **Storage**: Cloud mode limited by Vectorize free tier; local mode unlimited

**VEDA never blocks on memory operations** — all Hindsight calls are async and wrapped with timeouts.

---

## Breaking Changes

**None.** Hindsight is a pure addition:
- All existing nodes remain unchanged
- ChromaDB still works as before
- If Hindsight is unavailable, VEDA continues normally
- No modifications to the core LangGraph pipeline

---

## Next Steps

1. ✅ Install `hindsight-client`
2. ✅ Update `config/settings.py` with Hindsight block
3. ✅ Add fields to `agent/state.py`
4. ✅ Create `memory/hindsight_store.py`
5. ✅ Create `agent/nodes/hindsight_recall.py`
6. ✅ Create `agent/nodes/hindsight_retain.py`
7. ✅ Rewire `agent/graph.py`
8. ✅ (Optional) Update synthesizer/writer to use memories
9. ✅ Add health monitoring
10. ✅ Setup Docker for local mode
11. ✅ Test with `test_hindsight.py` script

---

## References

- **Hindsight GitHub**: https://github.com/vectorize-io/hindsight
- **Hindsight Docs**: https://hindsight.vectorize.io
- **Hindsight Cloud**: https://api.hindsight.vectorize.io
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/

---

## Questions?

See the **README.md** or the [Hindsight documentation](https://hindsight.vectorize.io).
