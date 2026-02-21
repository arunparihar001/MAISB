@echo off
REM MAISB v0.3 - Quick Evaluation Run
REM Prerequisites: Android emulator running with harness app, port forwarded

echo === MAISB v0.3 Quick Run ===
echo.
echo IMPORTANT: Ensure the MAISB harness app is running in Android Studio
echo            and port is forwarded: adb forward tcp:8765 tcp:8765
echo.

cd /d "%~dp0\..\runner"

REM Check if maisb CLI is available
where maisb >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] maisb CLI not found. Run: pip install -e .
    pause
    exit /b 1
)

echo Running quick evaluation (first 30 scenarios, D4 defense)...
maisb quick --pack v3 --defense D4 --output report_quick.json --charts-dir charts_quick

echo.
echo Done! Report: maisb\runner\report_quick.json
echo Charts: maisb\runner\charts_quick\
pause
