Param(
  [int]$Port = 11435,
  [switch]$Foreground
)

$ErrorActionPreference = 'Stop'

function Invoke-WSLCommand([string]$Command) {
  wsl -e bash -lc $Command
}

Write-Host "Starting Ollama in WSL on port $Port ..." -ForegroundColor Cyan

# Ensure Ollama exists; attempt install if missing
$check = Invoke-WSLCommand "command -v ollama >/dev/null 2>&1; echo $?"
if ($check.Trim() -ne '0') {
  Write-Host "Ollama not found in WSL; attempting installation..." -ForegroundColor Yellow
  Invoke-WSLCommand "curl -fsSL https://ollama.com/install.sh | sh" | Out-Null
}

# Start server
$envLine = "export OLLAMA_HOST=127.0.0.1:$Port"
if ($Foreground) {
  Write-Host "Running in foreground..." -ForegroundColor Yellow
  Invoke-WSLCommand "$envLine; exec ollama serve"
} else {
  Write-Host "Starting in background..." -ForegroundColor Yellow
  Invoke-WSLCommand "$envLine; nohup ollama serve >/tmp/ollama_$Port.log 2>&1 & disown; sleep 1"

  # Health check loop
  $healthUrl = "http://127.0.0.1:$Port/api/tags"
  $maxAttempts = 60
  for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 3
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        Write-Host "Ollama is up on $healthUrl" -ForegroundColor Green
        break
      }
    } catch {
      Start-Sleep -Seconds 2
    }
    if ($i -eq $maxAttempts) { throw "Ollama did not become healthy on port $Port in time." }
  }
}



