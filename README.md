# VEDA — Agent with Persistent Cross-Session Memory

**VEDA** (Vectorial Entity for Dialogue Autonomy) is an AI assistant powered by LangGraph with dual-layer memory: ChromaDB for research documents and **Hindsight** (by Vectorize) for learned facts and user patterns.

---

## 🧠 Architecture

### Dual Memory Layers

| Layer | Purpose | Technology |
|-------|---------|-----------|
| **ChromaDB** | Store & retrieve research documents | Semantic vector search |
| **Hindsight** | Store & recall user facts & learned patterns | Retain → Recall → Reflect |

**ChromaDB** is document-focused: it stores raw research papers, articles, and reference material that VEDA retrieves to answer research-heavy questions.

**Hindsight** is user-focused: it stores learned facts about the user (preferences, patterns, past topics) and synthesizes them into higher-order knowledge over time.

### LangGraph Flow with Hindsight

```
┌──────────────────────────────────────────────────────────────┐
│ User Input                                                   │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ hindsight_recall (FIRST)                                    │
│ ├─ Query Hindsight for relevant memories                   │
│ └─ Inject into state for downstream nodes                   │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ intent_router                                                │
│ ├─ Classify intent (research, recall, general, etc.)       │
│ └─ Route to appropriate pipeline                            │
└──────────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
    [planner]         [synthesizer]    [writer]
      ↓                                   (for direct Q&A)
   [searcher]
      ↓
   [reader]
      ↓
 [synthesizer]
      ↓
 [reflector] ← Quality gate (rewrite if needed)
      ↓
   [writer]
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ hindsight_retain (LAST)                                     │
│ ├─ Build session summary                                    │
│ ├─ Store in Hindsight long-term memory                     │
│ ├─ Increment session counter                                │
│ └─ Trigger reflection if threshold met (every N sessions)  │
└──────────────────────────────────────────────────────────────┘
                           ↓
                    Final Response
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker (for local Hindsight mode)
- OpenAI API key (or local LLM)

### 1. Clone & Setup

```bash
cd e:\VEDA PROJECT
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start VEDA

**Windows:**
```cmd
start_veda.bat
```

This automatically:
- Starts Hindsight Docker container (if in local mode)
- Launches VEDA Python application
- Connects both memory systems

---

## 🧠 Hindsight Modes

### Local Mode (Default — 100% Offline)

```env
HINDSIGHT_MODE=local
HINDSIGHT_LOCAL_URL=http://localhost:8888
```

Requires Docker. Hindsight uses a local LLM (Ollama) for memory synthesis:

```bash
docker run -d \
  --name hindsight-veda \
  -p 8888:8888 \
  -e HINDSIGHT_API_LLM_API_KEY=ollama \
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 \
  -e HINDSIGHT_API_LLM_MODEL=gemma2:2b \
  ghcr.io/vectorize-io/hindsight
```

**Pros:**
- ✅ Fully offline — no external API calls
- ✅ No API keys needed
- ✅ Complete data privacy
- ✅ Fast local inference

**Cons:**
- ⚠️ Requires Docker & local LLM
- ⚠️ Slower synthesis (depends on local LLM)

---

### Cloud Mode (Hindsight Cloud Free Tier)

```env
HINDSIGHT_MODE=cloud
HINDSIGHT_CLOUD_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_api_key_here
```

