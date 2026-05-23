# VEDA Complete Run Guide

This guide walks you through everything needed to get VEDA running locally with Ollama models, Hindsight memory, and ChromaDB.

---

## 🎯 Overview: What You'll Have

By the end of this guide, VEDA will run with:

| Component | Technology | Purpose | Status |
|-----------|-----------|---------|--------|
| **LLM** | Ollama (local) | Generate responses | 🟢 Offline |
| **Memory (Facts)** | Hindsight | Cross-session learning | 🟢 Offline |
| **Memory (Research)** | ChromaDB | Document storage | 🟢 Offline |
| **Graph** | LangGraph | Orchestration | 🟢 Local |

**Everything runs locally — 100% offline, zero API costs, complete privacy.**

---

## 📋 Prerequisites

### Required
- **Windows 10+** or **macOS** or **Linux**
- **Python 3.9+**
- **4GB RAM minimum** (8GB recommended)
- **5GB disk space** for models

### Optional
- **NVIDIA GPU** (for faster inference)
- **Docker Desktop** (for Hindsight local mode)

---

## 🔧 STEP 1: Install Prerequisites

### Windows

#### 1a) Install Python 3.11

1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ **Check "Add Python to PATH"**
4. Click "Install Now"

**Verify installation:**
```cmd
python --version
```

#### 1b) Install Ollama

1. Download https://ollama.ai/download/OllamaSetup.exe
2. Run installer
3. Click "Install"
4. Ollama starts automatically

**Verify installation:**
```cmd
ollama --version
```

#### 1c) (Optional) Install Docker Desktop

Only needed for **Hindsight local mode**. If using cloud mode, skip this.

1. Download https://www.docker.com/products/docker-desktop
2. Run installer
3. Follow on-screen instructions
4. Restart Windows

**Verify installation:**
```cmd
docker --version
```

---

## 📥 STEP 2: Download & Setup VEDA

### 2a) Open Command Prompt

```cmd
# Windows: Press Win+R, type "cmd"
# macOS/Linux: Open Terminal
```

### 2b) Navigate to VEDA Project

```cmd
cd e:\VEDA PROJECT
```

### 2c) Create Python Virtual Environment

```cmd
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Verify:**
```
# Prompt should show: (venv) ...
```

### 2d) Install Dependencies

```cmd
pip install -r requirements.txt
```

**Wait for installation to complete (~5-10 minutes)**

---

## 📦 STEP 3: Download Ollama Models

### Pull Recommended Model (Mistral)

```cmd
ollama pull mistral
```

**This downloads ~4GB — takes 2-5 minutes depending on internet**

### (Optional) Pull Alternative Models

```cmd
# Fast & friendly
ollama pull neural-chat

# More capable
ollama pull llama2

# Very capable (requires 20GB+)
ollama pull dolphin-mixtral
```

### Verify Models Downloaded

```cmd
ollama list
```

Should show:
```
NAME                INSECURE  ID              SIZE
mistral:latest              4.1 GB
```

---

## ⚙️ STEP 4: Configure VEDA

### 4a) Copy Environment Template

```cmd
copy .env.example .env
```

### 4b) Edit .env Configuration

Open `.env` in a text editor (Notepad, VS Code, etc.):

```env
# ── LLM Configuration ────────────────────────────────────────────────────────
# Use local Ollama (offline)
LLM_PROVIDER=ollama
LLM_MODEL=mistral

