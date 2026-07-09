# PowerShell Startup Script for LocalRAG System
# Must be run from the LocalRAG directory
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  LocalRAG System - Startup Launcher     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Resolve absolute paths for the subshells
$BackendPath = Join-Path $ScriptDir "backend"
$FrontendPath = Join-Path $ScriptDir "frontend"
$ParentPath = Split-Path -Parent $ScriptDir
$ComposePath = Join-Path $ParentPath "docker-compose.yml"

# 1. Start Docker Compose Stack (Qdrant, Prometheus, Grafana)
Write-Host "`n[1/3] Checking Docker Compose services..." -ForegroundColor Yellow
if (Test-Path $ComposePath) {
    # Temporarily suspend ErrorActionPreference to prevent native command warnings on stderr from throwing exceptions
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    
    & docker info > $null 2>&1
    $dockerCheck = $LASTEXITCODE
    
    $ErrorActionPreference = $oldEAP

    if ($dockerCheck -ne 0) {
        Write-Error "Docker daemon is not running! Please start Docker Desktop and try again."
        exit 1
    }
    Write-Host "Starting Docker Compose services (Qdrant, Prometheus, Grafana)..." -ForegroundColor Gray
    & docker compose -f $ComposePath up -d
} else {
    Write-Host "docker-compose.yml not found in parent directory. Skipping..." -ForegroundColor DarkYellow
}

# 2. Launch FastAPI Backend in a new window using conda run
Write-Host "`n[2/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendCmd = "conda run --no-capture-output -n LocalLLM python `"$BackendPath\api.py`""
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 3. Launch Vite React Frontend in a new window
Write-Host "[3/3] Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Yellow
$frontendCmd = "Set-Location `"$FrontendPath`"; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "  LocalRAG System starting up!           " -ForegroundColor Green
Write-Host "  Backend  -> http://localhost:8000      " -ForegroundColor Cyan
Write-Host "  Frontend -> http://localhost:5173      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green

Write-Host "`nWaiting 5 seconds for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Opening LocalRAG dashboard in your browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"