Sign up for free at **[hindsight.vectorize.io](https://hindsight.vectorize.io)**

**Pros:**
- ✅ Zero infrastructure — no Docker needed
- ✅ Fast cloud-hosted synthesis
- ✅ Free tier available
- ✅ No local LLM required

**Cons:**
- ⚠️ External API dependency
- ⚠️ Requires internet connection
- ⚠️ Data sent to Vectorize servers

---

## 📝 Using Hindsight Memories in Nodes

Downstream nodes (synthesizer, writer) can access recalled memories via `state['hindsight_memories']`:

```python
# In synthesizer.py or writer.py, before calling the LLM:

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

# Prepend memory_context to your prompt template:
full_prompt = memory_context + your_existing_prompt_template
```

---

## 📊 Hindsight Configuration

All settings are in `config/settings.py` and `.env`:

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `hindsight_mode` | str | `"local"` | `"local"` or `"cloud"` |
| `hindsight_enabled` | bool | `True` | Master on/off switch |
| `hindsight_recall_top_k` | int | `5` | Memories to inject per query |
| `hindsight_reflect_every_n` | int | `10` | Reflect threshold (sessions) |
| `hindsight_bank_id` | str | `"veda"` | Memory bank identifier |

---

## 🛠️ Architecture Details

### New Files

- **`memory/hindsight_store.py`**: Core Hindsight client wrapper
  - `retain(content, session_id)` → Store a session summary
  - `recall(query, session_id)` → Retrieve relevant memories
  - `reflect(session_id)` → Synthesize memories into patterns
  - `is_healthy()` → Health check for monitor

- **`agent/nodes/hindsight_recall.py`**: First LangGraph node
  - Queries Hindsight using user's current message
  - Injects results into `state['hindsight_memories']`
  - Graceful fallback if Hindsight unavailable

- **`agent/nodes/hindsight_retain.py`**: Last LangGraph node
  - Builds compact session summary from state
  - Stores to Hindsight after writer runs
  - Triggers periodic reflect()

### Modified Files

- **`config/settings.py`**: Added Hindsight configuration block
- **`agent/state.py`**: Added Hindsight state fields
- **`agent/graph.py`**: Rewired entry/exit to include Hindsight nodes
- **`requirements.txt`**: Added `hindsight-client==0.6.0`

---

## 💾 Session Counter & Reflection

Hindsight automatically triggers reflection every N sessions:

```
Session 1-9:  retain() only
Session 10:   retain() + reflect() ← synthesizes patterns
Session 11-19: retain() only
Session 20:   retain() + reflect() ← updates patterns
```

Session count is persisted to `memory/hindsight_session_count.json`.

Configure with `HINDSIGHT_REFLECT_EVERY_N` in `.env`.

---

## 🏥 Health Monitoring

VEDA's health monitor automatically checks Hindsight:

```log
[HEALTH] Hindsight OK
```

If Hindsight is down:

```log
[HEALTH] Hindsight unreachable — VEDA running without long-term memory
```

**VEDA continues normally** — Hindsight failure never crashes the assistant.

---

## 🐛 Troubleshooting

### "hindsight_client not installed"
```bash
pip install hindsight-client==0.6.0
```

### "Hindsight unreachable" (local mode)
```bash
# Verify Docker is running
docker ps

# Start Hindsight manually
docker run -d \
  --name hindsight-veda \
  -p 8888:8888 \
  -e HINDSIGHT_API_LLM_API_KEY=ollama \
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 \
  -e HINDSIGHT_API_LLM_MODEL=gemma2:2b \
  ghcr.io/vectorize-io/hindsight
```

### Memories not being recalled
- Check `HINDSIGHT_ENABLED=true` in `.env`
- Check logs for `[HINDSIGHT] Recalled` entries
- Verify at least 1 session has completed (memories stored)

### Reflection not triggering
- Check `HINDSIGHT_REFLECT_EVERY_N` setting (default 10)
- Run 10 sessions, then check logs for `[HINDSIGHT] Reflected`

---

## 📚 Hindsight Documentation

- **GitHub**: [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight)
- **Docs**: [hindsight.vectorize.io](https://hindsight.vectorize.io)
- **License**: MIT (free & open-source)

---

## 🔐 Privacy & Data

- **Local mode**: 100% offline — no data leaves your machine
- **Cloud mode**: Hindsight Cloud handles data per their [privacy policy](https://hindsight.vectorize.io/privacy)

Hindsight stores only the facts you explicitly `retain()` — never raw conversation transcripts.

---

## ✅ Feature Checklist

- ✅ Persistent cross-session memory (Hindsight)
- ✅ Research document storage (ChromaDB)
- ✅ Automatic memory synthesis (Hindsight reflect)
- ✅ Graceful degradation (VEDA works without memory)
- ✅ Dual offline/cloud modes
- ✅ Health monitoring
- ✅ Session tracking and telemetry
- ✅ Zero breaking changes to existing nodes

---

## 📄 License

VEDA uses [Hindsight by Vectorize](https://github.com/vectorize-io/hindsight) under the **MIT License**.

---

**Questions?** See the [Hindsight docs](https://hindsight.vectorize.io) or open an issue.
