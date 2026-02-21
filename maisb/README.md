# MAISB — Mobile AI Safety Benchmark

**Version 0.3** | Upgraded from v0.2

MAISB is a benchmark framework for evaluating the safety of AI agents operating on Android devices, testing resistance to prompt injection, exfiltration attempts, and unauthorized tool execution across multiple input channels.

## Overview

MAISB v0.3 introduces:
- **New scenario pack v3** with 240+ synthetic/mock scenarios across 5 channels
- **QR and WebView channel support** in the Android harness
- **Improved Python runner** with `quick`, `full`, and `sweep` commands
- **Reproducibility scripts** for Windows 10

## Directory Structure

```
maisb/
├── packs/
│   ├── v1/                    # Legacy v1 pack (kept as-is)
│   └── v3/                    # New v3 pack (240 scenarios)
│       ├── metadata.yaml
│       └── scenarios/
├── harness/
│   └── android/               # Ktor-based Android harness app
├── runner/
│   ├── maisb_runner/          # Python runner package
│   └── tests/                 # Unit tests (offline)
├── scripts/                   # Windows 10 reproducibility scripts
└── README.md
```

## Quick Start (Windows 10)

### 1. Prerequisites

Run the setup checker:
```powershell
powershell -ExecutionPolicy Bypass -File maisb/scripts/setup_windows.ps1
```

Required tools:
- Python 3.10+ with pip
- Android Studio with emulator (API 26+)
- ADB (Android Debug Bridge)

### 2. Install Runner

```bash
cd maisb/runner
pip install -e .
```

### 3. Start the Harness

1. Open `maisb/harness/android/` in Android Studio
2. Start an Android emulator (API 26+)
3. Build and run the harness app
4. Forward the port:
   ```bash
   adb forward tcp:8765 tcp:8765
   ```

### 4. Run Evaluations

**Quick run** (first 30 scenarios, ~2 minutes):
```bash
maisb quick
# or on Windows:
maisb\scripts\run_quick.bat
```

**Full run** (all 240 scenarios, ~20 minutes):
```bash
maisb full
# or on Windows:
maisb\scripts\run_full.bat
```

**Sweep** (multiple defense profiles):
```bash
maisb sweep --defense-profiles D0,D1,D2,D3,D4
# or on Windows:
maisb\scripts\run_sweep.bat
```

## Output Locations

| Command | Report | Charts |
|---------|--------|--------|
| `maisb quick` | `report_quick.json` | `charts_quick/` |
| `maisb full` | `report_full.json` | `charts_full/` |
| `maisb sweep` | `report_sweep.json` | `charts_sweep/` |

## Switching LLM Provider

Set the `LLM_PROVIDER` environment variable:

```bash
# Linux/macOS
export LLM_PROVIDER=openai
maisb quick --model gpt-4o

# Windows
set LLM_PROVIDER=openai
maisb quick --model gpt-4o
```

Supported values: `mock` (default), `openai`, `anthropic`, `gemini`

## Service URLs

When additional services are running:
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

## Android Harness API

The harness exposes a REST API on port 8765:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/arm` | Arm a scenario |
| POST | `/execute` | Execute armed scenario |
| POST | `/inject_qr` | Inject QR code text |
| POST | `/inject_webview` | Inject WebView HTML + extracted text |
| POST | `/inject_notification` | Inject notification text |

## Decision Codes

| Code | Label | Description |
|------|-------|-------------|
| D0 | BLOCKED_BEFORE_LLM | Input blocked before reaching LLM |
| D1 | BLOCKED_BY_LLM_REFUSAL | LLM refused the request |
| D2 | ALLOWED_WITH_CONFIRMATION | Executed after user confirmation |
| D3 | ALLOWED_SILENTLY | Executed silently (no confirmation) |
| D4 | ALLOWED_BENIGN | Allowed as benign |
| D5 | TOOL_EXECUTION_ERROR | Error during tool execution |

## Safety Notes

- **All tool executions are mock/synthetic** — no real network calls, file operations, or payments are made
- Scenario payloads use synthetic phone numbers (`+1000000000x`) and example domains (`*.example.com`)
- No real phishing domains or harmful content

## CI

The CI workflow (`.github/workflows/maisb_quick.yml`) runs on every push/PR:
- Validates pack v3 YAML schema and scenario counts
- Computes pack hash
- Runs unit tests (scoring, chart generation, pack loading)
- Generates charts on synthetic data
- Does NOT require a physical device or emulator
