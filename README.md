# maisb-monorepo

End-to-end evaluation framework for Mobile AI Security Benchmark (MAISB) v0.3.
It consists of:

- **Android harness** (`maisb/harness/android/`) – a Kotlin/Ktor app that runs on an Android emulator and exposes a local HTTP server.
- **Scenario packs** (`maisb/packs/`) – YAML scenario files (v1 and v3).
- **Python runner** (`maisb/runner/`) – CLI tool that drives the harness, scores results, and produces JSON reports and charts.
- **Dashboard backend** (`maisb/dashboard/backend/`) – FastAPI server that reads evaluation reports and exposes them as a REST API (port 8000, `/docs` for Swagger UI).
- **Dashboard frontend** (`maisb/dashboard/frontend/`) – Vite + React SPA that visualises metrics and channel-breakdown tables (port 5173).
- **Docker Compose** (`maisb/docker-compose.yml`) – one-command startup for the dashboard (backend + frontend).
- **Helper scripts** (`maisb/scripts/`) – Windows `.bat` wrappers and a PowerShell setup checker.

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|-----------------|-------|
| Python | 3.10 | <https://python.org/downloads/> |
| pip | bundled with Python | — |
| Java (JDK) | 17 | <https://adoptium.net/> – required to build the Android harness |
| Android Studio | Hedgehog (2023.1) or newer | <https://developer.android.com/studio> |
| Android emulator image | API 26 (Android 8.0) or higher | via Android Studio SDK Manager |
| ADB (Android Debug Bridge) | bundled with Android Studio | or <https://developer.android.com/tools/releases/platform-tools> |
| Node.js | 18 LTS *(optional)* | Required only if running a frontend/API server; not needed for CLI evaluation |
| Docker | 24 *(optional)* | Required only for containerised deployments; not needed for CLI evaluation |

> **macOS / Linux users**: all Python and ADB steps below work the same way; substitute `python3` for `python` if needed. The `.bat` scripts are Windows-only – use the equivalent `maisb` CLI commands shown in each section instead.

---

## Step 1 – Install the Python runner

```bash
# From the repository root
cd maisb/runner
pip install -e .
```

Verify the installation:

```bash
maisb --version
# maisb, version 0.3.0
```

---

## Step 2 – Build and launch the Android harness

1. Open **Android Studio**.
2. Choose **Open** → select the folder `maisb/harness/android/` (the directory that contains `build.gradle.kts`).
3. Let Gradle sync finish.
4. In the **Device Manager** panel, create (or start) an emulator with **API level 26 or higher** (e.g. Pixel 6, API 34).
5. Click **Run ▶** to build and install the `MaisbHarness` app on the emulator.
6. The app will start a local HTTP server on port **8765** inside the emulator.

---

## Step 3 – Forward the harness port to your laptop

With the emulator running, open a terminal and run:

```bash
adb forward tcp:8765 tcp:8765
```

You can verify the harness is reachable from your laptop:

```bash
# Should return {"status":"ok"} or similar
curl http://localhost:8765/health
```

---

## Step 4 – Run an evaluation

### Quick run (first 30 scenarios, ~1–2 min)

**Windows:**
```bat
cd maisb\scripts
run_quick.bat
```

**macOS / Linux (or any platform):**
```bash
cd maisb/runner
maisb quick --pack v3 --defense D4 --output report_quick.json --charts-dir charts_quick
```

Output files are written inside `maisb/runner/`:
- `report_quick.json` – full JSON report
- `charts_quick/` – PNG charts

### Full run (all 240 scenarios, ~10–15 min)

**Windows:**
```bat
cd maisb\scripts
run_full.bat
```

**macOS / Linux:**
```bash
cd maisb/runner
maisb full --pack v3 --defense D4 --output report_full.json --charts-dir charts_full
```

### Defense-profile sweep (D0–D4 across all scenarios)

**Windows:**
```bat
cd maisb\scripts
run_sweep.bat
```

**macOS / Linux:**
```bash
cd maisb/runner
maisb sweep --pack v3 --defense-profiles D0,D1,D2,D3,D4 --repeats 1 \
    --output report_sweep.json --charts-dir charts_sweep
```

---

## Dashboard (Docker Compose)

After you have run at least one evaluation (so report files exist in `maisb/runner/`),
start the full dashboard stack with a single command:

```bash
cd maisb
docker compose up --build
```

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | <http://localhost:8000/docs> | Swagger UI / REST API |
| Frontend dashboard | <http://localhost:5173> | React metrics dashboard |

The backend reads all `report_*.json` files from `maisb/runner/` (mounted read-only).
The frontend fetches from the backend and displays:

- Overall metrics cards (attack detection rate, false positive rate, accuracy)
- Per-scenario counts (TP / FP / FN)
- Per-channel breakdown table

To stop the stack:

```bash
docker compose down
```

### Running the frontend in development mode (no Docker)

```bash
cd maisb/dashboard/frontend
npm install
npm run dev          # http://localhost:5173
```

Make sure the backend is also running:

```bash
cd maisb/dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000
```

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `mock` | LLM backend used during evaluation. Set to your provider name to use a real model. |

---

## Windows quick-start check

A PowerShell script is provided to verify that all required tools are installed:

```powershell
powershell -ExecutionPolicy Bypass -File maisb\scripts\setup_windows.ps1
```

It checks for Python, pip, Node.js, Docker, and ADB, and prints guidance for anything that is missing.

---

## Running the tests

```bash
cd maisb/runner
pip install -e .
python -m pytest tests/ -v
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `[ERROR] Cannot reach harness at localhost:8765` | Ensure the emulator is running, the harness app is open, and you have run `adb forward tcp:8765 tcp:8765`. |
| `[ERROR] maisb CLI not found` | Run `pip install -e .` from `maisb/runner/`. |
| Gradle sync fails in Android Studio | Make sure JDK 17 is selected in **File → Project Structure → SDK Location → Gradle JDK**. |
| `adb: command not found` | Add the Android SDK `platform-tools` directory to your `PATH`, or install it via Android Studio's SDK Manager. |