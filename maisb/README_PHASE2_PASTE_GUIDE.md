# MAISB Phase 2 — Cross-Channel Trace Engine Patch

This patch implements the next Phase 2 step after the Phase 1 enterprise backend.

## What Phase 2 adds

- Cross-channel trace engine
- Trace ID propagation
- Payload journey tracking
- Supply-chain / propagation graph
- Dynamic trust scoring
- Channel reputation
- Structured decision explanations
- Integration hook for `/v1/scan`

Target flow:

```text
PDF/File -> OCR/Text Extraction -> Clipboard -> Browser/WebView -> Agent -> LLM
```

## Why this patch is self-contained

Your final Phase 1 Railway deployment uses:

```text
Railway Root Directory: /maisb/llm_proxy
Start Command: uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
```

So the live API should use:

```text
maisb/llm_proxy/api/phase2_trace.py
```

This avoids depending on imports from `maisb/core` during Railway deployment.

The modular `maisb/core/tracing`, `maisb/core/trust`, and `maisb/core/explainability` files are also included for future refactor, documentation, and cleaner architecture later.

## Files to add

```text
maisb/llm_proxy/api/phase2_trace.py
maisb/core/tracing/__init__.py
maisb/core/tracing/channel_trace.py
maisb/core/tracing/trust_chain.py
maisb/core/tracing/propagation_graph.py
maisb/core/trust/__init__.py
maisb/core/trust/trust_scores.py
maisb/core/trust/channel_trust.py
maisb/core/trust/reputation_engine.py
maisb/core/explainability/__init__.py
maisb/core/explainability/decision_reasoning.py
maisb/core/explainability/risk_explanations.py
maisb/core/explainability/trace_explanations.py
tools/apply_phase2_patch.py
docs/PHASE2_TEST_COMMANDS.ps1
SCAN_API_PHASE2_INSERTS.md
```

## Apply integration

From repo root:

```powershell
cd E:\projects\maisb-monorepo
python tools\apply_phase2_patch.py
```

This modifies:

```text
maisb/llm_proxy/api/scan_api.py
```

and creates a backup:

```text
maisb/llm_proxy/api/scan_api.py.phase2_backup
```

## Start API

```powershell
cd E:\projects\maisb-monorepo\maisb\llm_proxy
.\.venv\Scripts\Activate.ps1
uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload
```

## Test health

```powershell
Invoke-RestMethod http://127.0.0.1:8001/v1/phase2/health | ConvertTo-Json -Depth 10
```

Expected:

```json
{
  "status": "ok",
  "phase2": true,
  "phase2_complete": true,
  "features": {
    "cross_channel_trace": true,
    "dynamic_trust_scoring": true,
    "propagation_graph": true,
    "decision_explanations": true,
    "channel_reputation": true
  }
}
```

## Run all tests

```powershell
cd E:\projects\maisb-monorepo
.\docs\PHASE2_TEST_COMMANDS.ps1
```

## New endpoints

```text
GET  /v1/phase2/health
POST /v1/trace/payload
GET  /v1/trace/{trace_id}
POST /v1/trace/{trace_id}/event
GET  /v1/trace/{trace_id}/supply-chain
POST /v1/trust/score
GET  /v1/trust/channels
POST /v1/explain/decision
GET  /v1/explain/{trace_id}
```

## Git commands

```powershell
cd E:\projects\maisb-monorepo
git checkout -b phase2-cross-channel-trace
git add maisb/llm_proxy/api/phase2_trace.py maisb/core/tracing maisb/core/trust maisb/core/explainability tools/apply_phase2_patch.py docs/PHASE2_TEST_COMMANDS.ps1 SCAN_API_PHASE2_INSERTS.md
git add maisb/llm_proxy/api/scan_api.py
git commit -m "Add Phase 2 cross-channel trace engine"
```

## Railway

After local test passes, push branch or merge to main. Railway should keep:

```text
Root Directory: /maisb/llm_proxy
Start Command: uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
Healthcheck: /health
```

No new dependency is required.
