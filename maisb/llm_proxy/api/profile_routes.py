# maisb/llm_proxy/api/profile_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Profile / Authentication Routes
# Provides email-verification-based account flow:
#   POST /v1/profile/signup         → Create pending profile, send verify email
#   POST /v1/profile/verify-email   → Mark profile verified (token in body)
#   GET  /v1/profile/status         → Check if verified, has API key
#   POST /v1/profile/api-keys       → Generate first API key (verified profiles only)
#   GET  /v1/profile/login          → Validate Bearer token for email
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
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("DB_PATH", "usage.db")
FREE_TIER_MONTHLY_LIMIT = int(os.environ.get("FREE_TIER_MONTHLY_LIMIT", "1000"))
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.maisb.app")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = (
    os.environ.get("RESEND_FROM")
    or os.environ.get("RESEND_FROM_EMAIL")
    or "MAISB <hello@updates.maisb.app>"
)
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")

VERIFY_TOKEN_TTL_HOURS = 24

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/profile", tags=["Profile"])

# ── Pydantic models ──────────────────────────────────────────────────────────


class ProfileSignupRequest(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    use_case: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    email: str
    token: str


class GenerateApiKeyRequest(BaseModel):
    email: str


# ── Utilities ─────────────────────────────────────────────────────────────────


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_valid_email(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            (value or "").strip(),
        )
    )


def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def resend_enabled() -> bool:
    return bool(RESEND_API_KEY and RESEND_FROM)


def send_resend_email(to_email: str, subject: str, html_body: str) -> bool:
    if not resend_enabled():
        return False
    payload: Dict[str, Any] = {
        "from": RESEND_FROM,
        "to": [to_email],
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
    except Exception as exc:
        LOGGER.warning("Resend delivery failed: %s", exc)
        return False


def send_verification_email(email: str, token: str) -> bool:
    verify_url = f"{APP_DASHBOARD_URL}/verify-email"
    body = (
        "<p>Thank you for signing up for MAISB Shield.</p>"
        "<p>Use the token below to verify your account. "
        "This token expires in 24 hours and is single-use.</p>"
        f"<p><b>Verification token:</b></p>"
        f"<pre style='background:#f1f5f9;padding:12px;border-radius:8px;font-size:1.1em'>"
        f"{html.escape(token)}</pre>"
        f"<p><a href='{html.escape(verify_url)}'>Click here to verify your account</a>"
        " and enter the token above.</p>"
    )
    return send_resend_email(
        email, "Verify your MAISB Shield account", body
    )


# ── Database initialisation ──────────────────────────────────────────────────


def _add_column_if_missing(
    conn: sqlite3.Connection, table: str, column: str, ddl: str
) -> None:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_profile_db() -> None:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id                  TEXT PRIMARY KEY,
            name                        TEXT,
            email                       TEXT NOT NULL,
            company                     TEXT,
            use_case                    TEXT,
            verified                    INTEGER NOT NULL DEFAULT 0,
            verification_token_hash     TEXT,
            verification_token_expires  TEXT,
            created_at                  TEXT NOT NULL,
            updated_at                  TEXT NOT NULL
        )
    """)
    # Unique index on normalised email (case-insensitive lookup)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_email ON profiles(lower(email))"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profile_api_keys (
            key_id      TEXT PRIMARY KEY,
            profile_id  TEXT NOT NULL,
            email       TEXT NOT NULL,
            key_hash    TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_profile_api_keys_hash "
        "ON profile_api_keys(key_hash)"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_profile_api_keys_email "
        "ON profile_api_keys(lower(email))"
    )
    conn.commit()
    conn.close()


init_profile_db()

# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/signup")
def profile_signup(body: ProfileSignupRequest) -> Dict[str, Any]:
    """
    Create a pending profile and send a verification email.
    Returns immediately; does NOT issue an API key yet.
    """
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail="Valid email address required")

    email = body.email.strip().lower()
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT profile_id, verified FROM profiles WHERE lower(email)=?",
            (email,),
        ).fetchone()

        if existing and existing["verified"]:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail="An account with this email is already verified. Please log in.",
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = sha256(raw_token)
        expires = (
            dt.datetime.utcnow() + dt.timedelta(hours=VERIFY_TOKEN_TTL_HOURS)
        ).replace(microsecond=0).isoformat()
        now = utcnow()

        if existing:
            conn.execute(
                """
                UPDATE profiles
                SET name=?, company=?, use_case=?,
                    verification_token_hash=?, verification_token_expires=?,
                    updated_at=?
                WHERE lower(email)=?
                """,
                (
                    body.name,
                    body.company,
                    body.use_case,
                    token_hash,
                    expires,
                    now,
                    email,
                ),
            )
        else:
            profile_id = f"profile_{secrets.token_hex(8)}"
            conn.execute(
                """
                INSERT INTO profiles
                (profile_id, name, email, company, use_case, verified,
                 verification_token_hash, verification_token_expires,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    body.name,
                    email,
                    body.company,
                    body.use_case,
                    token_hash,
                    expires,
                    now,
                    now,
                ),
            )

        conn.commit()
        conn.close()

        send_verification_email(email, raw_token)
        return {
            "created": True,
            "email": email,
            "next_step": (
                "Check your email and enter the verification token at /verify-email."
            ),
            "email_delivery": "configured" if resend_enabled() else "disabled",
        }

    except HTTPException:
        conn.close()
        raise
    except Exception as exc:
        conn.close()
        LOGGER.error("Profile signup error: %s", exc)
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")


