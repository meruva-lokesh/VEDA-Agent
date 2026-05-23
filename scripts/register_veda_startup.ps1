$ErrorActionPreference = "Stop"

$TaskName = "VEDA Assistant"
$ProjectRoot = "E:\VEDA PROJECT"
$ScriptPath = Join-Path $ProjectRoot "scripts\start_veda_login.ps1"

if (-not (Test-Path $ScriptPath)) {
    throw "Startup script not found: $ScriptPath"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel LeastPrivilege

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Starts VEDA assistant after Windows login." `
    -Force | Out-Null

Write-Host "Registered startup task: $TaskName"
Write-Host "VEDA will start after you sign in to Windows."
Write-Host "Log file: $ProjectRoot\memory\logs\veda_startup.log"
