# MAISB v0.3 Windows Setup Check
# Run as: powershell -ExecutionPolicy Bypass -File setup_windows.ps1

Write-Host "=== MAISB v0.3 Windows Setup Checker ===" -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "  [OK] $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  [MISSING] Python not found. Install from https://python.org/downloads/ (3.10+)" -ForegroundColor Red
}

# Check pip
Write-Host "`nChecking pip..." -ForegroundColor Yellow
try {
    $pipVer = pip --version 2>&1
    Write-Host "  [OK] $pipVer" -ForegroundColor Green
} catch {
    Write-Host "  [MISSING] pip not found. Reinstall Python with pip option enabled." -ForegroundColor Red
}

# Check Node.js
Write-Host "`nChecking Node.js..." -ForegroundColor Yellow
try {
    $nodeVer = node --version 2>&1
    Write-Host "  [OK] Node.js $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "  [MISSING] Node.js not found. Install from https://nodejs.org/" -ForegroundColor Red
}

# Check Docker
Write-Host "`nChecking Docker..." -ForegroundColor Yellow
try {
    $dockerVer = docker --version 2>&1
    Write-Host "  [OK] $dockerVer" -ForegroundColor Green
} catch {
    Write-Host "  [MISSING] Docker not found. Install Docker Desktop from https://docker.com/products/docker-desktop" -ForegroundColor Red
}

# Check ADB
Write-Host "`nChecking ADB (Android Debug Bridge)..." -ForegroundColor Yellow
try {
    $adbVer = adb version 2>&1 | Select-Object -First 1
    Write-Host "  [OK] $adbVer" -ForegroundColor Green
} catch {
    Write-Host "  [MISSING] ADB not found. Install Android Studio or Android SDK Platform Tools." -ForegroundColor Red
    Write-Host "           Download: https://developer.android.com/tools/releases/platform-tools" -ForegroundColor Yellow
}

Write-Host "`n=== Setup Summary ===" -ForegroundColor Cyan
Write-Host "1. Install MAISB runner: cd maisb/runner && pip install -e ." -ForegroundColor White
Write-Host "2. Start Android emulator in Android Studio (API 26+)" -ForegroundColor White
Write-Host "3. Build & run the harness app from maisb/harness/android/ in Android Studio" -ForegroundColor White
Write-Host "4. Forward port: adb forward tcp:8765 tcp:8765" -ForegroundColor White
Write-Host "5. Run: run_quick.bat" -ForegroundColor White
Write-Host "`nOptional URLs once server is running:" -ForegroundColor Yellow
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
