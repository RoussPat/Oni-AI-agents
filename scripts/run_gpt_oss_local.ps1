Param(
  [string]$ModelNameOrPath = "/models/gpt-oss",
  [switch]$Detach
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
$ComposeFile = Join-Path $RepoRoot 'runtime/docker-compose.gpt-oss.yml'

# Default envs for local OpenAI-compatible runtime
$env:OPENAI_BASE_URL = "http://localhost:8000/v1"
if (-not $env:OPENAI_MODEL) { $env:OPENAI_MODEL = "gpt-oss" }

Write-Host "Using compose file: $ComposeFile" -ForegroundColor Cyan
Write-Host "OPENAI_BASE_URL=$($env:OPENAI_BASE_URL) OPENAI_MODEL=$($env:OPENAI_MODEL)" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker CLI not found. Please install Docker Desktop."
}

# Always bring up detached so we can run health checks
$upArgs = @('compose','-f', $ComposeFile, 'up', '-d')

# Pass model name/path to vLLM via env override
$env:MODEL_NAME_OR_PATH = $ModelNameOrPath

Write-Host "Starting container with MODEL_NAME_OR_PATH=$ModelNameOrPath ..." -ForegroundColor Yellow
docker @upArgs | Out-Null

# Health check loop (works both for -d and foreground modes)
$healthUrl = "http://localhost:8000/v1/models"
Write-Host "Waiting for health: $healthUrl" -ForegroundColor Yellow

$maxAttempts = 60
for ($i = 1; $i -le $maxAttempts; $i++) {
  try {
    $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 3
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
      Write-Host "Server is healthy." -ForegroundColor Green
      Write-Host ($resp.Content)
      break
    }
  } catch {
    Start-Sleep -Seconds 2
  }
  if ($i -eq $maxAttempts) { throw "Server did not become healthy in time." }
}

if (-not $Detach) {
  Write-Host "Tailing logs. Press Ctrl+C to stop tailing (container keeps running)." -ForegroundColor DarkGray
  docker compose -f $ComposeFile logs -f gpt-oss
}

