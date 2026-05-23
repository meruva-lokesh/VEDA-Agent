# ⚡ VEDA Quick Start (5 Minutes)

**Goal:** Get VEDA running offline with local Ollama models in minimal time.

---

## 📋 Checklist

- [ ] Python 3.9+ installed
- [ ] Ollama installed
- [ ] Ollama model pulled (`mistral`)
- [ ] VEDA cloned/setup
- [ ] `.env` configured
- [ ] VEDA running

---

## 🚀 5-Minute Setup

### 1️⃣ Install Ollama (2 min)

**Windows:**
- Download: https://ollama.ai/download/OllamaSetup.exe
- Run installer
- Verify: `ollama --version`

**macOS:**
```bash
brew install ollama
ollama serve &
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
ollama serve &
```

### 2️⃣ Pull Model (1 min)

```bash
ollama pull mistral
```

**Verify:**
```bash
ollama list
```

Should show: `mistral:latest    4.1 GB`

### 3️⃣ Setup VEDA (1 min)

```bash
cd e:\VEDA PROJECT

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4️⃣ Configure (1 min)

```bash
copy .env.example .env
# Edit .env and set:
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=mistral
```

### 5️⃣ Install & Run

```bash
pip install -r requirements.txt
python main.py
```

**Done! ✅ VEDA is running offline.**

---

## 🎮 Test It

### In another terminal:

```python
# test_quick.py
import asyncio
from agent.graph import agent_graph

async def test():
    state = {
        "user_message": "What is AI?",
        "session_id": "test-1",
    }
    config = {"configurable": {"thread_id": "default"}}
    result = await agent_graph.ainvoke(state, config)
    print(result.get("final_response", "No response"))

asyncio.run(test())
```

Run:
```bash
python test_quick.py
```

---

## 🛑 Stop

```bash
# In VEDA terminal:
Ctrl+C

# To stop Ollama (Windows):
net stop ollama
```

---

## 📚 Next Steps

- Read [RUN_GUIDE.md](RUN_GUIDE.md) for detailed setup
- Read [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) for model options
- Read [README.md](README.md) for architecture

---

**🎉 That's it! VEDA is running completely offline.**
