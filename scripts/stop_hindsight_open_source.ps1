$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\VEDA PROJECT"
Set-Location $ProjectRoot

docker compose stop hindsight
Write-Host "[VEDA] Hindsight stopped."
