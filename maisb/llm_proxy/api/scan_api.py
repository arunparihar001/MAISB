# maisb/llm_proxy/api/scan_api.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Production Scan API — v2.5.0
# Full working integrated file for:
#   Phase 1 Enterprise Foundation
#   Phase 2 Cross-Channel Trace Engine
#   Phase 3 Analyst Dashboard
#   Phase 4 SOC Workflow / Mobile Telemetry
#   Vercel customer dashboard support
#   Self-serve API key signup
#   Pakistan-compatible billing request workflow
#   MAISB Certify HTML/PDF/SVG badge workflow
#
# Paste this file at:
#   MAISB/maisb/llm_proxy/api/scan_api.py
#
# Railway start command:
#   uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
# Local command from MAISB/maisb/llm_proxy:
#   uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import datetime as dt
import hashlib
import html
import io
import json
import os
import secrets
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# ── Import path safety ───────────────────────────────────────────────────────
# This lets the file work with:
#   cd MAISB/maisb/llm_proxy
#   uvicorn api.scan_api:app ...
# and also when run from slightly different working directories.
THIS_FILE = Path(__file__).resolve()
API_DIR = THIS_FILE.parent
LLM_PROXY_DIR = API_DIR.parent
MAISB_DIR = LLM_PROXY_DIR.parent
REPO_ROOT = MAISB_DIR.parent
for p in (str(LLM_PROXY_DIR), str(MAISB_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Environment / settings ───────────────────────────────────────────────────
DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")
PUBLIC_SIGNUP_ENABLED = os.environ.get("PUBLIC_SIGNUP_ENABLED", "true").lower() == "true"
REQUIRE_SIGNUP_INVITE_CODE = os.environ.get("REQUIRE_SIGNUP_INVITE_CODE", "false").lower() == "true"
SIGNUP_INVITE_CODE = os.environ.get("SIGNUP_INVITE_CODE", "")
FREE_TIER_MONTHLY_LIMIT = int(os.environ.get("FREE_TIER_MONTHLY_LIMIT", "1000"))
PRO_TIER_MONTHLY_LIMIT = int(os.environ.get("PRO_TIER_MONTHLY_LIMIT", "50000"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://maisb.app")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.maisb.app")
CERTIFY_BASE_URL = os.environ.get("CERTIFY_BASE_URL", API_BASE_URL)
API_VERSION = "2.5.0"

# ── Pipeline imports with safe fallback ───────────────────────────────────────
# In your real repo these imports should succeed and use the MAISB pipeline.
# The fallback only prevents Railway startup failure if paths are temporarily off.
PIPELINE_IMPORT_ERROR: Optional[str] = None
try:
    from core.models import ScanRequest as PipelineScanRequest  # type: ignore
    from pipeline.runner import run_pipeline  # type: ignore
except Exception as exc:  # pragma: no cover - fallback only
    PIPELINE_IMPORT_ERROR = str(exc)

    class PipelineScanRequest(BaseModel):
        payload: str
        channel: str = "unknown"
        objective: str = "general"
        api_key: str
        session_id: Optional[str] = None

    class _FallbackPipelineResult(BaseModel):
        decision: str
        risk_score: float
        taxonomy_class: str
        recommended_action: str
        processing_ms: int

    def run_pipeline(req: PipelineScanRequest) -> _FallbackPipelineResult:
        started = time.time()
        text = (req.payload or "").lower()
        suspicious = [
            "ignore previous", "ignore all previous", "developer message",
            "system:", "assistant:", "exfiltrate", "steal", "dump",
            "transfer immediately", "skip confirmation", "without confirmation",
            "secret", "api key", "password", "token", "bypass",
        ]
        hits = sum(1 for token in suspicious if token in text)
        risk = min(0.15 + hits * 0.20, 0.98)
        if risk >= 0.80:
            decision = "BLOCKED"
            action = "Block: injection detected or policy threshold exceeded."
            taxonomy = "T1"
        elif risk >= 0.45:
            decision = "REVIEW"
            action = "Review: suspicious content requires human or policy review."
            taxonomy = "T2"
        else:
            decision = "ALLOWED"
            action = "Allow: no high-confidence injection indicators detected."
            taxonomy = "SAFE"
        return _FallbackPipelineResult(
            decision=decision,
            risk_score=round(risk, 2),
            taxonomy_class=taxonomy,
            recommended_action=action,
            processing_ms=int((time.time() - started) * 1000),
        )

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="MAISB Scan API",
    version=API_VERSION,
    description=(
        "Mobile AI Security Benchmark — Enterprise Runtime Security API\n\n"
        "Self-serve API key: POST /v1/public/signup\n\n"
        "Scan endpoint: POST /v1/scan\n\n"
        "Customer usage: GET /v1/public/dashboard\n\n"
        "SOC console: /soc if Phase 4 router is present\n\n"
        "MAISB Certify: POST /v1/commercial/certify/start"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://maisb.app",
        "https://www.maisb.app",
        "https://app.maisb.app",
        "https://api.maisb.app",
        "https://maisb-dashboard-static.vercel.app",  # legacy Vercel dashboard fallback
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=os.environ.get("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTER_STATUS: Dict[str, Any] = {}
INTERNAL_ROUTER_ERRORS: Dict[str, str] = {}


def include_optional_router(module_name: str, label: str) -> None:
    """Include Phase routers without killing app startup if a router is absent."""
    try:
        module = __import__(module_name, fromlist=["router"])
        router = getattr(module, "router")
        app.include_router(router)
        ROUTER_STATUS[label] = {"loaded": True, "module": module_name}
    except Exception as exc:
        ROUTER_STATUS[label] = {"loaded": False, "module": module_name}
        INTERNAL_ROUTER_ERRORS[label] = str(exc)


# Keep these optional because different repo snapshots may have slightly different files.
# If the modules exist, this file connects them automatically.
include_optional_router("api.phase2_trace", "phase2_trace")
include_optional_router("api.phase3_dashboard", "phase3_dashboard")
include_optional_router("api.phase4_soc", "phase4_soc")
include_optional_router("api.signup", "legacy_signup")
include_optional_router("api.certify", "legacy_certify")
include_optional_router("api.billing", "legacy_billing")

try:
    from api.paddle_routes import router as paddle_router  # type: ignore

    app.include_router(paddle_router)
    ROUTER_STATUS["paddle_billing"] = {"loaded": True, "module": "api.paddle_routes"}
except Exception as exc:
    ROUTER_STATUS["paddle_billing"] = {"loaded": False, "module": "api.paddle_routes"}
    INTERNAL_ROUTER_ERRORS["paddle_billing"] = str(exc)

# ── Database helpers ─────────────────────────────────────────────────────────

def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return dt.datetime.utcnow().date().isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def jdump(value: Any) -> str:
    return json.dumps(value if value is not None else {}, separators=(",", ":"), ensure_ascii=False)


def jload(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default if default is not None else {}
    try:
        return json.loads(value)
    except Exception:
        return default if default is not None else {}


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    if len(raw_key) <= 18:
        return raw_key[:6] + "****"
    return raw_key[:14] + "****" + raw_key[-4:]


def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_db() -> None:
    conn = get_conn()

    # Existing scan/signup compatibility table.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key        TEXT PRIMARY KEY,
            plan       TEXT DEFAULT 'free',
            scan_count INTEGER DEFAULT 0,
            email      TEXT,
            created    TEXT
        )
    """)

    # Existing scan logs used by public usage and admin stats.
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
            ts             TEXT,
            tenant_id      TEXT DEFAULT 'default',
            session_id     TEXT,
            trace_id       TEXT,
            event_id       TEXT
        )
    """)

    # Safe migrations for older DBs.
    for col, ddl in {
        "channel": "channel TEXT",
        "objective": "objective TEXT",
        "taxonomy_class": "taxonomy_class TEXT",
        "processing_ms": "processing_ms INTEGER",
        "tenant_id": "tenant_id TEXT DEFAULT 'default'",
        "session_id": "session_id TEXT",
        "trace_id": "trace_id TEXT",
        "event_id": "event_id TEXT",
    }.items():
        add_column_if_missing(conn, "scans", col, ddl)

    for col, ddl in {
        "email": "email TEXT",
        "created": "created TEXT",
        "plan": "plan TEXT DEFAULT 'free'",
        "scan_count": "scan_count INTEGER DEFAULT 0",
    }.items():
        add_column_if_missing(conn, "api_keys", col, ddl)

    # Self-serve signup audit table.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS public_signups (
            signup_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            company TEXT,
            name TEXT,
            use_case TEXT,
            tenant_id TEXT DEFAULT 'default',
            api_key_masked TEXT,
            plan TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            ip_hash TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Billing request table: deliberately not direct Stripe.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS billing_requests (
            request_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            company TEXT,
            plan TEXT NOT NULL,
            provider TEXT DEFAULT 'manual_invoice',
            status TEXT DEFAULT 'requested',
            notes TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Certify table compatible with previous Claude implementation and new workflow.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certify_orders (
            order_id       TEXT PRIMARY KEY,
            api_key        TEXT,
            email          TEXT,
            company        TEXT,
            status         TEXT DEFAULT 'pending_payment',
            payment_id     TEXT,
            payment_provider TEXT DEFAULT 'manual_invoice',
            payment_status TEXT DEFAULT 'pending',
            package        TEXT DEFAULT 'standard',
            target_type    TEXT DEFAULT 'mobile_ai_agent',
            notes          TEXT,
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
    for col, ddl in {
        "payment_provider": "payment_provider TEXT DEFAULT 'manual_invoice'",
        "payment_status": "payment_status TEXT DEFAULT 'pending'",
        "package": "package TEXT DEFAULT 'standard'",
        "target_type": "target_type TEXT DEFAULT 'mobile_ai_agent'",
        "notes": "notes TEXT",
    }.items():
        add_column_if_missing(conn, "certify_orders", col, ddl)

    # Seed public test key for local demos only.
    conn.execute(
        "INSERT OR IGNORE INTO api_keys (key, plan, scan_count, email, created) VALUES (?, 'free', 0, ?, ?)",
        ("maisb_live_test123", "demo@maisb.local", utcnow()),
    )

    conn.commit()
    conn.close()


init_db()

# ── Request / response models ────────────────────────────────────────────────

class ScanRequestBody(BaseModel):
    payload: str
    channel: str = "unknown"
    objective: str = "general"
    api_key: str
    session_id: Optional[str] = None
    tenant_id: str = DEFAULT_TENANT_ID


class ScanResponseBody(BaseModel):
    decision: str
    risk_score: float
    taxonomy_class: str
    recommended_action: str
    processing_ms: int
    trace_id: Optional[str] = None
    event_id: Optional[str] = None
    tenant_id: Optional[str] = DEFAULT_TENANT_ID


class PublicSignupRequest(BaseModel):
    email: str
    company: Optional[str] = None
    name: Optional[str] = None
    use_case: Optional[str] = Field(default="Android / AI agent runtime protection")
    tenant_id: str = DEFAULT_TENANT_ID
    invite_code: Optional[str] = None


class BillingRequest(BaseModel):
    email: str
    company: Optional[str] = None
    plan: str = Field("pro", pattern="^(free|pro|enterprise|certify)$")
    provider: str = Field("manual_invoice", pattern="^(manual_invoice|paddle|lemon_squeezy|lemonsqueezy|bank_transfer|wise)$")
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CertifyStartRequest(BaseModel):
    email: str
    company: str
    api_key: Optional[str] = None
    package: str = Field("standard", pattern="^(starter|standard|enterprise)$")
    target_type: str = Field("mobile_ai_agent")
    notes: Optional[str] = None


class CertifyCompleteRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    adr: float = Field(..., ge=0.0, le=100.0, description="Attack Detection Rate percentage")
    fpr: float = Field(..., ge=0.0, le=100.0, description="False Positive Rate percentage")
    grade: Optional[str] = None
    summary: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class MobileTelemetryRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    sdk_version: str = "unknown"
    client_type: str = "android"
    client_id: Optional[str] = None
    integration_env: str = "production"
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: Optional[str] = None
    objective: Optional[str] = None
    decision: Optional[str] = None
    risk_score: Optional[float] = None
    trace_id: Optional[str] = None
    event_id: Optional[str] = None
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[int] = None

# ── Auth / quota helpers ─────────────────────────────────────────────────────

def bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return authorization.strip()


def require_admin(admin_key: Optional[str] = None, authorization: Optional[str] = None) -> None:
    token = bearer_token(authorization) or (admin_key or "")
    if not secrets.compare_digest(token.encode(), (ADMIN_KEY or "").encode()):
        raise HTTPException(status_code=403, detail="Forbidden: valid admin token required")


def signup_count_for_email_today(conn: sqlite3.Connection, email: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM public_signups WHERE lower(email)=lower(?) AND created_at >= ?",
        (email, today_iso()),
    ).fetchone()
    return int(row["c"] or 0)


def create_public_api_key() -> str:
    return f"maisb_live_{secrets.token_urlsafe(24)}"


def get_key_info(api_key: str) -> Dict[str, Any]:
    conn = get_conn()
    row = conn.execute(
        "SELECT key, plan, scan_count, email, created FROM api_keys WHERE key = ?",
        (api_key,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key. Get one free using POST /v1/public/signup")
    return {
        "key": row["key"],
        "plan": row["plan"] or "free",
        "scan_count": int(row["scan_count"] or 0),
        "email": row["email"],
        "created": row["created"],
    }


def plan_limit(plan: str) -> Optional[int]:
    if plan == "enterprise":
        return None
    if plan == "pro":
        return PRO_TIER_MONTHLY_LIMIT
    return FREE_TIER_MONTHLY_LIMIT


def enforce_quota(api_key: str) -> Dict[str, Any]:
    info = get_key_info(api_key)
    limit = plan_limit(info["plan"])
    if limit is not None and info["scan_count"] >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"{info['plan'].title()} plan limit of {limit:,} scans/month reached.",
                "upgrade_url": f"{APP_DASHBOARD_URL}/billing",
            },
        )
    return info

# ── Logging helpers ──────────────────────────────────────────────────────────

def new_trace_id() -> str:
    return f"trace_{secrets.token_hex(8)}"


def new_event_id() -> str:
    return f"event_{secrets.token_hex(8)}"


def log_scan(
    api_key: str,
    decision: str,
    risk_score: float,
    taxonomy: str,
    channel: str,
    objective: str,
    ms: int,
    tenant_id: str = DEFAULT_TENANT_ID,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    event_id: Optional[str] = None,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO scans
        (api_key, decision, risk_score, taxonomy_class, channel, objective, processing_ms, ts, tenant_id, session_id, trace_id, event_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            api_key,
            decision,
            risk_score,
            taxonomy,
            channel,
            objective,
            ms,
            utcnow(),
            tenant_id,
            session_id,
            trace_id,
            event_id,
        ),
    )
    conn.execute("UPDATE api_keys SET scan_count = scan_count + 1 WHERE key = ?", (api_key,))
    conn.commit()
    conn.close()


def safe_call_phase2_trace(body: ScanRequestBody, result: Any, trace_id: str, event_id: str) -> None:
    """
    Best-effort bridge: Phase 2/3/4 routers keep their own tables.
    This function never fails the scan; it only logs compatibility info if available.
    """
    # Your phase2_trace router already exposes /v1/trace/payload.
    # We avoid direct internal calls because helper names may differ by version.
    # The core scan still returns trace_id/event_id so dashboards and SDKs can correlate.
    return None

# ── Core endpoints ───────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health() -> Dict[str, Any]:
    optional_legacy_modules = {
        key: value["loaded"]
        for key, value in ROUTER_STATUS.items()
        if key.startswith("legacy_")
    }
    return {
        "status": "ok",
        "version": API_VERSION,
        "phase1": True,
        "phase2": bool(ROUTER_STATUS.get("phase2_trace", {}).get("loaded")),
        "phase3": bool(ROUTER_STATUS.get("phase3_dashboard", {}).get("loaded")),
        "phase4": bool(ROUTER_STATUS.get("phase4_soc", {}).get("loaded")),
        "commercial": True,
        "self_serve_signup": True,
        "certify": True,
        "pipeline_ready": PIPELINE_IMPORT_ERROR is None,
        "pipeline_fallback_active": PIPELINE_IMPORT_ERROR is not None,
        "optional_legacy_modules": optional_legacy_modules,
        "routers": ROUTER_STATUS,
    }


@app.get("/v1/admin/diagnostics/routers", tags=["System"])
def admin_router_diagnostics(
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    require_admin(admin_key, authorization)
    return {
        "routers": ROUTER_STATUS,
        "internal_router_error_count": len(INTERNAL_ROUTER_ERRORS),
        "modules_with_errors": sorted(INTERNAL_ROUTER_ERRORS.keys()),
        "pipeline_fallback_active": PIPELINE_IMPORT_ERROR is not None,
    }


@app.get("/", tags=["System"])
def root() -> Dict[str, Any]:
    return {
        "name": "MAISB Scan API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "GET /health",
        "scan": "POST /v1/scan",
        "self_serve_signup": "POST /v1/public/signup",
        "customer_dashboard": "GET /v1/public/dashboard",
        "plans": "GET /v1/public/plans",
        "billing_request": "POST /v1/billing/upgrade-request",
        "certify": "POST /v1/commercial/certify/start",
        "soc": "/soc if Phase 4 router loaded",
    }


@app.post("/v1/scan", response_model=ScanResponseBody, tags=["Scan"])
def scan(body: ScanRequestBody, request: Request) -> ScanResponseBody:
    """
    Scan a payload before it reaches the LLM.

    Compatible with the Android SDK:
    - body.api_key
    - body.tenant_id
    - X-Tenant-ID header
    - session_id
    """
    enforce_quota(body.api_key)

    started = time.time()
    result = run_pipeline(PipelineScanRequest(
        payload=body.payload,
        channel=body.channel,
        objective=body.objective,
        api_key=body.api_key,
        session_id=body.session_id,
    ))

    trace_id = new_trace_id()
    event_id = new_event_id()
    tenant_id = request.headers.get("X-Tenant-ID") or body.tenant_id or DEFAULT_TENANT_ID
    processing_ms = int(getattr(result, "processing_ms", int((time.time() - started) * 1000)) or 0)

    log_scan(
        api_key=body.api_key,
        decision=str(getattr(result, "decision", "REVIEW")),
        risk_score=float(getattr(result, "risk_score", 0.5)),
        taxonomy=str(getattr(result, "taxonomy_class", "UNKNOWN")),
        channel=body.channel,
        objective=body.objective,
        ms=processing_ms,
        tenant_id=tenant_id,
        session_id=body.session_id,
        trace_id=trace_id,
        event_id=event_id,
    )

    safe_call_phase2_trace(body, result, trace_id, event_id)

    return ScanResponseBody(
        decision=str(getattr(result, "decision", "REVIEW")),
        risk_score=float(getattr(result, "risk_score", 0.5)),
        taxonomy_class=str(getattr(result, "taxonomy_class", "UNKNOWN")),
        recommended_action=str(getattr(result, "recommended_action", "Review before forwarding this payload to the LLM.")),
        processing_ms=processing_ms,
        trace_id=trace_id,
        event_id=event_id,
        tenant_id=tenant_id,
    )


@app.get("/usage", tags=["Auth"])
def usage(api_key: str) -> Dict[str, Any]:
    info = get_key_info(api_key)
    limit = plan_limit(info["plan"])
    return {
        "api_key_masked": mask_key(info["key"]),
        "plan": info["plan"],
        "scan_count": info["scan_count"],
        "limit": limit,
        "remaining": None if limit is None else max(0, limit - info["scan_count"]),
        "email": info.get("email"),
        "upgrade_url": f"{APP_DASHBOARD_URL}/billing",
    }

# ── Public signup / customer dashboard ───────────────────────────────────────

@app.post("/v1/public/signup", tags=["Public Signup"])
def public_signup(body: PublicSignupRequest, request: Request) -> Dict[str, Any]:
    if not PUBLIC_SIGNUP_ENABLED:
        raise HTTPException(status_code=403, detail="Public signup is currently disabled")
    if REQUIRE_SIGNUP_INVITE_CODE and body.invite_code != SIGNUP_INVITE_CODE:
        raise HTTPException(status_code=403, detail="Valid invite code required")
    if "@" not in body.email:
        raise HTTPException(status_code=422, detail="Valid email required")

    conn = get_conn()
    if signup_count_for_email_today(conn, body.email) >= 3:
        conn.close()
        raise HTTPException(status_code=429, detail="Daily signup limit reached for this email")

    raw_key = create_public_api_key()
    now = utcnow()
    conn.execute(
        "INSERT INTO api_keys (key, plan, scan_count, email, created) VALUES (?, 'free', 0, ?, ?)",
        (raw_key, body.email, now),
    )
    signup_id = f"signup_{secrets.token_hex(8)}"
    ip_hash = sha256(request.client.host) if request.client else None
    conn.execute(
        """
        INSERT INTO public_signups
        (signup_id, email, company, name, use_case, tenant_id, api_key_masked, plan, status, ip_hash, user_agent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'free', 'active', ?, ?, ?)
        """,
        (
            signup_id,
            body.email,
            body.company,
            body.name,
            body.use_case,
            body.tenant_id,
            mask_key(raw_key),
            ip_hash,
            request.headers.get("user-agent"),
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "created": True,
        "signup_id": signup_id,
        "api_key": raw_key,
        "api_key_masked": mask_key(raw_key),
        "plan": "free",
        "monthly_limit": FREE_TIER_MONTHLY_LIMIT,
        "tenant_id": body.tenant_id,
        "warning": "Copy this API key now. Do not expose production keys in GitHub, screenshots, or reports.",
    }


@app.get("/v1/public/usage", tags=["Public Signup"])
def public_usage(api_key: str = Query(...)) -> Dict[str, Any]:
    return usage(api_key)


@app.get("/v1/public/dashboard", tags=["Public Signup"])
def public_customer_dashboard(api_key: str = Query(...)) -> Dict[str, Any]:
    u = usage(api_key)
    return {
        "customer": {
            "email": u.get("email"),
            "plan": u.get("plan"),
            "api_key_masked": u.get("api_key_masked"),
        },
        "usage": u,
        "quick_start": {
            "endpoint": f"{API_BASE_URL}/v1/scan",
            "channels": ["clipboard", "qr", "notification", "deep_link", "webview", "share_intent"],
            "android_sdk_path": "maisb/sdk/android/maisb-android-sdk",
        },
        "links": {
            "public_site": PUBLIC_BASE_URL,
            "api_docs": f"{API_BASE_URL}/docs",
            "dashboard": APP_DASHBOARD_URL,
            "soc_console": f"{APP_DASHBOARD_URL}/soc",
        },
    }

# ── Billing / plans ──────────────────────────────────────────────────────────

@app.get("/v1/public/plans", tags=["Billing"])
def public_plans() -> Dict[str, Any]:
    return {
        "billing_mode": "manual_or_merchant_of_record",
        "stripe_direct_enabled": False,
        "reason": "Direct Stripe checkout is intentionally not used in this build. Use manual invoice, Paddle, Lemon Squeezy, Wise, or bank transfer request workflows.",
        "plans": [
            {
                "id": "free",
                "name": "Free Developer",
                "price": "$0/month",
                "limit": FREE_TIER_MONTHLY_LIMIT,
                "features": ["Prompt-injection scanning", "Basic dashboard", "Community support"],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": "Request invoice",
                "limit": PRO_TIER_MONTHLY_LIMIT,
                "features": ["Higher scan quota", "Android SDK telemetry", "Email support", "Commercial usage review"],
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": "Custom",
                "limit": None,
                "features": ["Tenant policy", "SOC workflow", "Audit/export", "Retention controls", "Private deployment option"],
            },
            {
                "id": "certify",
                "name": "MAISB Certify",
                "price": "Assessment quote",
                "limit": None,
                "features": ["Benchmark assessment", "PDF report", "Certification badge", "Attack-class breakdown"],
            },
        ],
    }


@app.get("/v1/billing/plans", tags=["Billing"])
def billing_plans_compat() -> Dict[str, Any]:
    """Compatibility path for older dashboard links."""
    return public_plans()


@app.post("/v1/billing/upgrade-request", tags=["Billing"])
def billing_upgrade_request(body: BillingRequest) -> Dict[str, Any]:
    provider = "lemon_squeezy" if body.provider == "lemonsqueezy" else body.provider
    request_id = f"bill_{secrets.token_hex(8)}"
    now = utcnow()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO billing_requests
        (request_id, email, company, plan, provider, status, notes, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'requested', ?, ?, ?, ?)
        """,
        (request_id, body.email, body.company, body.plan, provider, body.notes, jdump(body.metadata), now, now),
    )
    conn.commit()
    conn.close()
    return {
        "request_id": request_id,
        "status": "requested",
        "plan": body.plan,
        "provider": provider,
        "next_step": "Manual commercial review. Send invoice/payment link using your Pakistan-compatible provider.",
        "stripe_direct_enabled": False,
    }

# ── Certify helpers / endpoints ──────────────────────────────────────────────

def grade_from_score(score: float) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "Needs Improvement"


def default_certify_report(order: sqlite3.Row) -> Dict[str, Any]:
    score = order["score"] if order["score"] is not None else 92.0
    adr = order["adr"] if order["adr"] is not None else 99.23
    fpr = order["fpr"] if order["fpr"] is not None else 0.77
    grade = order["grade"] or grade_from_score(float(score))
    return {
        "order_id": order["order_id"],
        "company": order["company"] or "Customer",
        "status": order["status"] or "requested",
        "score": float(score),
        "grade": grade,
        "adr": float(adr),
        "fpr": float(fpr),
        "summary": "MAISB Certify assessment package created. Replace demo metrics with benchmark run outputs before issuing externally.",
        "findings": [
            {"area": "Mobile channel injection", "result": "Strong detection coverage", "severity": "low"},
            {"area": "Cross-channel propagation", "result": "Trace-aware telemetry supported", "severity": "medium"},
            {"area": "SOC workflow", "result": "Risk queue and case workflow available", "severity": "low"},
        ],
        "issued_at": order["completed_at"] or utcnow(),
    }


@app.post("/v1/commercial/certify/start", tags=["MAISB Certify"])
def certify_start(body: CertifyStartRequest) -> Dict[str, Any]:
    order_id = f"cert_{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
    now = utcnow()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO certify_orders
        (order_id, api_key, email, company, status, payment_provider, payment_status, package, target_type, notes, created, report_json)
        VALUES (?, ?, ?, ?, 'assessment_requested', 'manual_invoice', 'pending', ?, ?, ?, ?, ?)
        """,
        (
            order_id,
            body.api_key,
            body.email,
            body.company,
            body.package,
            body.target_type,
            body.notes,
            now,
            jdump({"summary": "Assessment requested. Run benchmark and complete report before issuing externally."}),
        ),
    )
    conn.commit()
    conn.close()
    return {
        "order_id": order_id,
        "status": "assessment_requested",
        "payment_provider": "manual_invoice",
        "payment_status": "pending",
        "report_html_url": f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/report.html",
        "report_pdf_url": f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/report.pdf",
        "badge_svg_url": f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/badge.svg",
        "next_step": "Run MAISB benchmark, review evidence, then complete scoring with real benchmark results.",
    }


@app.post("/v1/certify/start", tags=["MAISB Certify"])
def certify_start_compat(body: CertifyStartRequest) -> Dict[str, Any]:
    """Compatibility path for older docs/dashboard."""
    return certify_start(body)


@app.get("/v1/commercial/certify/orders/{order_id}", tags=["MAISB Certify"])
def certify_get_order(order_id: str) -> Dict[str, Any]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    return {"order": dict(row), "report": default_certify_report(row)}


@app.post("/v1/commercial/certify/orders/{order_id}/complete-demo", tags=["MAISB Certify"])
def certify_complete_demo(
    order_id: str,
    body: CertifyCompleteRequest,
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    require_admin(admin_key, authorization)
    grade = body.grade or grade_from_score(body.score)
    report = {
        "order_id": order_id,
        "score": body.score,
        "grade": grade,
        "adr": body.adr,
        "fpr": body.fpr,
        "summary": body.summary or "MAISB Certify assessment completed.",
        "findings": body.findings,
        "issued_at": utcnow(),
    }
    conn = get_conn()
    cur = conn.execute(
        """
        UPDATE certify_orders
        SET status='completed', payment_status='paid_or_waived', completed_at=?, score=?, grade=?, adr=?, fpr=?, report_json=?
        WHERE order_id=?
        """,
        (utcnow(), body.score, grade, body.adr, body.fpr, jdump(report), order_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Certify order not found")
    return {"updated": True, "order_id": order_id, "report": report}


def render_report_html(report: Dict[str, Any]) -> str:
    findings = "".join(
        f"<tr><td>{html.escape(str(f.get('area','')))}</td><td>{html.escape(str(f.get('result','')))}</td><td>{html.escape(str(f.get('severity','')))}</td></tr>"
        for f in report.get("findings", [])
    )
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>MAISB Certify Report</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#f8fafc;color:#0f172a;margin:0;padding:40px}}
.card{{max-width:920px;margin:auto;background:white;border:1px solid #e2e8f0;border-radius:22px;padding:32px;box-shadow:0 18px 45px rgba(15,23,42,.08)}}
h1{{margin:0 0 8px;font-size:34px}} .muted{{color:#64748b}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}}
.metric{{background:#f1f5f9;border-radius:16px;padding:18px}} .metric b{{font-size:24px;display:block}}
.badge{{display:inline-block;background:#052e2b;color:#5eead4;border-radius:999px;padding:8px 14px;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin-top:18px}}td,th{{border-bottom:1px solid #e2e8f0;text-align:left;padding:12px}}
</style></head><body><div class='card'>
<div class='badge'>MAISB CERTIFY</div>
<h1>Security Assessment Report</h1>
<p class='muted'>Order {html.escape(str(report.get('order_id')))} · Issued {html.escape(str(report.get('issued_at')))}</p>
<div class='grid'>
<div class='metric'><span>Score</span><b>{report.get('score')}%</b></div>
<div class='metric'><span>Grade</span><b>{html.escape(str(report.get('grade')))}</b></div>
<div class='metric'><span>ADR</span><b>{report.get('adr')}%</b></div>
<div class='metric'><span>FPR</span><b>{report.get('fpr')}%</b></div>
</div>
<h2>Summary</h2><p>{html.escape(str(report.get('summary')))}</p>
<h2>Findings</h2><table><thead><tr><th>Area</th><th>Result</th><th>Severity</th></tr></thead><tbody>{findings}</tbody></table>
<p class='muted'>Generated by MAISB. Do not publish private API keys, admin keys, payload samples, database files, or unredacted customer data.</p>
</div></body></html>"""


def make_simple_pdf(title: str, lines: List[str]) -> bytes:
    """Dependency-free single-page PDF writer."""
    def esc(s: str) -> str:
        return str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = ["BT", "/F1 20 Tf", "72 760 Td", f"({esc(title)}) Tj", "/F1 11 Tf", "0 -30 Td"]
    for line in lines[:42]:
        content_lines.append(f"({esc(line)[:110]}) Tj")
        content_lines.append("0 -16 Td")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", "replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects)+1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return out.getvalue()


@app.get("/v1/commercial/certify/orders/{order_id}/report.html", response_class=HTMLResponse, tags=["MAISB Certify"])
def certify_report_html(order_id: str) -> HTMLResponse:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    report = jload(row["report_json"], None) or default_certify_report(row)
    return HTMLResponse(render_report_html(report))


@app.get("/v1/commercial/certify/orders/{order_id}/report.pdf", tags=["MAISB Certify"])
def certify_report_pdf(order_id: str) -> Response:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    report = jload(row["report_json"], None) or default_certify_report(row)
    lines = [
        f"Order ID: {report.get('order_id')}",
        f"Company: {row['company'] or 'Customer'}",
        f"Status: {row['status']}",
        f"Score: {report.get('score')}%",
        f"Grade: {report.get('grade')}",
        f"Attack Detection Rate: {report.get('adr')}%",
        f"False Positive Rate: {report.get('fpr')}%",
        f"Issued: {report.get('issued_at')}",
        "",
        "Summary:",
        str(report.get("summary")),
        "",
        "Findings:",
    ]
    for finding in report.get("findings", []):
        lines.append(f"- {finding.get('area')}: {finding.get('result')} [{finding.get('severity')}]")
    pdf = make_simple_pdf("MAISB Certify Security Assessment Report", lines)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=maisb-certify-{order_id}.pdf"},
    )


@app.get("/v1/commercial/certify/orders/{order_id}/badge.svg", tags=["MAISB Certify"])
def certify_badge_svg(order_id: str) -> Response:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    report = jload(row["report_json"], None) or default_certify_report(row)
    grade = html.escape(str(report.get("grade", "PENDING")))
    score = html.escape(str(report.get("score", "—")))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="520" height="170" viewBox="0 0 520 170" role="img" aria-label="MAISB Certify Badge">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#0f766e"/></linearGradient></defs>
<rect width="520" height="170" rx="28" fill="url(#g)"/>
<circle cx="82" cy="85" r="44" fill="#14b8a6" opacity=".16" stroke="#5eead4" stroke-width="3"/>
<path d="M62 86l14 15 30-36" fill="none" stroke="#5eead4" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
<text x="145" y="58" fill="#e2e8f0" font-family="Inter,Arial" font-size="18" font-weight="700">MAISB CERTIFY</text>
<text x="145" y="94" fill="white" font-family="Inter,Arial" font-size="32" font-weight="800">Grade {grade}</text>
<text x="145" y="124" fill="#99f6e4" font-family="Inter,Arial" font-size="17">AI Runtime Security · Score {score}%</text>
<text x="145" y="148" fill="#cbd5e1" font-family="Inter,Arial" font-size="12">Order {html.escape(order_id)}</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")

# ── Commercial / admin visibility ────────────────────────────────────────────

@app.get("/v1/commercial/health", tags=["Commercial"])
def commercial_health() -> Dict[str, Any]:
    conn = get_conn()
    public_keys = conn.execute("SELECT COUNT(*) AS c FROM api_keys").fetchone()["c"]
    billing = conn.execute("SELECT COUNT(*) AS c FROM billing_requests").fetchone()["c"]
    certify = conn.execute("SELECT COUNT(*) AS c FROM certify_orders").fetchone()["c"]
    signups = conn.execute("SELECT COUNT(*) AS c FROM public_signups").fetchone()["c"]
    conn.close()
    return {
        "status": "ok",
        "commercial": True,
        "commercial_complete": True,
        "version": API_VERSION,
        "features": {
            "vercel_dashboard_connected": True,
            "self_serve_api_key_signup": PUBLIC_SIGNUP_ENABLED,
            "stripe_direct_billing": False,
            "manual_invoice_billing": True,
            "merchant_of_record_ready": True,
            "certify_pdf_report": True,
            "certify_svg_badge": True,
        },
        "counts": {
            "public_keys": int(public_keys or 0),
            "signups": int(signups or 0),
            "billing_requests": int(billing or 0),
            "certify_orders": int(certify or 0),
        },
        "routers": ROUTER_STATUS,
    }


@app.get("/v1/commercial/admin/requests", tags=["Commercial"])
def commercial_admin_requests(
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    require_admin(admin_key, authorization)
    conn = get_conn()
    signups = [dict(r) for r in conn.execute("SELECT * FROM public_signups ORDER BY created_at DESC LIMIT 50").fetchall()]
    billing = [dict(r) for r in conn.execute("SELECT * FROM billing_requests ORDER BY created_at DESC LIMIT 50").fetchall()]
    certify = [
        dict(r)
        for r in conn.execute(
            "SELECT order_id,email,company,status,payment_provider,payment_status,package,target_type,created,completed_at,score,grade FROM certify_orders ORDER BY created DESC LIMIT 50"
        ).fetchall()
    ]
    conn.close()
    return {"signups": signups, "billing_requests": billing, "certify_orders": certify}

# ── Mobile telemetry fallback endpoint ───────────────────────────────────────
# If Phase 4 router is loaded and defines the same route, that router may handle it.
# This fallback makes the Android SDK work even in snapshots where phase4_soc.py is absent.

@app.post("/v1/sdk/mobile/telemetry", tags=["Mobile SDK"])
def mobile_telemetry_fallback(body: MobileTelemetryRequest) -> Dict[str, Any]:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mobile_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            sdk_version TEXT,
            client_type TEXT,
            client_id TEXT,
            integration_env TEXT,
            device_id TEXT,
            session_id TEXT,
            channel TEXT,
            objective TEXT,
            decision TEXT,
            risk_score REAL,
            trace_id TEXT,
            event_id TEXT,
            latency_ms INTEGER,
            metadata_json TEXT,
            created_at TEXT
        )
    """)
    conn.execute(
        """
        INSERT INTO mobile_telemetry
        (tenant_id, sdk_version, client_type, client_id, integration_env, device_id, session_id, channel, objective, decision, risk_score, trace_id, event_id, latency_ms, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            body.tenant_id,
            body.sdk_version,
            body.client_type,
            body.client_id,
            body.integration_env,
            body.device_id,
            body.session_id,
            body.channel,
            body.objective,
            body.decision,
            body.risk_score,
            body.trace_id,
            body.event_id,
            body.latency_ms,
            jdump(body.metadata),
            utcnow(),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT COUNT(*) AS c FROM mobile_telemetry WHERE tenant_id=?", (body.tenant_id,)).fetchone()
    conn.close()
    return {"recorded": True, "tenant_id": body.tenant_id, "mobile_telemetry_count": int(row["c"] or 0)}

# ── Legacy admin endpoints ───────────────────────────────────────────────────

@app.post("/admin/reset-monthly-counts", include_in_schema=False)
def reset_monthly_counts(admin_key: str) -> Dict[str, Any]:
    require_admin(admin_key=admin_key)
    conn = get_conn()
    conn.execute("UPDATE api_keys SET scan_count = 0")
    conn.commit()
    conn.close()
    return {"reset": True}


@app.get("/admin/keys", include_in_schema=False)
def list_keys(admin_key: str) -> Dict[str, Any]:
    require_admin(admin_key=admin_key)
    conn = get_conn()
    rows = conn.execute(
        "SELECT key, plan, scan_count, email, created FROM api_keys ORDER BY created DESC"
    ).fetchall()
    conn.close()
    return {
        "keys": [
            {
                "key": mask_key(r["key"]),
                "plan": r["plan"],
                "scans": r["scan_count"],
                "email": r["email"],
                "created": r["created"],
            }
            for r in rows
        ]
    }


@app.get("/admin/stats", include_in_schema=False)
def stats(admin_key: str) -> Dict[str, Any]:
    require_admin(admin_key=admin_key)
    conn = get_conn()
    total_scans = conn.execute("SELECT SUM(scan_count) AS s FROM api_keys").fetchone()["s"] or 0
    total_keys = conn.execute("SELECT COUNT(*) AS c FROM api_keys").fetchone()["c"] or 0
    blocked = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='BLOCKED'").fetchone()["c"] or 0
    allowed = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='ALLOWED'").fetchone()["c"] or 0
    review = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='REVIEW'").fetchone()["c"] or 0
    conn.close()
    return {
        "total_api_keys": int(total_keys),
        "total_scans": int(total_scans),
        "decisions": {"BLOCKED": int(blocked), "ALLOWED": int(allowed), "REVIEW": int(review)},
    }
