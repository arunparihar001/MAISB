# maisb/llm_proxy/api/profile_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Profile & Auth Routes
#
# New enterprise auth flow (Resend.com-style):
#   POST /v1/profile/signup       → create profile, send verification email
#   POST /v1/profile/verify-email → mark profile as verified (token in body)
#   POST /v1/profile/login        → login with email, return profile data
#   POST /v1/profile/api-keys     → generate API key (raw key shown once, SHA256 in DB)
#
# Security:
#   - API keys: SHA256 hash stored in DB, raw key returned once
#   - Verification tokens: SHA256 hash in DB, 24hr expiry, single-use
#   - No API keys in URLs — only Bearer headers
#   - POST body for all sensitive operations
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

# ── Path setup (mirrors scan_api.py so this module finds shared helpers) ─────

THIS_FILE = Path(__file__).resolve()
API_DIR = THIS_FILE.parent
LLM_PROXY_DIR = API_DIR.parent
MAISB_DIR = LLM_PROXY_DIR.parent
REPO_ROOT = MAISB_DIR.parent
for p in (str(LLM_PROXY_DIR), str(MAISB_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Environment ───────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("DB_PATH", "usage.db")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = (
    os.environ.get("RESEND_FROM")
    or os.environ.get("RESEND_FROM_EMAIL")
    or "MAISB <hello@updates.maisb.app>"
)
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
TOKEN_EXPIRY_HOURS = 24

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/profile", tags=["Profile"])


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", (value or "").strip()))


_SAFE_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    # Validate identifiers to prevent SQL injection before using in dynamic DDL
    if not _SAFE_IDENTIFIER_RE.match(table):
        raise ValueError(f"Unsafe table name: {table!r}")
    if not _SAFE_IDENTIFIER_RE.match(column):
        raise ValueError(f"Unsafe column name: {column!r}")
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_profile_db() -> None:
    """Create Profile and APIKey tables if they don't exist."""
    conn = get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id    TEXT PRIMARY KEY,
            name          TEXT,
            email         TEXT NOT NULL UNIQUE,
            company       TEXT,
            use_case      TEXT,
            verified      INTEGER DEFAULT 0,
            token_hash    TEXT,
            token_expires TEXT,
            created_at    TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profile_api_keys (
            key_id     TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            email      TEXT NOT NULL,
            key_hash   TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
    """)

    # Safe migrations for older schemas
    for col, ddl in {
        "name": "name TEXT",
        "company": "company TEXT",
        "use_case": "use_case TEXT",
    }.items():
        add_column_if_missing(conn, "profiles", col, ddl)

    conn.commit()
    conn.close()


# Initialise on import
init_profile_db()


# ── Email helpers ─────────────────────────────────────────────────────────────

def resend_enabled() -> bool:
    return bool(RESEND_API_KEY and RESEND_FROM)


def send_resend_email(to: str, subject: str, html_body: str) -> bool:
    if not resend_enabled() or not to:
        return False
    payload: Dict[str, Any] = {
        "from": RESEND_FROM,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }
    if RESEND_REPLY_TO:
        payload["reply_to"] = RESEND_REPLY_TO
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception as exc:
        LOGGER.warning("Resend delivery failed: %s", exc)
        return False


def send_verification_email(email: str, raw_token: str) -> bool:
    verify_url = f"{APP_DASHBOARD_URL}/verify-email?token={raw_token}"
    body = (
        "<p>Thanks for signing up for MAISB Shield.</p>"
        "<p>Verify your email address by clicking the link below (valid 24 hours):</p>"
        f"<p><a href='{html.escape(verify_url)}'>{html.escape(verify_url)}</a></p>"
        "<p>If you did not sign up, ignore this email.</p>"
    )
    return send_resend_email(email, "Verify your MAISB Shield account", body)


def send_api_key_email(email: str, raw_key: str) -> bool:
    body = (
        "<p>Your MAISB Shield API key was created.</p>"
        f"<p><b>Key (shown once):</b></p><pre>{html.escape(raw_key)}</pre>"
        "<p>Store this key securely. Do not commit it to GitHub, "
        "screenshots, mobile apps, or public reports.</p>"
        f"<p><a href='{html.escape(APP_DASHBOARD_URL)}'>Open dashboard</a></p>"
    )
    return send_resend_email(email, "Your MAISB Shield API key", body)


# ── Bearer token helper ───────────────────────────────────────────────────────

def bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return authorization.strip()


def require_profile_by_email(email: str) -> sqlite3.Row:
    """Return a verified profile row or raise 401."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM profiles WHERE lower(email)=lower(?)",
        (email,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Profile not found. Use POST /v1/profile/signup first.")
    if not row["verified"]:
        raise HTTPException(status_code=403, detail="Email not verified. Check your inbox and verify first.")
    return row


def resolve_api_key_from_bearer(authorization: Optional[str]) -> Optional[str]:
    """
    Given an Authorization header, return the email associated with the
    profile_api_keys entry (hashed lookup).  Returns None if not found.
    """
    token = bearer_token(authorization)
    if not token:
        return None
    token_hash = sha256(token)
    conn = get_conn()
    row = conn.execute(
        "SELECT email FROM profile_api_keys WHERE key_hash=?",
        (token_hash,),
    ).fetchone()
    conn.close()
    return row["email"] if row else None


# ── Request / response models ─────────────────────────────────────────────────

class ProfileSignupRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    use_case: Optional[str] = Field(default="Android / AI agent runtime protection")


class VerifyEmailRequest(BaseModel):
    token: str


class ProfileLoginRequest(BaseModel):
    email: str


class CreateApiKeyRequest(BaseModel):
    email: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/signup")
def profile_signup(body: ProfileSignupRequest, request: Request) -> Dict[str, Any]:
    """
    Create a new profile and send a verification email.
    Returns profile_id and indicates whether email was sent.
    """
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=422, detail="Name is required")
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email is required")

    conn = get_conn()
    existing = conn.execute(
        "SELECT profile_id, verified FROM profiles WHERE lower(email)=lower(?)",
        (body.email,),
    ).fetchone()

    if existing:
        if existing["verified"]:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail="Email already registered and verified. Use POST /v1/profile/login.",
            )
        # Re-send verification for unverified profiles
        profile_id = existing["profile_id"]
    else:
        profile_id = f"prof_{secrets.token_hex(8)}"
        now = utcnow()
        conn.execute(
            """
            INSERT INTO profiles (profile_id, name, email, company, use_case, verified, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (profile_id, body.name.strip(), body.email.strip(), body.company, body.use_case, now),
        )

    # Generate a single-use verification token (store SHA256 hash)
    raw_token = secrets.token_urlsafe(32)
    token_hash = sha256(raw_token)
    token_expires = (dt.datetime.utcnow() + dt.timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()

    conn.execute(
        "UPDATE profiles SET token_hash=?, token_expires=? WHERE profile_id=?",
        (token_hash, token_expires, profile_id),
    )
    conn.commit()
    conn.close()

    email_sent = send_verification_email(body.email.strip(), raw_token)

    return {
        "created": True,
        "profile_id": profile_id,
        "email": body.email.strip(),
        "verified": False,
        "next_step": "Check your inbox and click the verification link, then POST /v1/profile/login",
        "email_sent": email_sent,
    }


@router.post("/verify-email")
def profile_verify_email(body: VerifyEmailRequest) -> Dict[str, Any]:
    """
    Verify a profile using the raw token from the email link.
    Token is in the POST body (never in URLs for security).
    """
    if not body.token:
        raise HTTPException(status_code=422, detail="Token is required")

    token_hash = sha256(body.token)
    now_str = dt.datetime.utcnow().isoformat()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM profiles WHERE token_hash=?",
        (token_hash,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or already-used verification token")
    if row["token_expires"] and row["token_expires"] < now_str:
        conn.close()
        raise HTTPException(status_code=400, detail="Verification token has expired. Request a new one via signup.")
    if row["verified"]:
        conn.close()
        return {"verified": True, "email": row["email"], "already_verified": True}

    # Mark verified and clear the token (single-use)
    conn.execute(
        "UPDATE profiles SET verified=1, token_hash=NULL, token_expires=NULL WHERE profile_id=?",
        (row["profile_id"],),
    )
    conn.commit()
    conn.close()

    return {
        "verified": True,
        "email": row["email"],
        "next_step": "POST /v1/profile/login",
    }


@router.post("/login")
def profile_login(body: ProfileLoginRequest) -> Dict[str, Any]:
    """
    Login by email. Returns profile data and whether a key exists.
    """
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email is required")

    profile = require_profile_by_email(body.email)
    conn = get_conn()
    key_count = conn.execute(
        "SELECT COUNT(*) AS c FROM profile_api_keys WHERE lower(email)=lower(?)",
        (body.email,),
    ).fetchone()["c"]
    conn.close()

    return {
        "profile_id": profile["profile_id"],
        "name": profile["name"],
        "email": profile["email"],
        "company": profile["company"],
        "use_case": profile["use_case"],
        "verified": bool(profile["verified"]),
        "created_at": profile["created_at"],
        "has_api_key": key_count > 0,
        "next_step": "POST /v1/profile/api-keys" if key_count == 0 else "Use Bearer token in API requests",
    }


@router.post("/api-keys")
def profile_create_api_key(body: CreateApiKeyRequest) -> Dict[str, Any]:
    """
    Generate a new API key for a verified profile.
    The raw key is returned ONCE and never stored in plaintext.
    """
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email is required")

    profile = require_profile_by_email(body.email)

    raw_key = f"maisb_live_{secrets.token_urlsafe(32)}"
    key_hash = sha256(raw_key)
    key_id = f"key_{secrets.token_hex(8)}"
    now = utcnow()

    conn = get_conn()
    # Check for existing keys — allow generating additional keys
    conn.execute(
        """
        INSERT INTO profile_api_keys (key_id, profile_id, email, key_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (key_id, profile["profile_id"], body.email.strip(), key_hash, now),
    )
    conn.commit()
    conn.close()

    send_api_key_email(body.email.strip(), raw_key)

    return {
        "key_id": key_id,
        "raw_key": raw_key,
        "email": body.email.strip(),
        "created_at": now,
        "warning": (
            "Copy this key now — it will not be shown again. "
            "Store securely. Do not commit to GitHub or screenshots."
        ),
    }


@router.get("/keys")
def profile_list_keys(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    List API keys (masked) for the authenticated profile.
    Requires Bearer token in Authorization header.
    """
    email = resolve_api_key_from_bearer(authorization)
    if not email:
        raise HTTPException(status_code=401, detail="Valid Bearer token required")

    conn = get_conn()
    rows = conn.execute(
        "SELECT key_id, email, created_at FROM profile_api_keys WHERE lower(email)=lower(?)",
        (email,),
    ).fetchall()
    conn.close()

    return {
        "email": email,
        "keys": [
            {"key_id": r["key_id"], "email": r["email"], "created_at": r["created_at"]}
            for r in rows
        ],
    }
