@echo off
REM MAISB v0.3 - Sweep Evaluation Run
REM Prerequisites: Android emulator running with harness app, port forwarded

echo === MAISB v0.3 Sweep Run ===
echo.
echo IMPORTANT: Ensure the MAISB harness app is running in Android Studio
echo            and port is forwarded: adb forward tcp:8765 tcp:8765
echo.

cd /d "%~dp0\..\runner"

where maisb >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] maisb CLI not found. Run: pip install -e .
    pause
    exit /b 1
)

REM Sweep over defense profiles D0-D4
echo Running sweep (profiles D0,D1,D2,D3,D4 x 1 repeat each)...
maisb sweep --pack v3 --defense-profiles D0,D1,D2,D3,D4 --repeats 1 --output report_sweep.json --charts-dir charts_sweep

echo.
echo Done! Report: maisb\runner\report_sweep.json
echo Charts: maisb\runner\charts_sweep\
pause
