#!/bin/bash

# start_veda.sh — Bootstrap VEDA with Hindsight memory server (macOS/Linux)

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Starting VEDA Assistant with Hindsight Agent Memory  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check if Docker is installed ──────────────────────────────────
echo "[VEDA] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "[VEDA] ERROR: Docker not found. Please install Docker."
    echo "[VEDA] Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# ── Step 2: Check if Ollama is running ────────────────────────────────────
echo "[VEDA] Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[VEDA] WARNING: Ollama not responding at localhost:11434"
    echo "[VEDA] Please start Ollama with: ollama serve"
    echo "[VEDA] Or install from: https://ollama.ai"
    read -p "[VEDA] Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# ── Step 3: Start or create Hindsight container ────────────────────────────
echo "[VEDA] Starting Hindsight memory server..."

if docker ps --filter name=hindsight-veda --filter status=running --format "{{.Names}}" | grep -q "hindsight-veda"; then
    echo "[VEDA] ✓ Hindsight already running"
else
    # Try to start existing container
    if docker start hindsight-veda 2>/dev/null; then
        echo "[VEDA] ✓ Hindsight container started"
    else
        # Create new container
        echo "[VEDA] Creating Hindsight container for first time..."
        docker run -d \
          --name hindsight-veda \
          -p 8888:8888 \
          -e HINDSIGHT_API_LLM_API_KEY=ollama \
          -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 \
          -e HINDSIGHT_API_LLM_MODEL=gemma2:2b \
          ghcr.io/vectorize-io/hindsight
        
        if [ $? -eq 0 ]; then
            echo "[VEDA] ✓ Hindsight container created"
        else
            echo "[VEDA] WARNING: Could not create Hindsight container"
            echo "[VEDA] VEDA will run without long-term memory"
        fi
    fi
fi

sleep 3

# ── Step 4: Verify Hindsight is responding ────────────────────────────────
echo "[VEDA] Verifying Hindsight at http://localhost:8888..."
if curl -s http://localhost:8888/api/health > /dev/null 2>&1; then
    echo "[VEDA] ✓ Hindsight responding"
else
    echo "[VEDA] WARNING: Hindsight not yet responding (will retry)"
fi

# ── Step 5: Activate Python virtual environment ────────────────────────────
echo "[VEDA] Activating Python virtual environment..."

if [ ! -d "venv" ]; then
    echo "[VEDA] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# ── Step 6: Start VEDA Python application ──────────────────────────────────
echo "[VEDA] Starting VEDA Python application..."
echo "╔════════════════════════════════════════════════════════╗"
echo ""

python main_new.py

# ── Cleanup ────────────────────────────────────────────────────────────────
echo ""
echo "[VEDA] VEDA session ended. Hindsight container remains running."
echo "[VEDA] To stop: docker stop hindsight-veda"
echo ""
