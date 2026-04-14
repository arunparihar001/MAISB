# MAISB — Mobile AI Safety Benchmark

End-to-end evaluation framework for **MAISB v0.3.0** with the **v4** scenario pack, **410 scenarios**, **6 channels**, and **D0–D5** defense profiles.

MAISB evaluates the safety of AI agents operating on Android devices against prompt injection, goal-shift attempts, exfiltration attempts, and unauthorized tool execution across multiple untrusted input channels.

## What is in this repository

- **Android harness** (`maisb/harness/android/`)  
  Kotlin/Ktor Android app that runs on an emulator or device and exposes a local HTTP API for scenario injection and execution.

- **Scenario packs** (`maisb/packs/`)  
  Benchmark packs used by the runner. The current release includes **v4**, which contains **410 scenarios** across **clipboard, deep link, QR, notification, share, and WebView** channels.

- **Python runner** (`maisb/runner/`)  
  CLI for quick runs, full runs, sweeps, scoring, and chart generation.

- **LLM proxy** (`maisb/llm_proxy/main.py`)  
  FastAPI proxy that evaluates requests under defense profiles **D0, D1, D2, D3, D4, and D5**.

- **Enterprise tool proxy** (`maisb/llm_proxy/enterprise_proxy.py`)  
  Optional proxy for testing enterprise detectors such as **Lakera Guard** and **Guardrails AI** under the MAISB workflow.

- **Dashboard backend** (`maisb/dashboard/backend/`)  
  FastAPI backend for reading generated reports and exposing them through a REST API.

- **Dashboard frontend** (`maisb/dashboard/frontend/`)  
  Vite + React dashboard for viewing aggregate metrics and channel breakdowns.

- **Helper scripts** (`maisb/scripts/`)  
  Windows helpers for setup and reproducible benchmark runs.

---

## v4 pack summary

- **Pack version:** `v4`
- **Pack SHA-256:** `befbd4dfff839fb3fa222f0812cbc7e401a380e0112ac0d9585d057139c6ee0b`
- **Scenario count:** `410`
- **Attack / benign split:** `260 attack` / `150 benign`
- **Channels:** `6`

### Channel distribution

- Clipboard: **80**
- Deep link: **70**
- QR: **70**
- Notification: **70**
- Share: **60**
- WebView: **60**

---

## Repository structure

```text
maisb/
├── dashboard/
│   ├── backend/
│   └── frontend/
├── harness/
│   └── android/
├── llm_proxy/
│   ├── main.py
│   └── enterprise_proxy.py
├── packs/
│   ├── v1/
│   ├── v3/
│   └── v4/
│       ├── manifest.json
│       └── SHA256SUMS
├── runner/
├── scripts/
└── README.md
```

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---:|---|
| Python | 3.10 | Required for the runner and API services |
| pip | bundled with Python | Package installer |
| Java (JDK) | 17 | Required for the Android harness |
| Android Studio | Hedgehog / newer | For building and running the harness |
| Android emulator image | API 26+ | Android 8.0 or higher |
| ADB | bundled with Android Studio | Needed for port forwarding |
| Node.js | 18 LTS | Optional, only for frontend development |
| Docker | 24 | Optional, only for containerised dashboard runs |

> On macOS/Linux, use `python3` instead of `python` where needed.

---

## Install the runner

```bash
cd maisb/runner
pip install -e .
maisb --version
```

Expected version:

```text
maisb, version 0.3.0
```

---

## Start the Android harness

1. Open `maisb/harness/android/` in Android Studio.
2. Start an emulator with **API 26 or higher**.
3. Build and run the harness app.
4. Forward the harness port to your machine:

```bash
adb forward tcp:8765 tcp:8765
```

Health check:

```bash
curl http://localhost:8765/health
```

---

## Run evaluations

### Quick run

```bash
cd maisb/runner
maisb quick --pack v4 --defense D4 --output report_quick.json --charts-dir charts_quick
```

### Full run

```bash
cd maisb/runner
maisb full --pack v4 --defense D4 --output report_full.json --charts-dir charts_full
```

### Defense sweep

```bash
cd maisb/runner
maisb sweep --pack v4 --defense-profiles D0,D1,D2,D3,D4,D5 --repeats 1 --output report_sweep.json --charts-dir charts_sweep
```

---

## Defense profiles

| Profile | Meaning |
|---|---|
| D0 | Baseline / minimal defense |
| D1 | LLM refusal-oriented defense |
| D2 | Confirmation-oriented defense |
| D3 | Silent allow / weaker guardrail path |
| D4 | Stronger benign-action handling |
| D5 | Enterprise-tool proxy / external detector path |

---

## LLM proxy

The default proxy lives at:

```text
maisb/llm_proxy/main.py
```

It exposes a FastAPI app and supports the MAISB `/complete` flow with defense profiles **D0–D5**.

Example local run:

```bash
cd maisb/llm_proxy
uvicorn main:app --host 0.0.0.0 --port 9000
```

---

## Enterprise proxy

The enterprise proxy is a drop-in alternative for benchmarking external or self-hosted security tools in the MAISB pipeline.

Supported tools currently documented in the repo:

- **Lakera Guard**
- **Guardrails AI**

Example:

```powershell
$env:ENTERPRISE_TOOL = "lakera"
$env:LAKERA_API_KEY = "your_key_here"
uvicorn enterprise_proxy:app --host 0.0.0.0 --port 9000
```

Then run MAISB against it, for example:

```bash
cd maisb/runner
maisb full --host 127.0.0.1 --port 8765 --defense D5 --model lakera-guard --output report_D5_lakera_r1.json --pack v4
```

---

## Reports and charts

Typical outputs written by the runner:

- `report_quick.json`
- `report_full.json`
- `report_sweep.json`
- `charts_quick/`
- `charts_full/`
- `charts_sweep/`

---

## Dashboard

After generating reports, you can start the dashboard stack:

```bash
cd maisb
docker compose up --build
```

Typical local URLs:

- Backend API: `http://localhost:8000/docs`
- Frontend dashboard: `http://localhost:5173`

---

## Windows helper scripts

Windows users can check local dependencies with:

```powershell
powershell -ExecutionPolicy Bypass -File maisb\scripts\setup_windows.ps1
```

---

## Testing

```bash
cd maisb/runner
pip install -e .
python -m pytest tests/ -v
```

---

## Safety notes

- Scenario content is synthetic and benchmark-oriented.
- The framework is intended for controlled evaluation of agent safety behavior.
- Review your environment variables and proxies before running against non-mock providers.

---

## Release checklist for this repo

Before pushing a clean public release, make sure you have:

- `maisb/packs/v4/manifest.json`
- `maisb/packs/v4/SHA256SUMS`
- `maisb/runner/`
- `maisb/llm_proxy/main.py`
- `maisb/llm_proxy/enterprise_proxy.py`
- `README.md`

---

## License

Add your preferred license file if you want the repository to be reusable by others.
