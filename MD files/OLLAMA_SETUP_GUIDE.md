# Ollama Setup Guide for VEDA

This guide explains how to install Ollama and use local models with VEDA for 100% offline operation.

---

## 📦 What is Ollama?

**Ollama** is an open-source tool that lets you run large language models (LLMs) locally on your machine:

- ✅ **100% Offline** — No API calls, no internet required
- ✅ **Free** — Open source, no subscription
- ✅ **Fast** — Models run on your hardware (GPU-accelerated)
- ✅ **Private** — All data stays on your machine
- ✅ **Simple** — One command to pull & run models

**Popular Ollama Models:**
- `mistral` (7B) — Fast, good quality (recommended for VEDA)
- `neural-chat` (7B) — Conversational, friendly
- `llama2` (7B or 13B) — Solid general-purpose model
- `dolphin-mixtral` (8x7B MoE) — Advanced reasoning (slower)
- `starling-lm` (7B) — Good at following instructions

---

## 🚀 Installation

### Windows (Recommended for VEDA)

1. **Download Ollama for Windows**
   ```
   https://ollama.ai/download/OllamaSetup.exe
   ```

2. **Run the installer**
   - Accept the license
   - Choose installation location (default is fine)
   - Ollama will start automatically as a background service

3. **Verify installation**
   ```cmd
   ollama --version
   ```
   
   Should output: `ollama version X.X.X`

### macOS

```bash
# Download DMG or use Homebrew
brew install ollama

# Start Ollama service
ollama serve
```

### Linux

```bash
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

---

## 📥 Download Models

Pull the model you want to use:

```bash
# Recommended for VEDA (fast, good quality)
ollama pull mistral

# Alternative options
ollama pull neural-chat
ollama pull llama2
ollama pull dolphin-mixtral
ollama pull starling-lm
```

**First time?** Start with `mistral` — it's fast and works great.

### Model Details

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| mistral | 4.1GB | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Good | General Q&A, chat |
| neural-chat | 3.6GB | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Good | Conversational |
| llama2 | 3.8GB (7B) | ⚡⚡ Medium | ⭐⭐⭐⭐ Good | Research, coding |
| dolphin-mixtral | 26GB | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent | Complex reasoning |
| starling-lm | 4.1GB | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ Good | Following instructions |

### Check Downloaded Models

```bash
ollama list
```

Output:
```
NAME                INSECURE  ID              SIZE      MODIFIED
mistral:latest              4.1 GB   2 minutes ago
neural-chat:latest          3.6 GB   5 minutes ago
```

---

## ✅ Verify Ollama is Running

### Windows

Ollama runs as a background service. To verify:

```cmd
# Test if Ollama API is responding
curl http://localhost:11434/api/tags
```

Should return JSON with list of models.

### macOS / Linux

```bash
# Start Ollama if not running
ollama serve &

# Test API
curl http://localhost:11434/api/tags
```

---

## 🔧 Configure VEDA to Use Ollama

### Step 1: Copy Environment Template

```bash
cd e:\VEDA PROJECT
copy .env.example .env
```

### Step 2: Edit .env

```env
# Use local Ollama (offline)
LLM_PROVIDER=ollama
LLM_MODEL=mistral

# Ollama API endpoint
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Leave cloud keys blank (we're using local)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# LLM parameters
TEMPERATURE=0.7
MAX_TOKENS=2000
```

**Quick Setup (just change these lines):**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### Step 3: Verify Configuration

```bash
python -c "from config.settings import settings; print(f'Provider: {settings.llm_provider}, Model: {settings.ollama_model}')"
```

Should output: `Provider: ollama, Model: mistral`

---

## 📝 Usage Patterns

### Test Ollama with Python

```python
import requests

# Direct Ollama API call
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "What is Python?",
        "stream": False
    }
)
print(response.json()["response"])
```

### Using Ollama with LangChain (VEDA Integration)

```python
from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="mistral",
    base_url="http://localhost:11434"
)

response = llm.invoke("What is machine learning?")
print(response)
```

---

## 🌐 Running Hindsight + Ollama

Both VEDA and Hindsight can use local Ollama models:

### Hindsight Configuration

In your `start_veda.bat`:

```batch
docker run -d ^
  --name hindsight-veda ^
  -p 8888:8888 ^
  -e HINDSIGHT_API_LLM_API_KEY=ollama ^
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 ^
  -e HINDSIGHT_API_LLM_MODEL=gemma2:2b ^
  ghcr.io/vectorize-io/hindsight
```

### VEDA Configuration

In `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

**Result:** Both VEDA and Hindsight running completely offline with local models!

---

## 📊 Performance Tuning

### For Different Hardware

