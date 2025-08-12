Param(
  [string]$Model = "gpt-oss:20b",
  [int]$Port = 11435
)

$ErrorActionPreference = 'Stop'

function Invoke-WSLCommand([string]$Command) {
  wsl -e bash -lc $Command
}

Write-Host "Pulling model '$Model' via Ollama in WSL (port $Port) ..." -ForegroundColor Cyan

$envLine = "export OLLAMA_HOST=127.0.0.1:$Port"
Invoke-WSLCommand "$envLine; ollama pull $Model"

Write-Host "Model '$Model' is available." -ForegroundColor Green


