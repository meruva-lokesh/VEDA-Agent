# VEDA Complete Setup & Run Summary

**Your AI assistant with persistent memory, running completely offline with Ollama.**

---

## 📊 Project Status

✅ **Hindsight Integration** — Cross-session memory system  
✅ **Ollama Support** — Local LLM models (offline)  
✅ **ChromaDB** — Research document storage  
✅ **LangGraph** — Agent orchestration  
✅ **Health Monitoring** — Auto-checks all components  

**All components ready to run offline with zero external dependencies.**

---

## 🎯 Architecture at a Glance

```
┌────────────────────────────────────────────┐
│  VEDA (Your AI Assistant)                  │
│  - LangGraph agent orchestration          │
│  - Hindsight cross-session memory         │
│  - ChromaDB research storage              │
├────────────────────────────────────────────┤
│  Local Services (100% Offline)            │
├────────────────────────────────────────────┤
│  ✓ Ollama (LLM)          :11434           │
│  ✓ Hindsight (Memory)    :8888            │
│  ✓ ChromaDB (Documents)  :8000 (optional) │
└────────────────────────────────────────────┘
```

---

## 🚀 To Get Running (Choose Your Speed)

### ⚡ I'm in a Hurry (5 minutes)
→ Go to [QUICK_START.md](QUICK_START.md)

### 🛠️ I Want Details (30 minutes)
→ Go to [RUN_GUIDE.md](RUN_GUIDE.md)

### 🧠 I Want to Learn Ollama First
→ Go to [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)

---

## 📖 File Guide

| File | Purpose | Read When |
|------|---------|-----------|
| [QUICK_START.md](QUICK_START.md) | 5-minute setup | You want to run VEDA immediately |
| [RUN_GUIDE.md](RUN_GUIDE.md) | Step-by-step setup (7 steps) | You want comprehensive guidance |
| [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) | Ollama installation & config | You're new to local LLMs |
| [README.md](README.md) | Architecture & features | You want to understand VEDA |
| [HINDSIGHT_INTEGRATION_GUIDE.md](HINDSIGHT_INTEGRATION_GUIDE.md) | Memory system details | You want to customize memory |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Technical checklist | You want implementation details |

---

## 🎬 The Essentials (Copy-Paste These)

### Install Python Dependencies

```bash
cd e:\VEDA PROJECT
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Download Ollama Model

```bash
ollama pull mistral
# Or: neural-chat, llama2, dolphin-mixtral
```

### Configure VEDA

**File: `.env`**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
HINDSIGHT_ENABLED=true
HINDSIGHT_MODE=local
```

### Run VEDA

```bash
# Windows
start_veda.bat

# macOS/Linux
bash start_veda.sh

# Or manually:
python main.py
```

---

## ✅ What You Get

### Immediately
- ✅ Local LLM (Mistral/Neural-Chat/Llama2 via Ollama)
- ✅ Instant responses (offline)
- ✅ No API costs
- ✅ Complete privacy
- ✅ GPU acceleration (if available)

### After 10 Sessions
- ✅ Hindsight memory system activates
- ✅ VEDA learns your preferences
- ✅ Personalized responses
- ✅ Pattern recognition
- ✅ Cross-session context awareness

### Always
- ✅ 100% offline operation
- ✅ Auto-health monitoring
- ✅ Persistent checkpoints
- ✅ Zero external dependencies
- ✅ Research document storage (ChromaDB)

---

## 🔧 Configuration Quick Reference

### Minimal (.env)
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
HINDSIGHT_ENABLED=true
```

### Production (.env)
```env
# LLM
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
TEMPERATURE=0.7
MAX_TOKENS=2000

# Memory
HINDSIGHT_ENABLED=true
HINDSIGHT_MODE=local
HINDSIGHT_RECALL_TOP_K=5
HINDSIGHT_REFLECT_EVERY_N=10

# Storage
CHROMADB_PATH=./memory/chromadb
CHECKPOINT_DB_PATH=./memory/checkpoints.db

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

## 📊 Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **neural-chat** | 3.6GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Friendly conversations |
| **mistral** | 4.1GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Recommended** |
| **llama2** | 3.8GB | ⚡⚡ | ⭐⭐⭐⭐ | General purpose |
| **dolphin-mixtral** | 26GB | ⚡ | ⭐⭐⭐⭐⭐ | Complex reasoning |

**Recommendation:** Start with `mistral` — it's fast and good quality.

---

## 🎯 Typical Usage Flow

### First Run
```
1. Install Python, Ollama
2. Pull model: ollama pull mistral
3. Configure .env (3 lines)
4. Run: python main.py
5. VEDA starts! ✅
```

### Session 1-9
```
User Input
  ↓
Hindsight queries memory (empty first time)
  ↓
LangGraph routes through appropriate nodes
  ↓
Ollama generates response
  ↓
Response + session summary stored to Hindsight
  ↓
Output to user
```

