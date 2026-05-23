$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\VEDA PROJECT"
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "memory\logs"
$StartupLog = Join-Path $LogDir "veda_startup.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectRoot

"[$(Get-Date -Format s)] Starting VEDA from Windows logon task" | Out-File -FilePath $StartupLog -Append -Encoding utf8

& $PythonExe "main_new.py" *>> $StartupLog
