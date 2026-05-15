# Phase 2 scan_api.py integration snippets

Use the automatic patch first:

```powershell
cd E:\projects\maisb-monorepo
python tools\apply_phase2_patch.py
```

If you prefer manual integration, apply these changes.

## 1. Add import near the top of scan_api.py

```python
from api.phase2_trace import router as phase2_router, record_scan_trace_safe
```

## 2. Include router after existing app.include_router(...) lines

```python
app.include_router(phase2_router)
```

## 3. Add this field to ScanRequestBody

```python
previous_trace_id: str | None = None
```

## 4. Add this field to ScanResponseBody

```python
trace_id: str | None = None
```

## 5. Inside /v1/scan, after final_decision is known and before return ScanResponseBody(...), add:

```python
phase2_trace_id = record_scan_trace_safe(
    tenant_id=tenant_id if "tenant_id" in locals() else getattr(body, "tenant_id", "default"),
    payload=body.payload,
    channel=body.channel,
    objective=body.objective,
    decision=final_decision if "final_decision" in locals() else result.decision,
    risk_score=result.risk_score,
    taxonomy_class=result.taxonomy_class,
    previous_trace_id=getattr(body, "previous_trace_id", None),
    session_id=getattr(body, "session_id", None),
)
```

## 6. Add trace_id to ScanResponseBody return

```python
trace_id = phase2_trace_id,
```