### Session 10 (Reflection Threshold)
```
Same as above, plus:
  ↓
Hindsight.reflect() runs
  ↓
Raw facts → Synthesized patterns
  ↓
"User prefers Python tutorials" (learned)
  ↓
Session 11+ gets smarter!
```

---

## 🔍 Monitoring & Debugging

### Check if Ollama is Running
```bash
curl http://localhost:11434/api/tags
```

### Check if Hindsight is Running
```bash
docker ps | grep hindsight-veda
```

### View VEDA Logs
```bash
# Logs appear in terminal where you ran: python main.py
# Look for lines starting with [VEDA], [HINDSIGHT], [HEALTH]
```

### Run Tests
```bash
python test_hindsight.py      # Test memory system
python test_quick.py          # Test LLM integration
```

---

## 🆘 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `Connection refused: 11434` | Ollama not running: `ollama serve` |
| `Module not found: ollama` | Install deps: `pip install -r requirements.txt` |
| `Hindsight not responding` | Start Docker & Hindsight: `start_veda.bat` |
| Slow responses | Use faster model: `OLLAMA_MODEL=neural-chat` |
| Out of memory | Use smaller model or reduce `MAX_TOKENS` |
| `port 11434 already in use` | Kill process or use different port |

See [RUN_GUIDE.md](RUN_GUIDE.md) for detailed troubleshooting.

---

## 📁 Directory Structure

```
e:\VEDA PROJECT/
├── venv/                    ← Python environment (auto-created)
├── memory/                  ← Persistent storage
│   ├── chromadb/           ← Research documents
│   ├── hindsight_session_count.json
│   └── checkpoints.db
├── agent/                   ← LangGraph nodes
│   ├── graph.py
│   ├── state.py
│   └── nodes/
│       ├── hindsight_recall.py
│       └── hindsight_retain.py
├── config/
│   └── settings.py
├── .env                     ← Your configuration
├── main.py                  ← Entry point
├── requirements.txt         ← Dependencies
└── [GUIDES]
    ├── QUICK_START.md
    ├── RUN_GUIDE.md
    ├── OLLAMA_SETUP_GUIDE.md
    └── README.md
```

---

## 🎮 Running VEDA

### Automated (Recommended)

**Windows:**
```bash
# Just double-click:
start_veda.bat
```

**macOS/Linux:**
```bash
bash start_veda.sh
```

### Manual

**Terminal 1 - Ensure Ollama running:**
```bash
ollama serve
```

**Terminal 2 - Start Hindsight (if using local):**
```bash
docker run -d --name hindsight-veda -p 8888:8888 \
  -e HINDSIGHT_API_LLM_API_KEY=ollama \
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 \
  -e HINDSIGHT_API_LLM_MODEL=gemma2:2b \
  ghcr.io/vectorize-io/hindsight
```

**Terminal 3 - Run VEDA:**
```bash
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
python main.py
```

---

## 🌟 Features Overview

### ✨ Hindsight Memory
- Retain facts after every session
- Recall relevant memories before responses
- Reflect & synthesize patterns every 10 sessions
- Learns user preferences automatically

### 🧠 Ollama LLM
- 20+ models available
- Instant responses (offline)
- GPU acceleration support
- No API keys needed

### 📚 ChromaDB
- Store research documents
- Semantic search
- Persist between sessions
- Integrate your own data

### 📊 LangGraph
- Multi-step workflows
- Conditional routing
- State persistence
- Checkpointing

### 🏥 Health Monitoring
- Auto-checks all services
- Graceful degradation
- Detailed logging
- No crashes on service failure

---

## 📚 Documentation Files

All documentation is in this project:

1. **[QUICK_START.md](QUICK_START.md)** — 5-min setup
2. **[RUN_GUIDE.md](RUN_GUIDE.md)** — Comprehensive guide
3. **[OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)** — Model details
4. **[README.md](README.md)** — Architecture overview
5. **[HINDSIGHT_INTEGRATION_GUIDE.md](HINDSIGHT_INTEGRATION_GUIDE.md)** — Memory system
6. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** — Technical details

---

## 🚀 You're All Set!

**Your VEDA setup includes:**
- ✅ Hindsight persistent memory
- ✅ Ollama local models (offline)
- ✅ ChromaDB document storage
- ✅ LangGraph orchestration
- ✅ Health monitoring
- ✅ Complete documentation
- ✅ Integration tests

### Next: Pick a guide and run!

```
⏱️  5 minutes?   → QUICK_START.md
📖 30 minutes?  → RUN_GUIDE.md  
🔬 Learning?    → OLLAMA_SETUP_GUIDE.md
```

---

**🎉 Enjoy your offline, private, self-learning AI assistant!**
