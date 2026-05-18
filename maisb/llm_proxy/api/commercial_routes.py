# maisb/llm_proxy/api/commercial_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Commercial + Public Dashboard Layer
# Adds: self-serve API key signup, customer dashboard data, Pakistan-compatible
# billing request workflow, MAISB Certify order/report/PDF/badge endpoints.
#
# Paste into:
#   MAISB/maisb/llm_proxy/api/commercial_routes.py
# Then include it in scan_api.py:
#   from api.commercial_routes import router as commercial_router
#   app.include_router(commercial_router)
# ─────────────────────────────────────────────────────────────────────────────

import datetime as dt
import hashlib
import hmac
import html
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
PUBLIC_SIGNUP_ENABLED = os.environ.get("PUBLIC_SIGNUP_ENABLED", "true").lower() == "true"
REQUIRE_SIGNUP_INVITE_CODE = os.environ.get("REQUIRE_SIGNUP_INVITE_CODE", "false").lower() == "true"
SIGNUP_INVITE_CODE = os.environ.get("SIGNUP_INVITE_CODE", "")
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")
COMMERCIAL_VERSION = "2.5.0"
FREE_TIER_MONTHLY_LIMIT = int(os.environ.get("FREE_TIER_MONTHLY_LIMIT", "1000"))
PRO_TIER_MONTHLY_LIMIT = int(os.environ.get("PRO_TIER_MONTHLY_LIMIT", "50000"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://maisb.app")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.maisb.app")
CERTIFY_BASE_URL = os.environ.get("CERTIFY_BASE_URL", API_BASE_URL)

LOGGER = logging.getLogger(__name__)

# Resend email notifications. Supports both the current Railway variable names
# and older PR aliases so deployment does not break when env names differ.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM") or os.environ.get("RESEND_FROM_EMAIL") or "MAISB <hello@updates.maisb.app>"
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")
SALES_NOTIFY_EMAIL = os.environ.get("SALES_NOTIFY_EMAIL", "")
SECURITY_NOTIFY_EMAIL = os.environ.get("SECURITY_NOTIFY_EMAIL", "")
RESEND_NOTIFY_EMAILS = [
    email.strip()
    for email in os.environ.get("RESEND_NOTIFY_EMAILS", "").split(",")
    if email.strip()
]

# Paddle / merchant-of-record billing. Checkout can run in link/config mode,
# while account upgrade is trusted only after signed webhook confirmation.
PADDLE_ENV = os.environ.get("PADDLE_ENV", "sandbox")
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
PADDLE_PRO_PRICE_ID = os.environ.get("PADDLE_PRO_PRICE_ID") or os.environ.get("PADDLE_PRICE_ID_PRO", "")
PADDLE_CERTIFY_PRICE_ID = os.environ.get("PADDLE_CERTIFY_PRICE_ID") or os.environ.get("PADDLE_PRICE_ID_CERTIFY", "")
PADDLE_CHECKOUT_URL = os.environ.get("PADDLE_CHECKOUT_URL", "")
PADDLE_ENABLED = os.environ.get(
    "PADDLE_ENABLED",
    "true" if (PADDLE_API_KEY or PADDLE_CHECKOUT_URL or PADDLE_PRO_PRICE_ID or PADDLE_CERTIFY_PRICE_ID) else "false",
).lower() == "true"

router = APIRouter(tags=["Commercial - Dashboard, Signup, Billing, Certify"])

# ── Utilities ────────────────────────────────────────────────────────────────

def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat()


def today() -> str:
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


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return row is not None


# ── Email + Paddle helpers ───────────────────────────────────────────────────

def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", (value or "").strip()))


def resend_enabled() -> bool:
    return bool(RESEND_API_KEY and RESEND_FROM)


def resend_recipients(*emails: Optional[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for email in list(emails) + RESEND_NOTIFY_EMAILS:
        if not email:
            continue
        clean = email.strip()
        if clean and clean not in seen:
            seen.add(clean)
            output.append(clean)
    return output


def send_resend_email(to_emails: List[str], subject: str, html_body: str) -> bool:
    recipients = [email for email in to_emails if email]
    if not resend_enabled() or not recipients:
        return False
    payload: Dict[str, Any] = {
        "from": RESEND_FROM,
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }
    if RESEND_REPLY_TO:
        payload["reply_to"] = RESEND_REPLY_TO
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception as exc:  # fail-safe: never break customer flows over email
        LOGGER.warning("Resend delivery failed: %s", exc)
        return False


def send_admin_notification(subject: str, message: str) -> bool:
    recipients = resend_recipients(SALES_NOTIFY_EMAIL, SECURITY_NOTIFY_EMAIL)
    return send_resend_email(recipients, subject, f"<p>{html.escape(message)}</p>")


def send_api_key_created_email(email: str, raw_api_key: str, api_key_masked: str) -> bool:
    body = (
        "<p>Your MAISB Shield API key was created.</p>"
        f"<p><b>Key shown once:</b></p><pre>{html.escape(raw_api_key)}</pre>"
        f"<p>Masked key: <code>{html.escape(api_key_masked)}</code></p>"
        "<p>Keep this key secret. Do not commit it to GitHub, screenshots, mobile apps, or public reports.</p>"
        f"<p><a href='{html.escape(APP_DASHBOARD_URL)}'>Open dashboard</a></p>"
    )
    return send_resend_email([email], "Your MAISB Shield API key", body)


def send_billing_request_email(email: str, plan: str, request_id: str, company: Optional[str] = None) -> bool:
    body = (
        "<p>We received your MAISB billing request.</p>"
        f"<p>Request ID: <b>{html.escape(request_id)}</b><br/>"
        f"Plan: {html.escape(plan)}<br/>Company: {html.escape(company or 'N/A')}</p>"
    )
    send_admin_notification("New MAISB billing request", f"{request_id} · {email} · {plan}")
    return send_resend_email([email], "MAISB billing request received", body)


def send_certify_started_email(email: str, order_id: str, company: str) -> bool:
    report_url = f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/report.pdf"
    badge_url = f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/badge.svg"
    body = (
        "<p>Your MAISB Certify order has been created.</p>"
        f"<p>Order: <b>{html.escape(order_id)}</b><br/>Company: {html.escape(company)}</p>"
        f"<p>Report URL: <a href='{html.escape(report_url)}'>{html.escape(report_url)}</a></p>"
        f"<p>Badge URL: <a href='{html.escape(badge_url)}'>{html.escape(badge_url)}</a></p>"
    )
    send_admin_notification("New MAISB Certify order", f"{order_id} · {email} · {company}")
    return send_resend_email([email], "MAISB Certify order started", body)


def send_certify_report_ready_email(email: str, order_id: str, report_url: str, badge_url: str) -> bool:
    body = (
        "<p>Your MAISB Certify report is ready.</p>"
        f"<p>Order: <b>{html.escape(order_id)}</b></p>"
        f"<p><a href='{html.escape(report_url)}'>Download report PDF</a></p>"
        f"<p><a href='{html.escape(badge_url)}'>Open badge SVG</a></p>"
    )
    return send_resend_email([email], "MAISB Certify report ready", body)


def paddle_price_id_for_plan(plan: str) -> str:
    if plan == "certify":
        return PADDLE_CERTIFY_PRICE_ID
    return PADDLE_PRO_PRICE_ID


def paddle_plan_for_price(price_id: str) -> str:
    if price_id and PADDLE_CERTIFY_PRICE_ID and price_id == PADDLE_CERTIFY_PRICE_ID:
        return "certify"
    return "pro"


def paddle_checkout_config(email: str, plan: str, company: Optional[str] = None, success_url: Optional[str] = None, cancel_url: Optional[str] = None) -> Dict[str, Any]:
    price_id = paddle_price_id_for_plan(plan)
    success = success_url or f"{APP_DASHBOARD_URL}/billing?checkout=success"
    cancel = cancel_url or f"{APP_DASHBOARD_URL}/billing?checkout=cancelled"
    if not PADDLE_ENABLED or not price_id:
        raise HTTPException(
            status_code=503,
            detail="Paddle checkout is not configured. Add Paddle env vars or use manual billing request.",
        )
    checkout: Dict[str, Any] = {
        "environment": PADDLE_ENV,
        "price_id": price_id,
        "plan": plan,
        "customer": {"email": email, "company": company},
        "success_url": success,
        "cancel_url": cancel,
        "custom_data": {"product": "maisb-shield", "plan": plan, "email": email},
    }
    if PADDLE_CHECKOUT_URL:
        query = {
            "email": email,
            "plan": plan,
            "price_id": price_id,
            "success_url": success,
            "cancel_url": cancel,
            "passthrough": jdump({"plan": plan, "email": email, "source": "maisb_dashboard"}),
        }
        glue = "&" if "?" in PADDLE_CHECKOUT_URL else "?"
        checkout["checkout_url"] = f"{PADDLE_CHECKOUT_URL}{glue}{urllib.parse.urlencode(query)}"
    return checkout


def parse_paddle_signature(signature_header: str) -> Dict[str, str]:
    parts: Dict[str, str] = {}
    for part in (signature_header or "").split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            parts[key.strip()] = value.strip()
    return parts


def verify_paddle_signature(raw_body: bytes, signature_header: Optional[str], tolerance_seconds: int = 300) -> bool:
    if not PADDLE_WEBHOOK_SECRET:
        return False
    parts = parse_paddle_signature(signature_header or "")
    ts = parts.get("ts", "")
    h1 = parts.get("h1", "")
    if not ts or not h1:
        return False
    try:
        timestamp = int(ts)
        if abs(time.time() - timestamp) > tolerance_seconds:
            return False
    except Exception:
        return False
    signed = ts.encode("utf-8") + b":" + raw_body
    digest = hmac.new(PADDLE_WEBHOOK_SECRET.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, h1)


def extract_paddle_context(payload: Dict[str, Any]) -> Dict[str, str]:
    data = payload.get("data") or {}
    customer = data.get("customer") or {}
    custom = data.get("custom_data") or {}
    items = data.get("items") or []
    price_id = ""
    if isinstance(items, list) and items:
        first = items[0] or {}
        price = first.get("price") or {}
        price_id = str(price.get("id") or first.get("price_id") or "")
    if not price_id:
        price_id = str((data.get("price") or {}).get("id") or data.get("price_id") or "")
    email = str(customer.get("email") or data.get("customer_email") or data.get("email") or custom.get("email") or "")
    return {
        "event_id": str(payload.get("event_id") or payload.get("id") or data.get("id") or ""),
        "event_type": str(payload.get("event_type") or payload.get("type") or "unknown"),
        "email": email,
        "price_id": price_id,
        "plan": str(custom.get("plan") or paddle_plan_for_price(price_id)),
        "customer_id": str(data.get("customer_id") or customer.get("id") or ""),
        "subscription_id": str(data.get("subscription_id") or data.get("id") or ""),
    }


def store_paddle_event(event_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO paddle_webhook_events(event_id,event_type,payload_json,received_at) VALUES(?,?,?,?)",
            (event_id, event_type, jdump(payload), utcnow()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def upsert_paddle_subscription(email: str, plan: str, status: str, customer_id: str, subscription_id: str, price_id: str) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO paddle_subscriptions(email,plan,status,customer_id,subscription_id,price_id,updated_at)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            plan=excluded.plan,
            status=excluded.status,
            customer_id=excluded.customer_id,
            subscription_id=excluded.subscription_id,
            price_id=excluded.price_id,
            updated_at=excluded.updated_at
        """,
        (email, plan, status, customer_id, subscription_id, price_id, utcnow()),
    )
    if status == "active":
        conn.execute("UPDATE api_keys SET plan=? WHERE lower(email)=lower(?)", (plan, email))
    conn.commit()
    conn.close()


def paddle_status_for(email: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    conn = get_conn()
    resolved_email = email
    if not resolved_email and api_key:
        row = conn.execute("SELECT email FROM api_keys WHERE key=?", (api_key,)).fetchone()
        resolved_email = row["email"] if row else None
    sub = None
    if resolved_email:
        sub = conn.execute("SELECT * FROM paddle_subscriptions WHERE lower(email)=lower(?)", (resolved_email,)).fetchone()
    conn.close()
    return {
        "email": resolved_email,
        "provider": "paddle",
        "plan": sub["plan"] if sub else "free",
        "status": sub["status"] if sub else "inactive",
        "price_id": sub["price_id"] if sub else None,
        "updated_at": sub["updated_at"] if sub else None,
    }

def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def require_admin_token(admin_key: Optional[str], authorization: Optional[str]) -> None:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token and admin_key:
        token = admin_key
    if not secrets.compare_digest((token or "").encode(), (ADMIN_KEY or "").encode()):
        raise HTTPException(status_code=403, detail="Forbidden: valid admin bearer token required")


def init_commercial_db() -> None:
    conn = get_conn()

    # Existing legacy tables used by /v1/scan compatibility.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            scan_count INTEGER DEFAULT 0,
            email TEXT,
            created TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            decision TEXT,
            risk_score REAL,
            taxonomy_class TEXT,
            channel TEXT,
            objective TEXT,
            processing_ms INTEGER,
            ts TEXT
        )
    """)

    # Public/self-serve signup tracking.
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

    # Billing/upgrade requests. This avoids Stripe and supports manual/MoR providers.
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

    # Certify orders. Safe migrations allow coexistence with earlier tables.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certify_orders (
            order_id TEXT PRIMARY KEY,
            api_key TEXT,
            email TEXT,
            company TEXT,
            status TEXT DEFAULT 'requested',
            payment_provider TEXT DEFAULT 'manual_invoice',
            payment_status TEXT DEFAULT 'pending',
            package TEXT DEFAULT 'standard',
            target_type TEXT DEFAULT 'mobile_ai_agent',
            notes TEXT,
            created TEXT,
            paid_at TEXT,
            completed_at TEXT,
            score REAL,
            grade TEXT,
            adr REAL,
            fpr REAL,
            report_json TEXT
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

    conn.commit()
    conn.close()


init_commercial_db()

# ── Pydantic models ──────────────────────────────────────────────────────────

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




class PaddleCheckoutRequest(BaseModel):
    email: str
    company: Optional[str] = None
    plan: str = Field("pro", pattern="^(pro|certify)$")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

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

# ── Data helpers ─────────────────────────────────────────────────────────────

def signup_count_for_email_today(conn: sqlite3.Connection, email: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM public_signups WHERE lower(email)=lower(?) AND created_at >= ?",
        (email, today()),
    ).fetchone()
    return int(row["c"] or 0)


def create_public_api_key(email: str, company: Optional[str]) -> str:
    # Works with existing /v1/scan because it writes to legacy api_keys.
    return f"maisb_live_{secrets.token_urlsafe(24)}"


def get_usage_for_key(raw_key: str) -> Dict[str, Any]:
    conn = get_conn()
    row = conn.execute("SELECT key, plan, scan_count, email, created FROM api_keys WHERE key=?", (raw_key,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    plan = row["plan"] or "free"
    limit = PRO_TIER_MONTHLY_LIMIT if plan == "pro" else FREE_TIER_MONTHLY_LIMIT
    return {
        "api_key_masked": mask_key(row["key"]),
        "plan": plan,
        "scan_count": int(row["scan_count"] or 0),
        "limit": limit,
        "remaining": max(0, limit - int(row["scan_count"] or 0)),
        "email": row["email"],
        "created": row["created"],
    }


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

# ── Public / commercial endpoints ────────────────────────────────────────────

@router.get("/v1/commercial/health")
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
        "version": COMMERCIAL_VERSION,
        "features": {
            "vercel_dashboard_connected": True,
            "self_serve_api_key_signup": PUBLIC_SIGNUP_ENABLED,
            "stripe_direct_billing": False,
            "manual_invoice_billing": True,
            "merchant_of_record_ready": True,
            "paddle_webhook_billing": True,
            "resend_notifications": resend_enabled(),
            "certify_pdf_report": True,
            "certify_svg_badge": True,
        },
        "counts": {
            "public_keys": int(public_keys or 0),
            "signups": int(signups or 0),
            "billing_requests": int(billing or 0),
            "certify_orders": int(certify or 0),
        },
    }


@router.post("/v1/public/signup", tags=["Public Signup"])
def public_signup(body: PublicSignupRequest, request: Request) -> Dict[str, Any]:
    if not PUBLIC_SIGNUP_ENABLED:
        raise HTTPException(status_code=403, detail="Public signup is currently disabled")
    if REQUIRE_SIGNUP_INVITE_CODE and body.invite_code != SIGNUP_INVITE_CODE:
        raise HTTPException(status_code=403, detail="Valid invite code required")
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email required")

    conn = get_conn()
    if signup_count_for_email_today(conn, body.email) >= 3:
        conn.close()
        raise HTTPException(status_code=429, detail="Daily signup limit reached for this email")

    raw_key = create_public_api_key()
    masked = mask_key(raw_key)
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
            masked,
            ip_hash,
            request.headers.get("user-agent"),
            now,
        ),
    )
    conn.commit()
    conn.close()

    send_api_key_created_email(body.email, raw_key, masked)
    send_admin_notification("New MAISB public signup", f"{signup_id} · {body.email} · {body.company or 'no company'}")

    return {
        "created": True,
        "signup_id": signup_id,
        "api_key": raw_key,
        "api_key_masked": masked,
        "plan": "free",
        "monthly_limit": FREE_TIER_MONTHLY_LIMIT,
        "tenant_id": body.tenant_id,
        "warning": "Copy this API key now. Do not expose production keys in GitHub, screenshots, or reports.",
        "email_delivery": "configured" if resend_enabled() else "disabled",
    }


@router.get("/v1/public/usage")
def public_usage(api_key: str = Query(...)) -> Dict[str, Any]:
    return get_usage_for_key(api_key)


@router.get("/v1/public/dashboard")
def public_customer_dashboard(api_key: str = Query(...)) -> Dict[str, Any]:
    usage = get_usage_for_key(api_key)
    return {
        "customer": {
            "email": usage.get("email"),
            "plan": usage.get("plan"),
            "api_key_masked": usage.get("api_key_masked"),
        },
        "usage": usage,
        "quick_start": {
            "python": "pip install maisb-shield",
            "endpoint": f"{API_BASE_URL}/v1/scan",
            "channels": ["clipboard", "qr", "notification", "deep_link", "webview", "share_intent"],
        },
        "links": {
            "public_site": PUBLIC_BASE_URL,
            "api_docs": f"{API_BASE_URL}/docs",
            "dashboard": APP_DASHBOARD_URL,
            "soc_console": f"{APP_DASHBOARD_URL}/soc",
        },
    }


@router.get("/v1/public/plans")
def public_plans() -> Dict[str, Any]:
    return {
        "billing_mode": "manual_or_merchant_of_record",
        "stripe_direct_enabled": False,
        "paddle_enabled": PADDLE_ENABLED,
        "paddle_checkout_endpoint": "/v1/billing/paddle/checkout-session",
        "reason": "Stripe direct account flow is intentionally not used in this build. Use manual invoice, Paddle, or Lemon Squeezy style Merchant-of-Record flow.",
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


@router.post("/v1/billing/upgrade-request", tags=["Billing"])
def billing_upgrade_request(body: BillingRequest) -> Dict[str, Any]:
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid billing email required")
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
    send_billing_request_email(body.email, body.plan, request_id, body.company)
    return {
        "request_id": request_id,
        "status": "requested",
        "plan": body.plan,
        "provider": provider,
        "next_step": "Manual commercial review or merchant-of-record checkout. Do not treat frontend checkout success as provisioning.",
        "stripe_direct_enabled": False,
        "paddle_checkout_endpoint": "/v1/billing/paddle/checkout-session",
    }



@router.post("/v1/billing/paddle/checkout-session", tags=["Billing"])
def paddle_checkout_session(body: PaddleCheckoutRequest) -> Dict[str, Any]:
    checkout = paddle_checkout_config(body.email, body.plan, body.company, body.success_url, body.cancel_url)
    request_id = f"paddle_{secrets.token_hex(8)}"
    now = utcnow()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO billing_requests
        (request_id, email, company, plan, provider, status, notes, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'paddle', 'checkout_session_created', ?, ?, ?, ?)
        """,
        (
            request_id,
            body.email,
            body.company,
            body.plan,
            "Paddle checkout session created; awaiting signed webhook confirmation.",
            jdump({"checkout_url_present": bool(checkout.get("checkout_url")), "price_id": checkout.get("price_id")}),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    send_admin_notification("MAISB Paddle checkout created", f"{request_id} · {body.email} · {body.plan}")
    return {
        "request_id": request_id,
        "provider": "paddle",
        "provisioning": "pending_webhook_confirmation",
        "checkout": checkout,
        "checkout_url": checkout.get("checkout_url"),
    }


@router.post("/v1/billing/paddle/checkout-link", tags=["Billing"])
def paddle_checkout_link_compat(body: PaddleCheckoutRequest) -> Dict[str, Any]:
    """Backward-compatible alias for older dashboard code."""
    return paddle_checkout_session(body)


@router.post("/v1/billing/paddle/webhook", tags=["Billing"])
async def paddle_webhook(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    signature = request.headers.get("Paddle-Signature")
    if not verify_paddle_signature(raw, signature):
        raise HTTPException(status_code=401, detail="Invalid Paddle signature")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Paddle event JSON")
    ctx = extract_paddle_context(payload)
    if not ctx["event_id"]:
        raise HTTPException(status_code=400, detail="Missing Paddle event id")
    inserted = store_paddle_event(ctx["event_id"], ctx["event_type"], payload)
    if not inserted:
        return {"ok": True, "duplicate": True, "event_id": ctx["event_id"]}

    active_events = {"transaction.completed", "subscription.created", "subscription.updated", "subscription.resumed"}
    inactive_events = {"subscription.canceled", "subscription.paused"}
    if ctx["email"] and ctx["event_type"] in active_events:
        upsert_paddle_subscription(
            email=ctx["email"],
            plan=ctx["plan"],
            status="active",
            customer_id=ctx["customer_id"],
            subscription_id=ctx["subscription_id"] or ctx["event_id"],
            price_id=ctx["price_id"],
        )
        send_admin_notification("Paddle billing activated", f"{ctx['email']} · {ctx['plan']} · {ctx['event_type']}")
    elif ctx["email"] and ctx["event_type"] in inactive_events:
        upsert_paddle_subscription(
            email=ctx["email"],
            plan=ctx["plan"],
            status="inactive",
            customer_id=ctx["customer_id"],
            subscription_id=ctx["subscription_id"] or ctx["event_id"],
            price_id=ctx["price_id"],
        )
    return {"ok": True, "event_id": ctx["event_id"], "event_type": ctx["event_type"], "processed": True}


@router.get("/v1/billing/paddle/status", tags=["Billing"])
def paddle_billing_status(email: Optional[str] = Query(None), api_key: Optional[str] = Query(None)) -> Dict[str, Any]:
    return paddle_status_for(email=email, api_key=api_key)

# ── Certify endpoints# ── Certify endpoints ────────────────────────────────────────────────────────

@router.post("/v1/commercial/certify/start", tags=["MAISB Certify"])
def certify_start(body: CertifyStartRequest) -> Dict[str, Any]:
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email required")
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
    send_certify_started_email(body.email, order_id, body.company)
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

@router.get("/v1/commercial/certify/orders/{order_id}")
def certify_get_order(order_id: str) -> Dict[str, Any]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    return {"order": dict(row), "report": default_certify_report(row)}


@router.post("/v1/commercial/certify/orders/{order_id}/complete-demo", tags=["MAISB Certify"])
def certify_complete_demo(
    order_id: str,
    body: CertifyCompleteRequest,
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    require_admin_token(admin_key, authorization)
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
    row = conn.execute("SELECT email FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
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
    if row and row["email"]:
        send_certify_report_ready_email(
            row["email"],
            order_id,
            f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/report.pdf",
            f"{CERTIFY_BASE_URL}/v1/commercial/certify/orders/{order_id}/badge.svg",
        )
        send_admin_notification("MAISB Certify report ready", f"{order_id} · grade {grade} · score {body.score}")
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
<p class='muted'>This report is generated by MAISB. Do not publish private API keys, admin keys, payload samples, database files, or unredacted customer data.</p>
</div></body></html>"""


def make_simple_pdf(title: str, lines: List[str]) -> bytes:
    """Tiny dependency-free PDF writer, enough for a clean report download."""
    def esc(s: str) -> str:
        return str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = ["BT", "/F1 20 Tf", "72 760 Td", f"({esc(title)}) Tj"]
    content_lines += ["/F1 11 Tf", "0 -30 Td"]
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


@router.get("/v1/commercial/certify/orders/{order_id}/report.html", response_class=HTMLResponse)
def certify_report_html(order_id: str) -> HTMLResponse:
    conn = get_conn()
    row = conn.execute("SELECT * FROM certify_orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certify order not found")
    report = jload(row["report_json"], None) or default_certify_report(row)
    return HTMLResponse(render_report_html(report))


@router.get("/v1/commercial/certify/orders/{order_id}/report.pdf")
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


@router.get("/v1/commercial/certify/orders/{order_id}/badge.svg")
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


@router.get("/v1/commercial/admin/requests")
def commercial_admin_requests(
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    require_admin_token(admin_key, authorization)
    conn = get_conn()
    signups = [dict(r) for r in conn.execute("SELECT * FROM public_signups ORDER BY created_at DESC LIMIT 50").fetchall()]
    billing = [dict(r) for r in conn.execute("SELECT * FROM billing_requests ORDER BY created_at DESC LIMIT 50").fetchall()]
    certify = [dict(r) for r in conn.execute("SELECT order_id,email,company,status,payment_provider,payment_status,package,target_type,created,completed_at,score,grade FROM certify_orders ORDER BY created DESC LIMIT 50").fetchall()]
    conn.close()
    return {"signups": signups, "billing_requests": billing, "certify_orders": certify}
