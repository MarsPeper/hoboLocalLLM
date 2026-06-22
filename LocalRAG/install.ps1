# PowerShell Installation Script for LocalRAG System
$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "LocalRAG System - Automated Installer" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check Node.js and NPM
Write-Host "`n[1/4] Checking Node.js and NPM..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "Found Node: $nodeVersion" -ForegroundColor Green
    Write-Host "Found NPM: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "CRITICAL ERROR: Node.js and/or NPM are not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please download and install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Exit 1
}

# 2. Check Conda
Write-Host "`n[2/4] Checking Conda Environment..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version
    Write-Host "Found Conda: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "CRITICAL ERROR: Conda is not installed or not in system PATH." -ForegroundColor Red
    Write-Host "Please install Miniconda or Anaconda and ensure 'conda' is available in your shell." -ForegroundColor Yellow
    Exit 1
}

# Check if LocalLLM environment exists
$envList = conda env list | Out-String
if ($envList -match "LocalLLM\s+") {
    Write-Host "Found existing Conda environment: LocalLLM" -ForegroundColor Green
} else {
    Write-Host "Conda environment 'LocalLLM' not found. Creating it..." -ForegroundColor Cyan
    conda create -n LocalLLM python=3.11 -y
}

# 3. Ensure python/pip are installed in the LocalLLM environment
Write-Host "`n[3/4] Configuring Python and installing backend dependencies..." -ForegroundColor Yellow
Write-Host "Ensuring python=3.11 and pip are installed inside LocalLLM environment..." -ForegroundColor Cyan
conda install -n LocalLLM python=3.11 pip -y

# Install requirements.txt
Write-Host "Installing python packages from backend/requirements.txt..." -ForegroundColor Cyan
conda run -n LocalLLM pip install -r backend/requirements.txt

# 4. Install frontend dependencies
Write-Host "`n[4/4] Installing React frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "LocalRAG Installation Completed successfully!" -ForegroundColor Green
Write-Host "To start the system, run:" -ForegroundColor Green
Write-Host "  .\start_rag.ps1" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
