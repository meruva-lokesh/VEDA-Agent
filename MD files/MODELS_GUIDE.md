# Ollama Models Guide for VEDA

Complete reference for choosing and configuring Ollama models with VEDA.

---

## 🎯 Quick Model Selection

### 🚀 I Want Speed
**Use: `neural-chat`**
```env
OLLAMA_MODEL=neural-chat
TEMPERATURE=0.5
MAX_TOKENS=1024
```
- 3.6GB
- ⚡ < 1 sec response
- Friendly, conversational

### ⚖️ I Want Balance (Recommended)
**Use: `mistral`**
```env
OLLAMA_MODEL=mistral
TEMPERATURE=0.7
MAX_TOKENS=2000
```
- 4.1GB
- ⚡⚡ ~1-2 sec response
- Great quality, very capable
- **VEDA Default**

### 🧠 I Want Quality
**Use: `llama2`**
```env
OLLAMA_MODEL=llama2
TEMPERATURE=0.8
MAX_TOKENS=2000
```
- 3.8GB (7B), 6.5GB (13B)
- ⚡⚡ ~2-3 sec response
- Excellent reasoning
- Great for technical questions

### 🔬 I Want Maximum Quality (High Resources)
**Use: `dolphin-mixtral`**
```env
OLLAMA_MODEL=dolphin-mixtral
TEMPERATURE=0.9
MAX_TOKENS=3000
```
- 26GB
- ⚡ ~5-10 sec response
- Expert-level reasoning
- Requires 24GB+ RAM & GPU

---

## 📊 Model Comparison Table

| Model | Size | VRAM | Speed | Quality | Best For | Install |
|-------|------|------|-------|---------|----------|---------|
| neural-chat | 3.6GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Chat, friendly | `ollama pull neural-chat` |
| **mistral** | 4.1GB | 4GB | ⚡⚡ | ⭐⭐⭐⭐ | **General** | `ollama pull mistral` |
| tinyllama | 1.1GB | 2GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Low resources | `ollama pull tinyllama` |
| llama2 | 3.8GB | 5GB | ⚡⚡ | ⭐⭐⭐⭐ | Technical | `ollama pull llama2` |
| llama2:13b | 6.5GB | 10GB | ⚡ | ⭐⭐⭐⭐⭐ | Research | `ollama pull llama2:13b` |
| phi | 1.4GB | 2GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Light | `ollama pull phi` |
| starling-lm | 4.1GB | 5GB | ⚡⚡ | ⭐⭐⭐⭐ | Instructions | `ollama pull starling-lm` |
| dolphin-mixtral | 26GB | 30GB | ⚡ | ⭐⭐⭐⭐⭐ | Complex | `ollama pull dolphin-mixtral` |

---

## 🔍 Detailed Model Profiles

### 1. Mistral (⭐ RECOMMENDED)

```bash
ollama pull mistral
```

**Profile:**
- Size: 4.1GB
- VRAM Required: 4-6GB
- Speed: 1-2 seconds per response
- Quality: 4/5 stars
- Use Cases: General Q&A, coding help, creative writing

**VEDA Config:**
```env
OLLAMA_MODEL=mistral
TEMPERATURE=0.7
MAX_TOKENS=2000
TOP_P=0.95
```

**Example Usage:**
```
Q: Explain machine learning in 2 sentences
A: ✓ Fast, clear, accurate response

Q: Write Python code for sorting
A: ✓ Good code, explains reasoning

Q: Tell me a joke
A: ✓ Actually funny!
```

**Best For:** New users, all-purpose assistant

---

### 2. Neural-Chat (Fast & Friendly)

```bash
ollama pull neural-chat
```

**Profile:**
- Size: 3.6GB
- VRAM Required: 3-4GB
- Speed: < 1 second per response
- Quality: 4/5 stars
- Personality: Conversational, friendly

**VEDA Config:**
```env
OLLAMA_MODEL=neural-chat
TEMPERATURE=0.5
MAX_TOKENS=1024
```

**Example Usage:**
```
Q: Hi! How are you today?
A: ✓ Warm, engaging response

Q: What's your favorite programming language?
A: ✓ Personable, thoughtful
```

**Best For:** Conversational AI, quick responses, resource-limited systems

---

### 3. Llama 2 (Solid General Purpose)

```bash
ollama pull llama2           # 7B version
ollama pull llama2:13b       # 13B version (better)
```

**Profile (7B):**
- Size: 3.8GB
- VRAM Required: 5-8GB
- Speed: 2-3 seconds per response
- Quality: 4/5 stars