**GPU-Accelerated (NVIDIA/AMD/Metal):**
```bash
# Ollama automatically uses GPU if available
# Monitor GPU usage:
# - NVIDIA: nvidia-smi
# - AMD: rocm-smi
```

**CPU-Only:**
```bash
# Use smaller, faster models
ollama pull mistral  # 4GB, very fast
ollama pull neural-chat  # 3.6GB, fast
```

**Limited RAM:**
```env
# Use quantized models (smaller)
OLLAMA_MODEL=mistral:q4_0  # Quantized version
```

### Temperature Settings

```env
# More deterministic (consistent answers)
TEMPERATURE=0.1

# Balanced (recommended for VEDA)
TEMPERATURE=0.7

# More creative/varied
TEMPERATURE=1.0
```

---

## 🐛 Troubleshooting

### Ollama Not Running

**Problem:** `ConnectionError: http://localhost:11434`

**Solutions:**
1. **Windows**: Check Services → Ollama is running
   ```cmd
   net start ollama
   ```

2. **Manual start**
   ```bash
   ollama serve
   ```

3. **Verify on browser**
   ```
   http://localhost:11434/api/tags
   ```

### Model Not Found

**Problem:** `Error: model "mistral" not found`

**Solution:**
```bash
ollama pull mistral
ollama list  # Verify it was downloaded
```

### Out of Memory

**Problem:** Model crashes or very slow

**Solutions:**
1. Use a smaller model
   ```bash
   ollama pull mistral  # Instead of dolphin-mixtral
   ```

2. Reduce context length
   ```env
   MAX_TOKENS=1024
   ```

3. Use quantized version
   ```bash
   ollama pull mistral:q4_0  # 4-bit quantized
   ```

### Slow Response Times

**Problem:** LLM takes 30+ seconds to respond

**Causes & Solutions:**
- ✅ **GPU not detected?** Reinstall Ollama with GPU support
- ✅ **Model too large?** Switch to `mistral` or `neural-chat`
- ✅ **Insufficient RAM?** Use quantized model (`:q4_0`)
- ✅ **Running other apps?** Close resource hogs (Chrome, VS Code, etc.)

### Port Already in Use

**Problem:** `Address already in use: 11434`

**Solution 1:** Stop existing Ollama
```cmd
taskkill /IM ollama.exe /F
```

**Solution 2:** Use different port
```env
OLLAMA_BASE_URL=http://localhost:11435
```

Then run Ollama on custom port:
```bash
ollama serve --address localhost:11435
```

---

## 📚 Ollama Commands Reference

```bash
# List all downloaded models
ollama list

# Pull a new model
ollama pull mistral

# Run model interactively
ollama run mistral

# Delete a model
ollama rm mistral

# Show model details
ollama show mistral

# API endpoint (runs in background)
ollama serve

# Stop Ollama service
ollama stop

# View logs
ollama logs
```

---

## 🔌 API Reference

### Health Check

```bash
curl http://localhost:11434/api/tags
```

### Generate Response (Streaming)

```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "prompt": "Why is the sky blue?",
    "stream": false
  }'
```

### Show Model Info

```bash
curl http://localhost:11434/api/show \
  -d '{"name": "mistral"}'
```

---

## 🎯 Recommended Setup for VEDA

### Balanced (Recommended)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
TEMPERATURE=0.7
MAX_TOKENS=2000
```

**Performance:** Fast (< 2 sec per response)  
**Quality:** Good (4-5 stars)  
**VRAM:** 4-6GB  

### Fast Setup (Limited Resources)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=neural-chat
TEMPERATURE=0.5
MAX_TOKENS=1024
```

**Performance:** Very fast (< 1 sec)  
**Quality:** Good (4 stars)  
**VRAM:** 3-4GB  

### High Quality Setup (More Resources)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=dolphin-mixtral
TEMPERATURE=0.8
MAX_TOKENS=3000
```

**Performance:** Slow (5-10 sec)  
**Quality:** Excellent (5 stars)  
**VRAM:** 20-30GB  

---

## 📖 More Information

- **Ollama Website**: https://ollama.ai
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **API Docs**: https://github.com/ollama/ollama/blob/main/docs/api.md

---

## ✅ Next Steps

1. ✅ Download & install Ollama from https://ollama.ai
2. ✅ Pull a model: `ollama pull mistral`
3. ✅ Edit `.env`: Set `LLM_PROVIDER=ollama`
4. ✅ Update `OLLAMA_MODEL=mistral`
5. ✅ Run VEDA: `python main.py`
6. ✅ Enjoy 100% offline AI!

---

**🚀 You're now ready to run VEDA completely offline with local Ollama models!**
