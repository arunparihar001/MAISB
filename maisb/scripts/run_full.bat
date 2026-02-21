@echo off
REM MAISB v0.3 - Full Evaluation Run
REM Prerequisites: Android emulator running with harness app, port forwarded

echo === MAISB v0.3 Full Run ===
echo.
echo IMPORTANT: Ensure the MAISB harness app is running in Android Studio
echo            and port is forwarded: adb forward tcp:8765 tcp:8765
echo.
echo WARNING: Full run evaluates all 240 scenarios. This may take several minutes.
echo.

cd /d "%~dp0\..\runner"

where maisb >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] maisb CLI not found. Run: pip install -e .
    pause
    exit /b 1
)

echo Running full evaluation (240 scenarios, D4 defense)...
maisb full --pack v3 --defense D4 --output report_full.json --charts-dir charts_full

echo.
echo Done! Report: maisb\runner\report_full.json
echo Charts: maisb\runner\charts_full\
pause