**Profile (13B):**
- Size: 6.5GB
- VRAM Required: 10-12GB
- Speed: 3-5 seconds per response
- Quality: 4.5/5 stars

**VEDA Config (7B):**
```env
OLLAMA_MODEL=llama2
TEMPERATURE=0.8
MAX_TOKENS=2000
```

**VEDA Config (13B):**
```env
OLLAMA_MODEL=llama2:13b
TEMPERATURE=0.8
MAX_TOKENS=2500
```

**Example Usage:**
```
Q: What's the difference between Python and JavaScript?
A: ✓ Technical, detailed comparison

Q: Debug this code for me
A: ✓ Good analysis, finds issues
```

**Best For:** Technical questions, research, coding assistance

---

### 4. Phi (Lightweight)

```bash
ollama pull phi
```

**Profile:**
- Size: 1.4GB
- VRAM Required: 2-3GB
- Speed: < 0.5 seconds
- Quality: 3/5 stars
- Best For: Very limited resources

**VEDA Config:**
```env
OLLAMA_MODEL=phi
TEMPERATURE=0.5
MAX_TOKENS=512
```

**Best For:** Old computers, extremely limited resources, edge devices

---

### 5. TinyLlama (Minimal Resource)

```bash
ollama pull tinyllama
```

**Profile:**
- Size: 1.1GB
- VRAM Required: 2GB
- Speed: < 0.5 seconds
- Quality: 2.5/5 stars

**VEDA Config:**
```env
OLLAMA_MODEL=tinyllama
TEMPERATURE=0.3
MAX_TOKENS=512
```

**Best For:** Testing, minimal deployments, learning

---

### 6. Starling-LM (Instruction-Following)

```bash
ollama pull starling-lm
```

**Profile:**
- Size: 4.1GB
- VRAM Required: 5-6GB
- Speed: 1-2 seconds
- Quality: 4/5 stars
- Specialty: Follows instructions precisely

**VEDA Config:**
```env
OLLAMA_MODEL=starling-lm
TEMPERATURE=0.3
MAX_TOKENS=2000
```

**Example Usage:**
```
Q: List 3 benefits of Python in markdown format
A: ✓ Perfect markdown formatting
   ✓ Exactly 3 items
   ✓ Follows format precisely
```

**Best For:** Structured output, complex instructions, templates

---

### 7. Dolphin-Mixtral (Expert-Level)

```bash
ollama pull dolphin-mixtral
```

**Profile:**
- Size: 26GB
- VRAM Required: 24-30GB (GPU recommended)
- Speed: 5-10 seconds per response
- Quality: 5/5 stars
- Expertise: Excellent reasoning, coding, math

**VEDA Config:**
```env
OLLAMA_MODEL=dolphin-mixtral
TEMPERATURE=0.9
MAX_TOKENS=3000
```

**Requirements:**
- GPU with 24GB+ VRAM (NVIDIA RTX 4090+, A100)
- Or 32GB+ system RAM (very slow on CPU)
- Lots of disk space

**Example Usage:**
```
Q: Explain quantum computing with mathematical rigor
A: ✓ PhD-level explanation
   ✓ Correct mathematics
   ✓ Comprehensive

Q: Find bug in complex algorithm
A: ✓ Catches subtle issues
   ✓ Explains root cause
```

**Best For:** Research, advanced coding, complex analysis

---

## 📈 Performance Benchmarks

### Response Time (ms)

```
tinyllama      ████ 300ms
phi            █████ 400ms
neural-chat    ██████ 600ms
mistral        ███████████ 1.5s
llama2         ██████████████ 2s
llama2:13b     ███████████████████ 3.5s
dolphin-mixtral ████████████████████████████ 7s
```

### Output Quality (1-5 stars)

```
tinyllama      ██.5
phi            ███
neural-chat    ████
mistral        ████
llama2         ████
llama2:13b     ████.5
dolphin-mixtral █████
```

### Memory Usage (GB)

```
tinyllama      █ 1.1GB
phi            ██ 1.4GB
neural-chat    ███ 3.6GB
mistral        ████ 4.1GB
llama2         ███.8 3.8GB
llama2:13b     █████.5 6.5GB
dolphin-mixtral ████████████████████████ 26GB
```

---

## 🎛️ Model Parameters Explained

### Temperature (0.0 - 1.0)

Controls randomness in responses.

```env
TEMPERATURE=0.1   # Deterministic (same question → same answer)
TEMPERATURE=0.5   # Balanced (consistent but creative)
TEMPERATURE=0.7   # Recommended (balanced exploration)
TEMPERATURE=1.0   # Creative (varied, sometimes random)
```

