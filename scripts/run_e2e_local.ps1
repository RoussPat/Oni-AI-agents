Param()

$ErrorActionPreference = 'Stop'

# Resolve repo root and move there so relative paths work
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RepoRoot

if (-not $env:OPENAI_BASE_URL) {
  Write-Error "OPENAI_BASE_URL is not set. Example: http://127.0.0.1:11435/v1"
  exit 1
}

function Get-HealthUrl([string]$BaseUrl) {
  $trimmed = $BaseUrl.TrimEnd('/')
  if ($trimmed.ToLower().EndsWith('/v1')) {
    return "$trimmed/models"
  } else {
    return "$trimmed/v1/models"
  }
}

$healthUrl = Get-HealthUrl $env:OPENAI_BASE_URL
Write-Host "Checking endpoint: $healthUrl" -ForegroundColor Cyan

try {
  $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 3
  if (-not ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)) {
    Write-Error "Endpoint responded with status $($resp.StatusCode)"
    exit 1
  }
} catch {
  Write-Error "Endpoint not reachable at $healthUrl"
  exit 1
}

# Force chat-completions path for compat servers like Ollama
$env:OPENAI_FORCE_CHAT = '1'

Write-Host "Running pytest -m e2e ..." -ForegroundColor Yellow
python -m pytest -q -m e2e
$code = $LASTEXITCODE

# Pytest returns 5 when no tests were collected; fall back to optional integration smoke
if ($code -eq 5) {
  Write-Host "No e2e tests collected; running optional integration smoke test instead..." -ForegroundColor Yellow
  python -m pytest -q Oni-AI-agents/tests/test_openai_local_runtime.py::test_optional_integration_roundtrip
  $code = $LASTEXITCODE
}

if ($code -ne 0) {
  Write-Error "E2E run failed with exit code $code"
  exit $code
}

Write-Host "E2E run completed successfully." -ForegroundColor Green
exit 0


