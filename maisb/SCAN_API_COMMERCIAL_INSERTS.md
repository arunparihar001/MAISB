# MAISB scan_api.py Commercial Router Integration

Your current repo already has `maisb/llm_proxy/api/scan_api.py` as the main Railway entry point.
Do **not** replace the full file unless you intentionally want to rebuild it. Add only these two lines.

## 1) Add this import near the other router imports

```python
from api.commercial_routes import router as commercial_router
```

Example location:

```python
from api.phase3_dashboard import router as phase3_router
from api.phase4_soc import router as phase4_router
from api.commercial_routes import router as commercial_router
```

## 2) Include the router after existing app.include_router calls

```python
app.include_router(commercial_router)
```

Example location:

```python
app.include_router(phase3_router)
app.include_router(phase4_router)
app.include_router(commercial_router)
```

## 3) Optional health flag update

If your `/health` currently returns:

```python
return {"status": "ok", "version": "2.4.0", "phase2": True, "phase3": True, "phase4": True}
```

Update it to:

```python
return {
    "status": "ok",
    "version": "2.5.0",
    "phase2": True,
    "phase3": True,
    "phase4": True,
    "commercial": True,
    "self_serve_signup": True,
    "certify": True,
}
```

This is optional because `/v1/commercial/health` already reports the new commercial layer.

## 4) CORS check

Make sure your CORS allow list includes:

```python
"https://maisb-dashboard-static.vercel.app",
# legacy fallback origin
"http://localhost:5173",
"http://localhost:3000",
```

## 5) New endpoints after adding the router

```text
GET  /v1/commercial/health
POST /v1/public/signup
GET  /v1/public/usage
GET  /v1/public/dashboard
GET  /v1/public/plans
POST /v1/billing/upgrade-request
POST /v1/commercial/certify/start
GET  /v1/commercial/certify/orders/{order_id}
GET  /v1/commercial/certify/orders/{order_id}/report.html
GET  /v1/commercial/certify/orders/{order_id}/report.pdf
GET  /v1/commercial/certify/orders/{order_id}/badge.svg
POST /v1/commercial/certify/orders/{order_id}/complete-demo
GET  /v1/commercial/admin/requests
```