@router.post("/verify-email")
def profile_verify_email(body: VerifyEmailRequest) -> Dict[str, Any]:
    """
    Verify an email address using the single-use token sent by /signup.
    Token is supplied in the request body (not a URL parameter).
    """
    email = body.email.strip().lower()
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=422, detail="Verification token is required")

    token_hash = sha256(token)
    conn = get_conn()
    row = conn.execute(
        """
        SELECT profile_id, verification_token_hash,
               verification_token_expires, verified
        FROM profiles
        WHERE lower(email)=?
        """,
        (email,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail="No account found for this email address"
        )

    if row["verified"]:
        conn.close()
        return {"verified": True, "email": email, "message": "Email already verified"}

    if row["verification_token_hash"] != token_hash:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid verification token")

    expires_str = row["verification_token_expires"]
    if expires_str:
        try:
            expires_dt = dt.datetime.fromisoformat(expires_str)
            if expires_dt < dt.datetime.utcnow():
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Verification token has expired. "
                        "Please sign up again to get a new token."
                    ),
                )
        except ValueError:
            pass  # unparseable expiry — still allow verification

    now = utcnow()
    conn.execute(
        """
        UPDATE profiles
        SET verified=1,
            verification_token_hash=NULL,
            verification_token_expires=NULL,
            updated_at=?
        WHERE profile_id=?
        """,
        (now, row["profile_id"]),
    )
    conn.commit()
    conn.close()
    return {
        "verified": True,
        "email": email,
        "message": "Email verified. You may now generate your API key.",
    }


@router.get("/status")
def profile_status(email: str = Query(...)) -> Dict[str, Any]:
    """Return whether the given email has a verified profile and/or an API key."""
    norm = email.strip().lower()
    conn = get_conn()
    row = conn.execute(
        "SELECT profile_id, verified FROM profiles WHERE lower(email)=?",
        (norm,),
    ).fetchone()
    if not row:
        conn.close()
        return {"exists": False, "verified": False, "has_api_key": False}
    has_key = (
        conn.execute(
            "SELECT 1 FROM profile_api_keys WHERE lower(email)=?",
            (norm,),
        ).fetchone()
        is not None
    )
    conn.close()
    return {
        "exists": True,
        "verified": bool(row["verified"]),
        "has_api_key": has_key,
    }


@router.post("/api-keys")
def profile_generate_api_key(body: GenerateApiKeyRequest) -> Dict[str, Any]:
    """
    Generate the first API key for a verified profile.
    Raw key is returned once only; only its SHA-256 hash is stored.
    The key is also inserted into the main api_keys table so /v1/scan works.
    """
    email = body.email.strip().lower()
    conn = get_conn()
    profile = conn.execute(
        "SELECT profile_id, verified FROM profiles WHERE lower(email)=?",
        (email,),
    ).fetchone()

    if not profile:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Account not found. Please sign up first.",
        )
    if not profile["verified"]:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email first.",
        )

    existing_key = conn.execute(
        "SELECT key_id FROM profile_api_keys WHERE lower(email)=?",
        (email,),
    ).fetchone()
    if existing_key:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="An API key already exists for this account.",
        )

    raw_key = f"maisb_live_{secrets.token_urlsafe(24)}"
    key_hash = sha256(raw_key)
    key_id = f"key_{secrets.token_hex(8)}"
    now = utcnow()

    conn.execute(
        """
        INSERT INTO profile_api_keys
        (key_id, profile_id, email, key_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (key_id, profile["profile_id"], email, key_hash, now),
    )
    # Register in main api_keys table so existing /v1/scan quota checks work
    conn.execute(
        "INSERT OR IGNORE INTO api_keys (key, plan, scan_count, email, created) "
        "VALUES (?, 'free', 0, ?, ?)",
        (raw_key, email, now),
    )
    conn.commit()
    conn.close()

    return {
        "created": True,
        "key_id": key_id,
        "api_key": raw_key,
        "email": email,
        "monthly_limit": FREE_TIER_MONTHLY_LIMIT,
        "warning": (
            "Copy this API key now. It will not be shown again. "
            "Do not commit it to GitHub, screenshots, or public reports."
        ),
    }


@router.get("/login")
def profile_login(
    email: str = Query(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Simple login check: validate that a Bearer token belongs to the given email.
    Returns authenticated=True and the key_id on success.
    """
    norm = email.strip().lower()
    raw_key = ""
    if authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization.split(" ", 1)[1].strip()
    if not raw_key:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required in Authorization header",
        )

    key_hash = sha256(raw_key)
    conn = get_conn()
    row = conn.execute(
        "SELECT key_id FROM profile_api_keys WHERE lower(email)=? AND key_hash=?",
        (norm, key_hash),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=401, detail="Invalid API key for this email address"
        )
    return {"authenticated": True, "email": norm, "key_id": row["key_id"]}
