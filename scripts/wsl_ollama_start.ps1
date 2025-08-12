Param(
  [switch]$ShowLogs
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BashScript = Join-Path $ScriptDir 'wsl_ollama_start.sh'

if (-not (Test-Path $BashScript)) { throw "Missing $BashScript" }

Write-Host "Starting Ollama in WSL..." -ForegroundColor Yellow
wsl -e bash $BashScript

if ($ShowLogs) {
  Write-Host "Showing last 50 log lines from WSL (if available)" -ForegroundColor DarkGray
  wsl -e bash -lc 'tail -n 50 /tmp/ollama_11435.log || true'
}

