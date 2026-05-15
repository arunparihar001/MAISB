# maisb/llm_proxy/api/scan_api.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Production Scan API — v2.1.0
# Wires: core scan + signup + certify + billing
#
# Run locally:
#   uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload
# Railway start command (set in railway.json):
#   uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
import datetime
import os
import sys
import hashlib
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.models import ScanRequest as PipelineScanRequest
from pipeline.runner import run_pipeline

# ── New routers wired in ──────────────────────────────────────────────────────
from api.signup  import router as signup_router   # Part 1 — self-serve keys
from api.certify import router as certify_router  # Part 3 — MAISB Certify
from api.billing import router as billing_router  # Part 4 — Paddle billing

# ── Enterprise Phase 1 complete imports ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from maisb.core.database import init_db as init_enterprise_db, get_db_session
from maisb.core.migrations import run_phase1_migrations
from maisb.core.models.auth import APIKey as EnterpriseAPIKey
from maisb.core.bootstrap import ensure_default_enterprise
from maisb.core.policies.engine import PolicyEngine
from maisb.core.audit.logger import AuditLogger
from maisb.core.services.auth.auth_middleware import authenticate_api_key
from maisb.core.governance.retention_policy import get_retention_policy
from maisb.core.governance.privacy_modes import sanitize_payload_preview
from api.enterprise_routes import router as enterprise_router

DB_PATH                = os.environ.get("DB_PATH", "usage.db")
FREE_TIER_MONTHLY_LIMIT = 1000
PRO_TIER_MONTHLY_LIMIT  = 50_000
ADMIN_KEY              = os.environ.get("ADMIN_KEY", "change_me_in_production")

