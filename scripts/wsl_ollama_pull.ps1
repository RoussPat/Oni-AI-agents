Param(
  [Parameter(Mandatory = $true)]
  [string]$Model,
  [switch]$Tail
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BashScript = Join-Path $ScriptDir 'wsl_ollama_pull.sh'

if (-not (Test-Path $BashScript)) { throw "Missing $BashScript" }

Write-Host "Pulling $Model via Ollama in WSL..." -ForegroundColor Yellow

if ($Tail) {
  wsl -e bash $BashScript $Model -t
} else {
  wsl -e bash $BashScript $Model
}

