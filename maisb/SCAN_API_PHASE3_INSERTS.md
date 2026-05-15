# Phase 3 scan_api.py integration snippets

Use the automatic patch first:

```powershell
cd E:\projects\maisb-monorepo
python tools\apply_phase3_patch.py
```

If you prefer manual integration, apply these changes.

## 1. Add import near the top of `maisb/llm_proxy/api/scan_api.py`

```python
from api.phase3_dashboard import router as phase3_router
```

## 2. Include router after existing app.include_router(...) lines

```python
app.include_router(phase3_router)
```

## 3. Update API version

Change:

```python
version = "2.2.0"
```

to:

```python
version = "2.3.0"
```

Also update `/health` response from version `2.2.0` to `2.3.0`.

## 4. Optional health flag

If your `/health` response has:

```python
"phase2": True
```

change it to:

```python
"phase2": True,
"phase3": True
```