# ── DB setup ──────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key        TEXT PRIMARY KEY,
            plan       TEXT DEFAULT 'free',
            scan_count INTEGER DEFAULT 0,
            email      TEXT,
            created    TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key        TEXT,
            decision       TEXT,
            risk_score     REAL,
            taxonomy_class TEXT,
            channel        TEXT,
            objective      TEXT,
            processing_ms  INTEGER,
            ts             TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certify_orders (
            order_id       TEXT PRIMARY KEY,
            api_key        TEXT,
            email          TEXT,
            company        TEXT,
            status         TEXT DEFAULT 'pending_payment',
            payment_id     TEXT,
            created        TEXT,
            paid_at        TEXT,
            completed_at   TEXT,
            score          REAL,
            grade          TEXT,
            adr            REAL,
            fpr            REAL,
            report_json    TEXT
        )
    """)

    # ── Schema migrations (safe on existing DBs) ──────────────────────────────
    scan_cols = {r[1] for r in conn.execute("PRAGMA table_info(scans)").fetchall()}
    for col, sql in {
        "channel":        "ALTER TABLE scans ADD COLUMN channel TEXT",
        "objective":      "ALTER TABLE scans ADD COLUMN objective TEXT",
        "taxonomy_class": "ALTER TABLE scans ADD COLUMN taxonomy_class TEXT",
        "processing_ms":  "ALTER TABLE scans ADD COLUMN processing_ms INTEGER",
    }.items():
        if col not in scan_cols:
            conn.execute(sql)

    key_cols = {r[1] for r in conn.execute("PRAGMA table_info(api_keys)").fetchall()}
    if "email" not in key_cols:
        conn.execute("ALTER TABLE api_keys ADD COLUMN email TEXT")

    # Seed the public test key
    conn.execute(
        "INSERT OR IGNORE INTO api_keys (key, plan, scan_count, created) VALUES (?, 'free', 0, ?)",
        ("maisb_live_test123", datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

init_db()

# Initialize SQLAlchemy enterprise database and seed default tenant/policy.
init_enterprise_db()
run_phase1_migrations()
with get_db_session() as db:
    ensure_default_enterprise(db)

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "MAISB Scan API",
    version     = "2.1.0",
    description = (
        "Mobile AI Security Benchmark — Prompt Injection Detection\n\n"
        "**Get your free API key:** POST /v1/signup\n\n"
        "**Run a scan:** POST /v1/scan\n\n"
        "**MAISB Certify (annual assessment):** POST /v1/certify/start"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://maisb-dashboard-static.vercel.app",
        "https://maisb.ai",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire all routers
app.include_router(signup_router)
app.include_router(certify_router)
app.include_router(billing_router)
app.include_router(enterprise_router)

# ── Request / Response models ─────────────────────────────────────────────────

class ScanRequestBody(BaseModel):
    payload:    str
    channel:    str = "unknown"
    objective:  str = "general"
    api_key:    str
    session_id: str = None
    tenant_id:  str = "default"

class ScanResponseBody(BaseModel):
    decision:           str
    risk_score:         float
    taxonomy_class:     str
    recommended_action: str
    processing_ms:      int

# ── DB helpers ────────────────────────────────────────────────────────────────


def get_enterprise_key_info(api_key: str, tenant_id: str | None = None, consume_usage: bool = False) -> dict | None:
    """
    Verify API keys created by /v1/auth/generate-key.

    Also enforces:
    - tenant binding
    - scan scope
    - monthly usage limit
    """
    if not api_key:
        return None

    try:
        with get_db_session() as db:
            ctx = authenticate_api_key(
                db=db,
                raw_key=api_key,
                tenant_id=tenant_id,
                required_scope="scan",
                required_permission="scan",
                consume_usage=consume_usage,
            )
            return {
                "key": api_key,
                "plan": "enterprise",
                "scan_count": ctx.usage_count,
                "tenant_id": ctx.tenant_id,
                "key_id": ctx.key_id,
                "role": ctx.role,
                "scopes": ctx.scopes,
                "monthly_limit": ctx.monthly_limit,
                "enterprise": True,
            }
    except HTTPException:
        raise
    except Exception:
        return None

def get_key_info(api_key: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row  = conn.execute(
        "SELECT key, plan, scan_count FROM api_keys WHERE key = ?", (api_key,)
    ).fetchone()
    conn.close()
    if not row:
        enterprise_info = get_enterprise_key_info(api_key)
        if enterprise_info:
            return enterprise_info
        raise HTTPException(status_code=401, detail="Invalid API key. Get one free: POST /v1/signup")
    return {"key": row[0], "plan": row[1] or "free", "scan_count": row[2] or 0, "tenant_id": "default", "enterprise": False}

def enforce_quota(api_key: str):
    info  = get_key_info(api_key)
    if info.get("enterprise"):
        return info
    limit = PRO_TIER_MONTHLY_LIMIT if info["plan"] == "pro" else FREE_TIER_MONTHLY_LIMIT
    if info["scan_count"] >= limit:
        raise HTTPException(status_code=429, detail={
            "error":       "quota_exceeded",
            "message":     f"{info['plan'].title()} plan limit of {limit:,} scans/month reached.",
            "upgrade_url": "https://maisb-production.up.railway.app/v1/billing/plans",
        })
    return info

def log_scan(api_key, decision, risk_score, taxonomy, channel, objective, ms):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scans (api_key,decision,risk_score,taxonomy_class,channel,objective,processing_ms,ts) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (api_key, decision, risk_score, taxonomy, channel, objective, ms,
         datetime.datetime.utcnow().isoformat())
    )
    conn.execute("UPDATE api_keys SET scan_count = scan_count + 1 WHERE key = ?", (api_key,))
    conn.commit()
    conn.close()


def apply_enterprise_policy(
    tenant_id: str,
    payload: str,
    channel: str,
    objective: str,
    pipeline_decision: str,
    risk_score: float
) -> str:
    """
    Apply tenant policy after the existing MAISB pipeline result.
    Also writes privacy-aware audit logs.
    """
    normalized_pipeline = (pipeline_decision or "REVIEW").upper()

    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=tenant_id)
        retention_policy = get_retention_policy(db, tenant_id)
        payload_preview = sanitize_payload_preview(
            payload,
            mode=retention_policy.privacy_mode,
            limit=100,
        )

        policy_decision = PolicyEngine.evaluate(
            db=db,
            payload=payload,
            channel=channel,
            objective=objective,
            tenant_id=tenant_id,
            risk_score=risk_score,
        )

        final_decision = normalized_pipeline
        if normalized_pipeline == "BLOCKED":
            final_decision = "BLOCKED"
        elif policy_decision.action == "BLOCK":
            final_decision = "BLOCKED"
        elif normalized_pipeline == "REVIEW":
            final_decision = "REVIEW"
        elif policy_decision.action == "REVIEW":
            final_decision = "REVIEW"
        elif normalized_pipeline in {"ALLOWED", "ALLOW"} and policy_decision.action == "ALLOW":
            final_decision = "ALLOWED"

        AuditLogger.log_scan(
            db=db,
            tenant_id=tenant_id,
            channel=channel,
            decision=final_decision,
            risk_score=risk_score,
            payload_preview=payload_preview,
        )
        return final_decision

# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "2.1.0"}

@app.get("/", tags=["System"])
def root():
    return {
        "name":    "MAISB Scan API",
        "version": "2.1.0",
        "docs":    "/docs",
        "signup":  "POST /v1/signup",
        "scan":    "POST /v1/scan",
        "plans":   "GET /v1/billing/plans",
        "certify": "POST /v1/certify/start",
        "enterprise_health": "GET /v1/enterprise/health",
        "enterprise_keys": "POST /v1/auth/generate-key",
        "governance_retention": "GET /v1/governance/retention",
    }

@app.post("/v1/scan", response_model=ScanResponseBody, tags=["Scan"])
def scan(body: ScanRequestBody, request: Request):
    """
    Scan a payload for prompt injection attacks.

    Enterprise Phase 1 complete additions:
    - tenant context from X-Tenant-ID or body.tenant_id
    - enterprise API key support
    - scan scope enforcement
    - RBAC scan permission enforcement
    - enterprise usage limits
    - policy engine enforcement
    - privacy-aware audit logging
    """
    requested_tenant_id = request.headers.get("X-Tenant-ID") or body.tenant_id or "default"

    # Enterprise keys are strictly tenant/scoped/role/usage checked here.
    # Legacy SQLite keys continue to work through the older quota logic.
    key_info = get_enterprise_key_info(body.api_key, tenant_id=requested_tenant_id, consume_usage=True)
    if not key_info:
        key_info = enforce_quota(body.api_key)

    tenant_id = key_info.get("tenant_id") or requested_tenant_id or "default"

    result = run_pipeline(PipelineScanRequest(
        payload    = body.payload,
        channel    = body.channel,
        objective  = body.objective,
        api_key    = body.api_key,
        session_id = body.session_id,
    ))

    final_decision = apply_enterprise_policy(
        tenant_id=tenant_id,
        payload=body.payload,
        channel=body.channel,
        objective=body.objective,
        pipeline_decision=result.decision,
        risk_score=result.risk_score,
    )

    log_scan(body.api_key, final_decision, result.risk_score,
             result.taxonomy_class, body.channel, body.objective, result.processing_ms)

    return ScanResponseBody(
        decision           = final_decision,
        risk_score         = result.risk_score,
        taxonomy_class     = result.taxonomy_class,
        recommended_action = result.recommended_action,
        processing_ms      = result.processing_ms,
    )

@app.get("/usage", tags=["Auth"])
def usage(api_key: str):
    """Check your current usage and quota."""
    info  = get_key_info(api_key)
    limit = PRO_TIER_MONTHLY_LIMIT if info["plan"] == "pro" else FREE_TIER_MONTHLY_LIMIT
    return {
        "plan":        info["plan"],
        "scan_count":  info["scan_count"],
        "limit":       limit,
        "remaining":   max(0, limit - info["scan_count"]),
        "upgrade_url": "https://maisb-production.up.railway.app/v1/billing/plans",
    }

# ── Admin endpoints ───────────────────────────────────────────────────────────

@app.post("/admin/reset-monthly-counts", include_in_schema=False)
def reset_monthly_counts(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE api_keys SET scan_count = 0")
    conn.commit()
    conn.close()
    return {"reset": True}

@app.get("/admin/keys", include_in_schema=False)
def list_keys(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT key, plan, scan_count, email, created FROM api_keys ORDER BY created DESC"
    ).fetchall()
    conn.close()
    return {"keys": [{"key": r[0][:14]+"****", "plan": r[1], "scans": r[2],
                      "email": r[3], "created": r[4]} for r in rows]}

@app.get("/admin/stats", include_in_schema=False)
def stats(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = sqlite3.connect(DB_PATH)
    total_scans = conn.execute("SELECT SUM(scan_count) FROM api_keys").fetchone()[0] or 0
    total_keys  = conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0] or 0
    blocked     = conn.execute("SELECT COUNT(*) FROM scans WHERE decision='BLOCKED'").fetchone()[0] or 0
    allowed     = conn.execute("SELECT COUNT(*) FROM scans WHERE decision='ALLOWED'").fetchone()[0] or 0
    review      = conn.execute("SELECT COUNT(*) FROM scans WHERE decision='REVIEW'").fetchone()[0] or 0
    conn.close()
    return {
        "total_api_keys":   total_keys,
        "total_scans":      total_scans,
        "decisions":        {"BLOCKED": blocked, "ALLOWED": allowed, "REVIEW": review},
    }
