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

# 1. Launch FastAPI Backend in a new window using conda run
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendCmd = "conda run --no-capture-output -n LocalLLM python `"$BackendPath\api.py`""
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 2. Launch Vite React Frontend in a new window
Write-Host "[2/2] Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Yellow
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
