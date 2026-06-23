# PowerShell Installer for LocalLLM Environment (Conda + llama.cpp)
# Run this script once to set up everything needed to run a local GGUF model.
#
# Usage:
#   cd LocalLLM
#   .\install.ps1
#
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  LocalLLM Environment Installer          " -ForegroundColor Cyan
Write-Host "  Sets up Conda + llama.cpp               " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan


# ----------------------------------------------------------
# 1. Verify Conda is available
# ----------------------------------------------------------
Write-Host "`n[1/4] Checking Conda installation..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version 2>&1
    Write-Host "Found: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "ERROR: 'conda' was not found in your PATH." -ForegroundColor Red
    Write-Host "Please install Miniconda or Anaconda first:" -ForegroundColor Yellow
    Write-Host "  https://docs.anaconda.com/miniconda/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installing, close this terminal, open a fresh one," -ForegroundColor Yellow
    Write-Host "and run this script again." -ForegroundColor Yellow
    Exit 1
}


# ----------------------------------------------------------
# 2. Create (or verify) the LocalLLM conda environment
# ----------------------------------------------------------
Write-Host "`n[2/4] Setting up 'LocalLLM' Conda environment..." -ForegroundColor Yellow

$envList = conda env list 2>&1 | Out-String
if ($envList -match "LocalLLM\s") {
    Write-Host "Environment 'LocalLLM' already exists. Skipping creation." -ForegroundColor Green
} else {
    Write-Host "Creating new Conda environment 'LocalLLM' with Python 3.11..." -ForegroundColor Cyan
    conda create -n LocalLLM python=3.11 -y
    Write-Host "Environment created." -ForegroundColor Green
}


# ----------------------------------------------------------
# 3. Add conda-forge and install llama.cpp
# ----------------------------------------------------------
Write-Host "`n[3/4] Installing llama.cpp from conda-forge..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first install." -ForegroundColor Gray

conda config --add channels conda-forge 2>&1 | Out-Null
conda config --set channel_priority strict 2>&1 | Out-Null

conda install -n LocalLLM llama.cpp -y
Write-Host "llama.cpp installed successfully." -ForegroundColor Green


# ----------------------------------------------------------
# 4. Verify installation
# ----------------------------------------------------------
Write-Host "`n[4/4] Verifying llama-server..." -ForegroundColor Yellow

try {
    $verifyOutput = conda run -n LocalLLM llama-server --version 2>&1 | Out-String
    Write-Host "llama-server is available:" -ForegroundColor Green
    Write-Host $verifyOutput.Trim() -ForegroundColor Gray
} catch {
    Write-Host "WARNING: Could not verify llama-server. It may still work - check manually:" -ForegroundColor Yellow
    Write-Host "  conda activate LocalLLM" -ForegroundColor Gray
    Write-Host "  llama-server --help" -ForegroundColor Gray
}


# ----------------------------------------------------------
# Summary
# ----------------------------------------------------------
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  LocalLLM Installation Complete!         " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Download a GGUF model (e.g. Phi-4 Mini, Qwen3, Llama 3.2)." -ForegroundColor White
Write-Host "     Recommended source: https://huggingface.co" -ForegroundColor Gray
Write-Host "     Suggested folder:   C:\LLMModels\" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Edit the startup script with your model path:" -ForegroundColor White
Write-Host "     .\startLocalLLM.ps1  (update the -m parameter)" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run the server:" -ForegroundColor White
Write-Host "     .\startLocalLLM.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  The API will be available at http://localhost:8080" -ForegroundColor Cyan
Write-Host "  A built-in web chat UI is at  http://localhost:8080/" -ForegroundColor Cyan
Write-Host ""
