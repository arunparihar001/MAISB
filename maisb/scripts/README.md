# MAISB v0.3 Scripts

Helper scripts for running MAISB evaluations on Windows 10.

## Prerequisites

Before running any scripts, ensure:

1. **Android Studio** is installed with an emulator (API 26+)
2. **MAISB Harness** is built and running on the emulator
3. **Port forwarded**: `adb forward tcp:8765 tcp:8765`
4. **MAISB Runner** is installed: `cd maisb/runner && pip install -e .`

## Scripts

### `setup_windows.ps1`
Checks that required tools (Python, Node, Docker, ADB) are available and prints guidance.

```powershell
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

### `run_quick.bat`
Runs the quick evaluation: first 30 scenarios from v3 pack (sorted by id), defense D4.

- Output: `maisb/runner/report_quick.json`
- Charts: `maisb/runner/charts_quick/`

### `run_full.bat`
Runs the full evaluation: all 240 scenarios from v3 pack, defense D4.

- Output: `maisb/runner/report_full.json`
- Charts: `maisb/runner/charts_full/`

### `run_sweep.bat`
Sweeps defense profiles D0–D4 across all scenarios.

- Output: `maisb/runner/report_sweep.json`
- Charts: `maisb/runner/charts_sweep/`

## Notes

- **No auto-start**: Scripts do NOT automatically start the emulator. Start it manually in Android Studio.
- **Mock tools only**: All tool executions are synthetic/mock - no real network calls or file operations.
- **LLM Provider**: Set the `LLM_PROVIDER` environment variable to switch providers (default: `mock`).