# Ollama API endpoint
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Leave cloud keys blank (we're using local)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ── Hindsight (Vectorize) Agent Memory ───────────────────────────────────────
HINDSIGHT_MODE=local
HINDSIGHT_ENABLED=true

# ── ChromaDB Memory (Research Documents) ─────────────────────────────────────
CHROMADB_PATH=./memory/chromadb
CHROMADB_COLLECTION=veda_research

# ── General ──────────────────────────────────────────────────────────────────
DEBUG=false
LOG_LEVEL=INFO
```

**Save the file.**

### 4c) Verify Configuration

```cmd
python -c "from config.settings import settings; print(f'✓ Config loaded: {settings.llm_provider}')"
```

Should output: `✓ Config loaded: ollama`

---

## 🚀 STEP 5: Start Services (Quick Start)

### Option A: Automated Startup (Recommended)

#### Windows - Double-click start_veda.bat

```cmd
# The script will:
# 1. Check Docker installation
# 2. Start Hindsight container (if local mode)
# 3. Verify Ollama is running
# 4. Launch VEDA
```

Just double-click: **start_veda.bat**

#### macOS/Linux - Run startup script

```bash
bash start_veda.sh  # (or create manually)
```

### Option B: Manual Startup (Advanced)

If automated script doesn't work, start manually:

#### Terminal 1: Ensure Ollama is Running

```cmd
# Windows (should be running as service)
# Verify:
curl http://localhost:11434/api/tags

# If not responding, start manually:
ollama serve
```

#### Terminal 2: Start Hindsight (Local Mode Only)

```cmd
# If using local Hindsight:
docker run -d ^
  --name hindsight-veda ^
  -p 8888:8888 ^
  -e HINDSIGHT_API_LLM_API_KEY=ollama ^
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 ^
  -e HINDSIGHT_API_LLM_MODEL=gemma2:2b ^
  ghcr.io/vectorize-io/hindsight
```

#### Terminal 3: Start VEDA

```cmd
# Make sure virtual environment is activated
venv\Scripts\activate

# Run VEDA
python main.py
```

---

## ✅ STEP 6: Verify Everything is Working

### Check Ollama Health

```cmd
curl http://localhost:11434/api/tags
```

**Expected output:** JSON with models list

### Check Hindsight Health

```cmd
# If using local mode:
curl http://localhost:8888/api/health
```

**Expected output:** 200 OK

### Test Full VEDA Stack

```cmd
python test_hindsight.py
```

**Should show:**
```
[HINDSIGHT] Initialised | mode=local
[HEALTH] Hindsight OK
✓ TEST 1: Client initialization... PASS
✓ TEST 2: Health check... PASS
...
✓ ALL TESTS PASSED
```

---

## 🎮 STEP 7: Use VEDA

### Example: Interactive Chat

Create `test_veda.py`:

```python
import asyncio
from agent.graph import agent_graph
from agent.state import AgentState

async def main():
    # Create initial state
    state = {
        "user_message": "What are the benefits of Python?",
        "session_id": "test-session-1",
        "user_id": "user-1",
    }
    
    # Run through graph
    config = {"configurable": {"thread_id": "default"}}
    result = await agent_graph.ainvoke(state, config)
    
    print(f"Response: {result.get('final_response', 'No response')}")

asyncio.run(main())
```

Run it:
```cmd
python test_veda.py
```

---

## 📊 System Architecture During Runtime

```
┌─────────────────────────────────────────────────────────────┐
│                     VEDA (Python)                           │
│                   (main.py running)                         │
├─────────────────────────────────────────────────────────────┤
│  ├─ LangGraph Agent (agent/graph.py)                        │
│  ├─ ChromaDB (./memory/chromadb/) ← Research docs           │
│  ├─ Hindsight Client (localhost:8888) ← Cross-session mem   │
│  └─ LLM Client (localhost:11434) ← Local Ollama             │
└─────────────────────────────────────────────────────────────┘
         │              │                      │
         │              │                      │
    ┌────▼─────┐  ┌────▼──────┐      ┌───────▼────┐
    │ ChromaDB  │  │ Hindsight  │      │   Ollama   │
    │  (Local)  │  │  (Docker)  │      │   (Local)  │
    └───────────┘  └────────────┘      └────────────┘
```

---

## 🛑 Stopping VEDA

### Gracefully Shutdown

**In VEDA terminal:**
```cmd
Ctrl+C
```

This will:
- Stop LangGraph processing
- Close ChromaDB connections
- Retain any session memories
- Leave Ollama & Hindsight running

### Stop All Services

```cmd
# Stop Ollama (Windows service)
net stop ollama

# Or manually:
taskkill /IM ollama.exe

# Stop Hindsight container
docker stop hindsight-veda

# Stop Docker
# (Or just close Docker Desktop)
```

---

## 🔄 Restart Services

### Just VEDA

```cmd
# Terminal: 
venv\Scripts\activate
python main.py
```

### Ollama (if stuck)

```cmd
net stop ollama
net start ollama
```

Or restart Windows.

### Hindsight (if stuck)

```cmd
docker stop hindsight-veda
docker rm hindsight-veda

# Then restart via start_veda.bat
```

---

## 📈 Monitor Running Services

### Check Ollama Status

```cmd
# Is it running?
curl -s http://localhost:11434/api/tags | find "mistral"

# Should find your model
```

### Check Hindsight Status

```cmd
# Is Docker container running?
docker ps | find "hindsight-veda"

# Check logs:
docker logs hindsight-veda --tail 20
```

### Check VEDA Logs

Logs appear in the terminal where you ran `python main.py`:

```
[2026-05-16 10:30:45] [VEDA] Starting VEDA...
[2026-05-16 10:30:46] [HINDSIGHT] Initialised | mode=local
[2026-05-16 10:30:47] [GRAPH] Building LangGraph agent...
[2026-05-16 10:30:48] [MAIN] VEDA ready — awaiting input...
```

---

## 🆘 Quick Troubleshooting

### "Connection refused: localhost:11434"

**Ollama not running:**
```cmd
# Windows service stopped?
net start ollama

# Or start manually:
ollama serve
```

### "Docker daemon not running"

**Hindsight needs Docker:**
```cmd
# Open Docker Desktop application (Windows/Mac)
# On Linux:
sudo systemctl start docker
```

### "ModuleNotFoundError: hindsight_client"

**Virtual environment issue:**
```cmd
# Reactivate environment:
venv\Scripts\activate

# Reinstall:
pip install -r requirements.txt
```

### Slow Response Times

**Model too heavy:**
```env
# Switch to faster model
OLLAMA_MODEL=neural-chat
```

**Or restart everything:**
```cmd
net stop ollama
net start ollama
```

### Port Already in Use

**Another app using port 11434:**
```cmd
# Find what's using it:
netstat -ano | findstr :11434

# Kill the process:
taskkill /PID <PID> /F

# Or use different port:
# Set OLLAMA_BASE_URL=http://localhost:11435
```

---

## 📚 File Structure After Setup

```
e:\VEDA PROJECT\
├── venv\                          ← Python environment
├── memory\
│   ├── chromadb\                  ← ChromaDB data (auto-created)
│   ├── hindsight_session_count.json
│   └── checkpoints.db
├── agent\
│   ├── graph.py
│   ├── state.py
│   └── nodes\
│       ├── hindsight_recall.py
│       └── hindsight_retain.py
├── config\
│   └── settings.py
├── .env                           ← Your configuration
├── main.py
├── start_veda.bat
├── requirements.txt
└── README.md
```

---

## 🎯 Next Steps

1. ✅ Complete STEP 1-4 above
2. ✅ Run `start_veda.bat` (or manual startup)
3. ✅ See logs showing "VEDA ready"
4. ✅ Create your own agents/workflows
5. ✅ Read [README.md](README.md) for architecture
6. ✅ Check [HINDSIGHT_INTEGRATION_GUIDE.md](HINDSIGHT_INTEGRATION_GUIDE.md) for memory usage
7. ✅ Review [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) for model options

---

## 💡 Pro Tips

### Faster Startup
```bash
# Pre-load Ollama on Windows boot
# Settings → Apps → Startup → Enable "Ollama"
```

### Better Performance
```env
# Reduce context for faster responses
MAX_TOKENS=1000

# Use faster model
OLLAMA_MODEL=neural-chat
```

### Save Session State
```bash
# VEDA automatically saves session checkpoints
# Stored in: ./memory/checkpoints.db
# Persists across restarts
```

### Monitor Resource Usage
```cmd
# Watch GPU/VRAM usage (while VEDA is running)
# Task Manager → Performance → GPU
```

---

## 📞 Support

- **Ollama Issues**: https://github.com/ollama/ollama/issues
- **Hindsight Issues**: https://github.com/vectorize-io/hindsight/issues
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **ChromaDB Docs**: https://docs.trychroma.com/

---

## ✨ You're Ready!

```
🚀 VEDA is ready to run completely offline with:
   ✅ Local Ollama LLMs
   ✅ Hindsight memory system
   ✅ ChromaDB research storage
   ✅ LangGraph orchestration
   
   → 100% offline, zero cost, complete privacy
```

**Happy coding! 🎉**
