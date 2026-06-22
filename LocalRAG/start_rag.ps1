# PowerShell Startup Script for LocalRAG System
$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "LocalRAG System - Startup Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Launch FastAPI Backend
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendCommand = "conda activate LocalLLM; cd backend; python api.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCommand" -WindowStyle Normal

# 2. Launch Vite React Frontend
Write-Host "[2/2] Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Yellow
$frontendCommand = "cd frontend; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$frontendCommand" -WindowStyle Normal

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "LocalRAG System is starting up!" -ForegroundColor Green
Write-Host "  - Backend Console: running in a new window" -ForegroundColor Cyan
Write-Host "  - Frontend Console: running in a new window" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green

Write-Host "Waiting 3 seconds for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Opening dashboard in your default browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"
