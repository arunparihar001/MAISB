# MAISB Phase 3 — Dashboard + Telemetry Layer

Phase 3 builds the analyst/demo layer on top of the completed Phase 2 trace data.

## Scope

Phase 2 completed:

- Cross-channel trace engine
- Dynamic trust scoring
- Propagation graph generation
- Channel reputation
- Explainable security decisions

Phase 3 adds:

- Browser-based analyst dashboard
- Telemetry summary endpoints
- Decision summary views
- Channel reputation views
- Trace timeline views
- Trace graph retrieval for dashboard visualizations
- JSON/CSV export
- Basic incident notes for demo/SOC workflows

## Files to add

```text
maisb/llm_proxy/api/phase3_dashboard.py
tools/apply_phase3_patch.py
docs/PHASE3_TEST_COMMANDS.ps1
SCAN_API_PHASE3_INSERTS.md
README_PHASE3_PASTE_GUIDE.md
FILE_TREE.txt
```

## Where to paste

Extract this ZIP into:

```text
E:\projects\maisb-monorepo
```

The main Phase 3 file should end up here:

```text
E:\projects\maisb-monorepo\maisb\llm_proxy\api\phase3_dashboard.py
```

## Apply integration

From repo root:

```powershell
cd E:\projects\maisb-monorepo
python tools\apply_phase3_patch.py
```

This modifies:

```text
maisb/llm_proxy/api/scan_api.py
```

and creates a backup:

```text
maisb/llm_proxy/api/scan_api.py.phase3_backup
```

## Start local API

```powershell
cd E:\projects\maisb-monorepo\maisb\llm_proxy
.\.venv\Scripts\Activate.ps1
uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload
```

## Test Phase 3

```powershell
Invoke-RestMethod http://127.0.0.1:8001/v1/phase3/health | ConvertTo-Json -Depth 10
```

Expected:

```json
{
  "status": "ok",
  "phase3": true,
  "phase3_complete": true,
  "version": "2.3.0"
}
```

## Open dashboard

Open this in your browser:

```text
http://127.0.0.1:8001/dashboard
```

Use:

```text
Admin Key: change_me_in_production
Tenant ID: default
Window Hours: 24
```

## Run full test script

```powershell
cd E:\projects\maisb-monorepo
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\docs\PHASE3_TEST_COMMANDS.ps1
```

## New endpoints

```text
GET  /dashboard
GET  /v1/phase3/health
GET  /v1/dashboard/summary
GET  /v1/dashboard/decisions
GET  /v1/dashboard/channels
GET  /v1/dashboard/recent-traces
GET  /v1/dashboard/timeline
GET  /v1/dashboard/trace-graph/{trace_id}
GET  /v1/dashboard/export
POST /v1/dashboard/incidents
POST /v1/dashboard/incidents/{incident_id}/status
```

## Git commands

```powershell
cd E:\projects\maisb-monorepo
git checkout -b phase3-dashboard-telemetry
git add maisb/llm_proxy/api/phase3_dashboard.py tools/apply_phase3_patch.py docs/PHASE3_TEST_COMMANDS.ps1 SCAN_API_PHASE3_INSERTS.md README_PHASE3_PASTE_GUIDE.md FILE_TREE.txt
git add maisb/llm_proxy/api/scan_api.py
git commit -m "Add Phase 3 dashboard telemetry layer"
```

## Railway

No new dependency is required.

Keep Railway:

```text
Root Directory: /maisb/llm_proxy
Start Command: uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
```

After deploy:

```powershell
Invoke-RestMethod https://maisb-production.up.railway.app/v1/phase3/health | ConvertTo-Json -Depth 10
```

Then open:

```text
https://maisb-production.up.railway.app/dashboard
```

Use a real Railway environment variable for ADMIN_KEY before public demos.