**Recommendation for VEDA:** `0.7` (balanced)

### Max Tokens

Maximum length of generated response.

```env
MAX_TOKENS=512    # Short, snappy responses
MAX_TOKENS=1024   # Medium (recommended default)
MAX_TOKENS=2000   # Long-form (research, detailed)
MAX_TOKENS=4000   # Very long (rare)
```

**Recommendation:** `2000` for general use

### Top P (Nucleus Sampling)

Controls diversity of response.

```env
TOP_P=0.9     # Very high quality
TOP_P=0.95    # Recommended
TOP_P=1.0     # Maximum variety
```

### Top K

Filters to top K most likely tokens.

```env
TOP_K=20      # Conservative
TOP_K=40      # Recommended
TOP_K=100     # Exploratory
```

---

## 🔄 Switching Models

### List Available Models

```bash
ollama list
```

### Switch in .env

Simply change:
```env
OLLAMA_MODEL=mistral    # Current
# To:
OLLAMA_MODEL=neural-chat  # New
```

Restart VEDA:
```bash
# Ctrl+C in VEDA terminal
python main.py
```

### Pull New Model First

```bash
ollama pull <model-name>
```

Models are cached locally after first pull.

---

## 🚀 Optimization Tips

### For Fast Responses
```env
OLLAMA_MODEL=neural-chat
TEMPERATURE=0.3
MAX_TOKENS=1024
TOP_P=0.9
```

### For High Quality
```env
OLLAMA_MODEL=llama2:13b
TEMPERATURE=0.7
MAX_TOKENS=2000
TOP_P=0.95
```

### For Creative Output
```env
OLLAMA_MODEL=mistral
TEMPERATURE=0.9
MAX_TOKENS=2000
TOP_P=1.0
```

### For Factual/Consistent
```env
OLLAMA_MODEL=mistral
TEMPERATURE=0.3
MAX_TOKENS=1024
TOP_P=0.9
```

---

## 📊 Hardware Requirements by Model

### CPU Only
- ✅ tinyllama (2GB RAM)
- ✅ phi (2GB RAM)
- ✅ neural-chat (4GB RAM)
- ✅ mistral (4GB RAM)
- ⚠️ llama2 (5GB RAM, slow)
- ❌ dolphin-mixtral (too large)

### GPU Recommended
- ✅ NVIDIA GTX 1660 (6GB) → mistral
- ✅ NVIDIA RTX 2070 (8GB) → llama2
- ✅ NVIDIA RTX 3090 (24GB) → dolphin-mixtral

### GPU Optimal
- ✅ NVIDIA A100 (40GB) → dolphin-mixtral
- ✅ NVIDIA H100 (80GB) → multiple instances

---

## 🧪 Benchmarking Your Setup

### Test a Model

```python
import time
from ollama import OllamaLLM

llm = OllamaLLM(model="mistral", base_url="http://localhost:11434")

start = time.time()
response = llm.invoke("What is Python?")
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
print(f"Token count: ~{len(response.split()) * 1.3:.0f}")
```

### Test All Installed Models

```bash
# Create benchmark_models.py
for model in tinyllama phi neural-chat mistral llama2; do
  echo "Testing $model..."
  ollama run $model "What is machine learning?" --timeout 30
done
```

---

## 🎯 Recommended Configs

### Starter Setup
```env
OLLAMA_MODEL=mistral
TEMPERATURE=0.7
MAX_TOKENS=1024
```

### Conversation Bot
```env
OLLAMA_MODEL=neural-chat
TEMPERATURE=0.5
MAX_TOKENS=1024
```

### Code Assistant
```env
OLLAMA_MODEL=llama2
TEMPERATURE=0.3
MAX_TOKENS=2000
```

### Research Agent
```env
OLLAMA_MODEL=llama2:13b
TEMPERATURE=0.8
MAX_TOKENS=3000
```

### Instruction Following
```env
OLLAMA_MODEL=starling-lm
TEMPERATURE=0.2
MAX_TOKENS=2000
```

---

## 📚 Resources

- **Ollama Model Library**: https://ollama.ai/library
- **Model Cards**: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
- **Benchmark Scores**: https://huggingface.co/spaces/JIndIA/vLLM-Benchmark

---

## ✅ Summary

1. **New to VEDA?** → Use `mistral` (default)
2. **Need speed?** → Use `neural-chat`
3. **Complex tasks?** → Use `llama2:13b` or `dolphin-mixtral`
4. **Low resources?** → Use `phi` or `tinyllama`
5. **Instruction-heavy?** → Use `starling-lm`

**All models are free and run 100% offline!**

---

**Happy model selection! 🚀**
