Param(
  [Parameter(Mandatory = $true)]
  [string]$ModelRepo
)

$ErrorActionPreference = 'Stop'

# Resolve workspace root relative to this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
$ModelsDir = Join-Path $RepoRoot 'models'
$TargetDir = Join-Path $ModelsDir 'gpt-oss'

Write-Host "Models dir: $ModelsDir"
Write-Host "Target dir: $TargetDir"

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

function Is-RemoteRepo($pathOrRepo) {
  return ($pathOrRepo -match '^[^/]+/[^/]+$') -or ($pathOrRepo -match '^(https?://|git@|hf://)')
}

if (Is-RemoteRepo $ModelRepo) {
  # Download from Hugging Face using git lfs clone (preferred) or snapshot API fallback
  Write-Host "Detected remote repo identifier: $ModelRepo" -ForegroundColor Cyan

  $gitInstalled = (Get-Command git -ErrorAction SilentlyContinue) -ne $null
  if ($gitInstalled) {
    Write-Host "Cloning with git (requires git-lfs for large files)..." -ForegroundColor Yellow
    $env:GIT_LFS_SKIP_SMUDGE = '1'  # avoid huge pulls on clone
    if (-not (Test-Path (Join-Path $TargetDir '.git'))) {
      git init $TargetDir | Out-Null
    }
    Push-Location $TargetDir
    try {
      git remote remove origin 2>$null
    } catch {}
    git remote add origin "https://huggingface.co/$ModelRepo"
    git fetch --depth=1 origin main 2>$null
    git checkout -B main FETCH_HEAD 2>$null
    # Try to fetch specific refs if exist
    git lfs install 2>$null
    git lfs pull 2>$null
    Pop-Location
  } else {
    Write-Host "git not found; attempting snapshot download" -ForegroundColor Yellow
    $snapshotUrl = "https://huggingface.co/api/models/$ModelRepo/snapshots/main"
    $manifest = Invoke-RestMethod -Uri $snapshotUrl -Method Get
    foreach ($file in $manifest.files) {
      $destPath = Join-Path $TargetDir $file.path
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destPath) | Out-Null
      $url = "https://huggingface.co/$ModelRepo/resolve/main/$($file.path)"
      Write-Host "Downloading $($file.path)" -ForegroundColor Cyan
      Invoke-WebRequest -Uri $url -OutFile $destPath
    }
  }
} else {
  # Treat as local path to copy
  $source = Resolve-Path $ModelRepo
  Write-Host "Copying local model from $source" -ForegroundColor Cyan
  robocopy $source $TargetDir /E | Out-Null
}

Write-Host "Model assets ready at $TargetDir" -ForegroundColor Green

