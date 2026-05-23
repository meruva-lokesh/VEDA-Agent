@echo off
REM ════════════════════════════════════════════════════════════════════════════════
REM start_veda.bat — Bootstrap VEDA with Hindsight memory server
REM ════════════════════════════════════════════════════════════════════════════════

echo.
echo [VEDA] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [VEDA] Starting VEDA Assistant with Hindsight Agent Memory
echo [VEDA] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM ── Step 1: Check if Docker is running ───────────────────────────────────────────
echo [VEDA] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [VEDA] ERROR: Docker not found. Please install Docker Desktop.
    echo [VEDA] Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM ── Step 2: Start or create Hindsight container ─────────────────────────────────
echo [VEDA] Starting Hindsight memory server...

REM Check if hindsight-veda container is already running
docker ps --filter name=hindsight-veda --filter status=running --format "{{.Names}}" | find "hindsight-veda" >nul 2>&1

if errorlevel 1 (
    REM Container not running, try to start it
    docker start hindsight-veda 2>nul
    
    if errorlevel 1 (
        REM Container doesn't exist, create it
        echo [VEDA] Creating Hindsight container for first time...
        docker run -d ^
          --name hindsight-veda ^
          -p 8888:8888 ^
          -p 9999:9999 ^
          -e HINDSIGHT_API_LLM_PROVIDER=ollama ^
          -e HINDSIGHT_API_LLM_API_KEY=ollama ^
          -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 ^
          -e HINDSIGHT_API_LLM_MODEL=gemma2:2b ^
          -v hindsight_data:/home/hindsight/.pg0 ^
          ghcr.io/vectorize-io/hindsight:latest
        
        if errorlevel 1 (
            echo [VEDA] WARNING: Could not create Hindsight container
            echo [VEDA] VEDA will run without long-term memory
            echo [VEDA] To fix: make sure you have internet for image pull
        ) else (
            echo [VEDA] ✓ Hindsight container created
        )
    ) else (
        echo [VEDA] ✓ Hindsight container started
    )
) else (
    echo [VEDA] ✓ Hindsight already running
)

timeout /t 3 /nobreak >nul

REM ── Step 3: Verify Hindsight is responding ──────────────────────────────────────
echo [VEDA] Verifying Hindsight at http://localhost:8888...
powershell -Command "try { $null = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8888/api/health' -ErrorAction Stop; Write-Host '[VEDA] Hindsight responding'; exit 0 } catch { Write-Host '[VEDA] WARNING: Hindsight not yet responding (will retry)'; exit 1 }" 2>nul

REM ── Step 4: Start VEDA Python application ───────────────────────────────────────
echo [VEDA] Starting VEDA Python application...
echo [VEDA] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python main_new.py

REM ── Cleanup ─────────────────────────────────────────────────────────────────────
echo.
echo [VEDA] VEDA session ended. Hindsight container remains running.
echo [VEDA] To stop: docker stop hindsight-veda
echo.
pause
