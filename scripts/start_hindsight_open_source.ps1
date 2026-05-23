$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\VEDA PROJECT"
Set-Location $ProjectRoot

Write-Host "[VEDA] Starting open-source Hindsight from ghcr.io/vectorize-io/hindsight:latest"
Write-Host "[VEDA] API: http://localhost:8888"
Write-Host "[VEDA] UI : http://localhost:9999"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install Docker Desktop and restart PowerShell."
}

docker compose up -d hindsight

Write-Host "[VEDA] Waiting for Hindsight API..."
for ($i = 1; $i -le 30; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:8888/api/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "[VEDA] Hindsight is ready."
        exit 0
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Warning "[VEDA] Hindsight container started, but health endpoint did not respond yet."
Write-Host "[VEDA] Check with: docker logs hindsight-veda --tail 100"
