from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
from email.utils import parseaddr
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import jwt
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from passlib.context import CryptContext
from pydantic import BaseModel, Field

THIS_FILE = Path(__file__).resolve()
API_DIR = THIS_FILE.parent
LLM_PROXY_DIR = API_DIR.parent
MAISB_DIR = LLM_PROXY_DIR.parent
REPO_ROOT = MAISB_DIR.parent
for p in (str(LLM_PROXY_DIR), str(MAISB_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

DB_PATH = os.environ.get("DB_PATH", "usage.db")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM") or os.environ.get("RESEND_FROM_EMAIL") or "hello@updates.maisb.app"
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
SESSION_SECRET = (
    os.environ.get("JWT_SECRET")
    or os.environ.get("MAISB_JWT_SECRET")
    or os.environ.get("SESSION_SECRET")
    or os.environ.get("ADMIN_KEY")
    or "dev_only_session_secret"
)
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "12"))
TOKEN_EXPIRY_HOURS = 24

LOGGER = logging.getLogger(__name__)
PASSWORD_CTX = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_DIAGNOSTIC_MESSAGE_LENGTH = 200
RESEND_CONNECT_TIMEOUT = 5.0
RESEND_READ_TIMEOUT = 8.0
RESEND_WRITE_TIMEOUT = 8.0
RESEND_POOL_TIMEOUT = 8.0
_LAST_RESEND_DIAGNOSTICS: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "last_resend_diagnostics",
    default=None,
)

router = APIRouter(tags=["SaaS"])


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


def is_production_env() -> bool:
    checks = [
        os.environ.get("APP_ENV", ""),
        os.environ.get("ENVIRONMENT", ""),
        os.environ.get("ENV", ""),
        os.environ.get("RAILWAY_ENVIRONMENT", ""),
    ]
    return any(v.lower() in {"prod", "production"} for v in checks if v)


if is_production_env() and SESSION_SECRET in {"", "dev_only_session_secret", "change_me_in_production"}:
    LOGGER.warning("JWT secret is not configured. Set JWT_SECRET or MAISB_JWT_SECRET in production.")


def bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return authorization.strip()


def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if not _SAFE_IDENTIFIER_RE.match(table):
        raise ValueError(f"Unsafe table name: {table!r}")
    if not _SAFE_IDENTIFIER_RE.match(column):
        raise ValueError(f"Unsafe column name: {column!r}")
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def init_profile_db() -> None:
    conn = get_conn()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            company       TEXT,
            use_case      TEXT,
            password_hash TEXT,
            verified      INTEGER DEFAULT 0,
            plan          TEXT DEFAULT 'free',
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        )
        """
    )

    profile_cols = table_columns(conn, "profiles")
    if "profile_id" in profile_cols:
        conn.execute("UPDATE profiles SET id=profile_id WHERE (id IS NULL OR id='') AND profile_id IS NOT NULL")

    for col, ddl in {
        "id": "id TEXT",
        "name": "name TEXT",
        "company": "company TEXT",
        "use_case": "use_case TEXT",
        "password_hash": "password_hash TEXT",
        "verified": "verified INTEGER DEFAULT 0",
        "plan": "plan TEXT DEFAULT 'free'",
        "created_at": "created_at TEXT",
        "updated_at": "updated_at TEXT",
    }.items():
        add_column_if_missing(conn, "profiles", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS email_verifications (
            id         TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at    TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    for col, ddl in {
        "id": "id TEXT",
        "profile_id": "profile_id TEXT",
        "token_hash": "token_hash TEXT",
        "expires_at": "expires_at TEXT",
        "used_at": "used_at TEXT",
        "created_at": "created_at TEXT",
    }.items():
        add_column_if_missing(conn, "email_verifications", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            key            TEXT PRIMARY KEY,
            plan           TEXT DEFAULT 'free',
            scan_count     INTEGER DEFAULT 0,
            email          TEXT,
            created        TEXT,
            key_id         TEXT UNIQUE,
            profile_id     TEXT,
            key_hash       TEXT,
            key_prefix     TEXT,
            name           TEXT,
            scopes_json    TEXT,
            status         TEXT DEFAULT 'active',
            created_at     TEXT,
            last_used_at   TEXT,
            revoked_at     TEXT
        )
        """
    )

    # Keep legacy scan API columns alongside the newer profile-aware fields so
    # old Railway DBs and /v1/scan compatibility remain intact during deploys.
    for col, ddl in {
        "key": "key TEXT",
        "plan": "plan TEXT DEFAULT 'free'",
        "scan_count": "scan_count INTEGER DEFAULT 0",
        "email": "email TEXT",
        "created": "created TEXT",
        "key_id": "key_id TEXT",
        "profile_id": "profile_id TEXT",
        "key_hash": "key_hash TEXT",
        "key_prefix": "key_prefix TEXT",
        "name": "name TEXT",
        "scopes_json": "scopes_json TEXT",
        "status": "status TEXT DEFAULT 'active'",
        "created_at": "created_at TEXT",
        "last_used_at": "last_used_at TEXT",
        "revoked_at": "revoked_at TEXT",
    }.items():
        add_column_if_missing(conn, "api_keys", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profile_api_keys (
            key_id     TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            email      TEXT NOT NULL,
            key_hash   TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )
    for col, ddl in {
        "key_id": "key_id TEXT",
        "profile_id": "profile_id TEXT",
        "email": "email TEXT",
        "key_hash": "key_hash TEXT",
        "created_at": "created_at TEXT",
    }.items():
        add_column_if_missing(conn, "profile_api_keys", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id      TEXT,
            api_key_id      TEXT,
            decision        TEXT,
            risk_score      REAL,
            taxonomy_class  TEXT,
            channel         TEXT,
            objective       TEXT,
            trace_id        TEXT,
            boundary_status TEXT,
            created_at      TEXT NOT NULL
        )
        """
    )
    for col, ddl in {
        "id": "id INTEGER",
        "profile_id": "profile_id TEXT",
        "api_key_id": "api_key_id TEXT",
        "decision": "decision TEXT",
        "risk_score": "risk_score REAL",
        "taxonomy_class": "taxonomy_class TEXT",
        "channel": "channel TEXT",
        "objective": "objective TEXT",
        "trace_id": "trace_id TEXT",
        "boundary_status": "boundary_status TEXT",
        "created_at": "created_at TEXT",
    }.items():
        add_column_if_missing(conn, "scan_events", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cross_channel_traces (
            trace_id           TEXT PRIMARY KEY,
            profile_id         TEXT,
            channels_json      TEXT,
            trust_score        REAL,
            degradation_score  REAL,
            final_decision     TEXT,
            created_at         TEXT NOT NULL,
            updated_at         TEXT NOT NULL
        )
        """
    )
    for col, ddl in {
        "trace_id": "trace_id TEXT",
        "profile_id": "profile_id TEXT",
        "channels_json": "channels_json TEXT",
        "trust_score": "trust_score REAL",
        "degradation_score": "degradation_score REAL",
        "final_decision": "final_decision TEXT",
        "created_at": "created_at TEXT",
        "updated_at": "updated_at TEXT",
    }.items():
        add_column_if_missing(conn, "cross_channel_traces", col, ddl)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id    TEXT,
            action        TEXT NOT NULL,
            metadata_json TEXT,
            created_at    TEXT NOT NULL
        )
        """
    )
    for col, ddl in {
        "id": "id INTEGER",
        "profile_id": "profile_id TEXT",
        "action": "action TEXT",
        "metadata_json": "metadata_json TEXT",
        "created_at": "created_at TEXT",
    }.items():
        add_column_if_missing(conn, "activity_logs", col, ddl)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(lower(email))")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_profile_status ON api_keys(profile_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_events_profile_created ON scan_events(profile_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_traces_profile ON cross_channel_traces(profile_id, updated_at)")

    conn.commit()
    conn.close()


init_profile_db()


def resend_enabled() -> bool:
    return bool(RESEND_API_KEY and _resend_from_address())


def _resend_from_address() -> str:
    """Return the canonical bare Resend sender email address."""
    value = (RESEND_FROM or "").strip()
    if not value:
        return ""
    parsed = parseaddr(value)[1].strip()
    if is_valid_email(parsed):
        return parsed
    if is_valid_email(value):
        return value
    LOGGER.warning("Invalid Resend sender configured: %s", value)
    return ""


def get_last_resend_diagnostics() -> Optional[Dict[str, Any]]:
    """Return the most recent request-scoped Resend diagnostics."""
    diagnostics = _LAST_RESEND_DIAGNOSTICS.get()
    if diagnostics is None:
        return None
    return diagnostics


def _set_last_resend_diagnostics(diagnostics: Optional[Dict[str, Any]]) -> None:
    if diagnostics is None:
        _LAST_RESEND_DIAGNOSTICS.set(None)
    else:
        _LAST_RESEND_DIAGNOSTICS.set(dict(diagnostics))


def _safe_resend_diagnostics_from_response(response: httpx.Response) -> Dict[str, Any]:
    """Extract Resend error details while tolerating malformed responses."""
    try:
        diagnostics: Dict[str, Any] = {"provider": "resend", "status_code": response.status_code}
        # `x-request-id` is the current Resend request ID header; `x-resend-request-id` is a legacy variant.
        request_id = response.headers.get("x-request-id") or response.headers.get("x-resend-request-id")
        if request_id:
            diagnostics["request_id"] = request_id

        try:
            body = response.json()
        except ValueError:
            body = None

        if body is not None:
            diagnostics["provider_error"] = body
        if isinstance(body, dict):
            for key in ("error", "name", "message", "code"):
                value = body.get(key)
                if isinstance(value, str) and value.strip():
                    diagnostics[key] = value.strip()[:MAX_DIAGNOSTIC_MESSAGE_LENGTH]
        else:
            text = response.text.strip()
            if text:
                diagnostics["provider_error"] = text
                diagnostics["message"] = text[:MAX_DIAGNOSTIC_MESSAGE_LENGTH]

        return diagnostics
    except Exception as exc:
        return {
            "provider": "resend",
            "error": "diagnostic_error",
            "message": str(exc)[:MAX_DIAGNOSTIC_MESSAGE_LENGTH],
        }


def send_resend_email(to: str, subject: str, html_body: str) -> bool:
    # Reset request-scoped diagnostics before each send attempt.
    _set_last_resend_diagnostics(None)
    if not resend_enabled() or not to:
        return False
    from_address = _resend_from_address()
    payload: Dict[str, Any] = {
        "from": from_address,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }
    if RESEND_REPLY_TO:
        payload["reply_to"] = RESEND_REPLY_TO
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "MAISB/1.0",
            },
            timeout=httpx.Timeout(
                connect=RESEND_CONNECT_TIMEOUT,
                read=RESEND_READ_TIMEOUT,
                write=RESEND_WRITE_TIMEOUT,
                pool=RESEND_POOL_TIMEOUT,
            ),
        )
        response.raise_for_status()
        return True
    except httpx.HTTPStatusError as exc:
        diagnostics = _safe_resend_diagnostics_from_response(exc.response)
        _set_last_resend_diagnostics(diagnostics)
        LOGGER.warning("Resend delivery failed: %s", diagnostics)
        return False
    except httpx.RequestError as exc:
        diagnostics = {
            "provider": "resend",
            "error": "request_error",
            "message": str(exc)[:MAX_DIAGNOSTIC_MESSAGE_LENGTH],
        }
        _set_last_resend_diagnostics(diagnostics)
        LOGGER.warning("Resend delivery failed: %s", diagnostics)
        return False


def send_verification_email(email: str, raw_token: str) -> bool:
    verify_url = f"{APP_DASHBOARD_URL.rstrip('/')}/verify-email"
    body = (
        "<p>Thanks for signing up for MAISB.</p>"
        f"<p><a href='{html.escape(verify_url)}'>Verify your email</a></p>"
        "<p>Or use this verification token in <code>POST /v1/profile/verify-email</code>.</p>"
        f"<pre>{html.escape(raw_token)}</pre>"
        "<p>This token expires in 24 hours and can only be used once.</p>"
        f"<p><a href='{html.escape(APP_DASHBOARD_URL)}'>Open dashboard</a></p>"
    )
    return send_resend_email(email, "Verify your MAISB account", body)


def safe_log_activity(profile_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    try:
        log_activity(profile_id, action, metadata)
    except Exception as exc:
        LOGGER.warning("Activity log failed for %s: %s", action, exc)


def hash_password(password: str) -> str:
    try:
        return PASSWORD_CTX.hash(password)
    except Exception as exc:
        LOGGER.warning("bcrypt hashing failed, falling back to pbkdf2_sha256: %s", exc)
        return PASSWORD_CTX.hash(password, scheme="pbkdf2_sha256")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return PASSWORD_CTX.verify(password, password_hash)
    except Exception as exc:
        LOGGER.warning("Password verification encountered an unexpected error; returning False: %s", exc)
        return False


def profile_id_from_row(row: sqlite3.Row) -> str:
    fallback = row["profile_id"] if "profile_id" in row.keys() else ""
    return str(row["id"] or fallback or "")


def log_activity(profile_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO activity_logs (profile_id, action, metadata_json, created_at) VALUES (?, ?, ?, ?)",
        (profile_id, action, json.dumps(metadata or {}, separators=(",", ":"), ensure_ascii=False), utcnow()),
    )
    conn.commit()
    conn.close()


def create_session_token(profile_id: str, email: str) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": profile_id,
        "email": email,
        "typ": "session",
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(hours=SESSION_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm="HS256")


def resolve_profile_from_bearer(authorization: Optional[str], allow_api_key: bool) -> Tuple[sqlite3.Row, str]:
    token = bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail={"error": "unauthorized", "message": "Authorization: Bearer token required"})

    conn = get_conn()

    try:
        payload = jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
        if payload.get("typ") == "session" and payload.get("sub"):
            row = conn.execute("SELECT * FROM profiles WHERE id=?", (payload["sub"],)).fetchone()
            if row and row["verified"]:
                conn.close()
                return row, "session"
    except Exception:
        pass

    if allow_api_key:
        key_hash = sha256(token)
        key_row = conn.execute(
            "SELECT profile_id, key_id FROM api_keys WHERE key_hash=? AND COALESCE(status,'active')='active'",
            (key_hash,),
        ).fetchone()
        if key_row and key_row["profile_id"]:
            profile = conn.execute("SELECT * FROM profiles WHERE id=?", (key_row["profile_id"],)).fetchone()
            if profile:
                conn.execute("UPDATE api_keys SET last_used_at=? WHERE key_hash=?", (utcnow(), key_hash))
                conn.commit()
                conn.close()
                return profile, "api_key"

        bridge = conn.execute("SELECT profile_id FROM profile_api_keys WHERE key_hash=?", (key_hash,)).fetchone()
        if bridge:
            profile = conn.execute("SELECT * FROM profiles WHERE id=?", (bridge["profile_id"],)).fetchone()
            if profile:
                conn.close()
                return profile, "api_key"

    conn.close()
    raise HTTPException(status_code=401, detail={"error": "unauthorized", "message": "Invalid or expired Bearer token"})


def collect_scan_events(profile_id: str, since_iso: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_conn()
    if since_iso:
        rows = conn.execute(
            "SELECT * FROM scan_events WHERE profile_id=? AND created_at>=? ORDER BY created_at ASC",
            (profile_id, since_iso),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM scan_events WHERE profile_id=? ORDER BY created_at ASC", (profile_id,)).fetchall()
    conn.close()
    return rows


def decision_reason(decision: str) -> str:
    if decision == "BLOCKED":
        return "MAISB blocked due to high risk score and policy boundary threshold"
    if decision == "REVIEW":
        return "MAISB requested manual review because risk signals crossed review threshold"
    return "MAISB allowed request because risk remained within acceptable boundaries"


class ProfileSignupRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    use_case: Optional[str] = Field(default="Android / AI agent runtime protection")
    password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class ProfileLoginRequest(BaseModel):
    email: str
    password: str


class PlanSelectRequest(BaseModel):
    plan: str = Field(pattern="^(free|pro|certify)$")


class APIKeyCreateRequest(BaseModel):
    name: Optional[str] = "Default key"
    scopes: List[str] = Field(default_factory=lambda: ["scan"])


class ComplianceRequest(BaseModel):
    framework: str = Field(default="soc2")


class ScheduleReportRequest(BaseModel):
    cadence: str = Field(default="weekly", pattern="^(daily|weekly|monthly)$")


class TeamInviteRequest(BaseModel):
    email: str
    role: str = Field(default="viewer")


class TeamRolePatchRequest(BaseModel):
    role: str = Field(default="viewer")


@router.post("/v1/profile/signup")
def profile_signup(body: ProfileSignupRequest) -> Dict[str, Any]:
    if not body.name.strip():
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Name is required"})
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Valid email is required"})

    email = body.email.strip().lower()
    now = utcnow()
    conn = get_conn()
    created = False
    raw_token = ""
    profile_id = ""
    try:
        cols = table_columns(conn, "profiles")
        existing = conn.execute("SELECT * FROM profiles WHERE lower(email)=lower(?)", (email,)).fetchone()
        if existing and existing["verified"]:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please log in.",
            )

        profile_id = str(existing["id"]) if existing and existing["id"] else f"prof_{secrets.token_hex(8)}"
        new_password_hash = hash_password(body.password)
        stored_password_hash = new_password_hash

        if existing is None:
            try:
                if "profile_id" in cols:
                    conn.execute(
                        "INSERT INTO profiles (id, profile_id, name, email, company, use_case, password_hash, verified, plan, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'free', ?, ?)",
                        (profile_id, profile_id, body.name.strip(), email, body.company, body.use_case, stored_password_hash, now, now),
                    )
                else:
                    conn.execute(
                        "INSERT INTO profiles (id, name, email, company, use_case, password_hash, verified, plan, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, 'free', ?, ?)",
                        (profile_id, body.name.strip(), email, body.company, body.use_case, stored_password_hash, now, now),
                    )
                created = True
            except sqlite3.IntegrityError:
                conn.rollback()
                existing = conn.execute("SELECT * FROM profiles WHERE lower(email)=lower(?)", (email,)).fetchone()
                if existing and existing["verified"]:
                    raise HTTPException(
                        status_code=409,
                        detail="An account with this email already exists. Please log in.",
                    )
                if existing and existing["id"]:
                    profile_id = str(existing["id"])
        else:
            update_result = conn.execute(
                "UPDATE profiles SET name=?, company=?, use_case=?, password_hash=?, updated_at=? WHERE lower(email)=lower(?) AND COALESCE(verified, 0)=0",
                (body.name.strip(), body.company, body.use_case, new_password_hash, now, email),
            )
            if update_result.rowcount == 0:
                current = conn.execute("SELECT verified FROM profiles WHERE lower(email)=lower(?)", (email,)).fetchone()
                if current and current["verified"]:
                    raise HTTPException(
                        status_code=409,
                        detail="An account with this email already exists. Please log in.",
                    )
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "signup_failed",
                        "message": "Unable to create or update the signup record.",
                    },
                )

        raw_token = secrets.token_urlsafe(32)
        token_hash = sha256(raw_token)
        verification_id = f"ver_{secrets.token_hex(10)}"
        expires_at = (dt.datetime.utcnow() + dt.timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()
        conn.execute(
            "INSERT INTO email_verifications (id, profile_id, token_hash, expires_at, used_at, created_at) VALUES (?, ?, ?, ?, NULL, ?)",
            (verification_id, profile_id, token_hash, expires_at, now),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        LOGGER.warning("Signup failed due to database integrity constraint violation: %s", exc)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "signup_conflict",
                "message": "Unable to complete signup because this email is already in use.",
            },
        )
    except Exception as exc:
        conn.rollback()
        LOGGER.exception("Signup failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "signup_failed",
                "message": "Signup could not be completed.",
            },
        ) from exc
    finally:
        conn.close()

    email_sent = send_verification_email(email, raw_token)
    if resend_enabled() and not email_sent:
        diagnostics = get_last_resend_diagnostics() or {"provider": "resend", "error": "failed"}
        safe_log_activity(
            profile_id,
            "profile_signup_email_failed",
            {"email": email, "email_sent": email_sent, "diagnostics": diagnostics},
        )
        raise HTTPException(
            status_code=502,
            detail={
                "error": "verification_email_failed",
                "message": "Verification email could not be sent. Please try again later.",
                "profile_id": profile_id,
                "email": email,
                "diagnostics": diagnostics,
            },
        )

    response: Dict[str, Any] = {
        "created": created,
        "status": "pending_verification",
        "profile_id": profile_id,
        "email": email,
        "email_sent": email_sent,
    }
    response["message"] = "Verification email sent." if created else "Verification email resent."
    if not email_sent and not is_production_env() and not resend_enabled():
        response["dev_verification_token"] = raw_token

    safe_log_activity(profile_id, "profile_signup", {"email": email, "email_sent": email_sent, "created": created})
    return response


@router.post("/v1/profile/verify-email")
def profile_verify_email(body: VerifyEmailRequest) -> Dict[str, Any]:
    if not body.token.strip():
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Token is required"})

    token_hash = sha256(body.token.strip())
    now = dt.datetime.utcnow().isoformat()

    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM email_verifications WHERE token_hash=? AND used_at IS NULL ORDER BY created_at DESC LIMIT 1",
        (token_hash,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "invalid_token", "message": "Invalid or already-used verification token"})

    if row["expires_at"] < now:
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "token_expired", "message": "Verification token expired"})

    conn.execute("UPDATE email_verifications SET used_at=? WHERE id=?", (utcnow(), row["id"]))
    conn.execute("UPDATE profiles SET verified=1, updated_at=? WHERE id=?", (utcnow(), row["profile_id"]))
    email_row = conn.execute("SELECT email FROM profiles WHERE id=?", (row["profile_id"],)).fetchone()
    conn.commit()
    conn.close()

    safe_log_activity(row["profile_id"], "profile_verify_email", {"email": email_row["email"] if email_row else None})
    return {"verified": True, "email": email_row["email"] if email_row else None}


@router.post("/v1/profile/login")
def profile_login(body: ProfileLoginRequest) -> Dict[str, Any]:
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Valid email is required"})

    conn = get_conn()
    profile = conn.execute("SELECT * FROM profiles WHERE lower(email)=lower(?)", (body.email.strip().lower(),)).fetchone()
    conn.close()

    if not profile:
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Invalid email or password"})
    if not profile["password_hash"] or not verify_password(body.password, profile["password_hash"]):
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Invalid email or password"})
    if not profile["verified"]:
        raise HTTPException(status_code=403, detail={"error": "email_not_verified", "message": "Verify your email before login"})

    token = create_session_token(profile["id"], profile["email"])
    safe_log_activity(profile["id"], "profile_login", {"email": profile["email"]})
    return {
        "token_type": "Bearer",
        "session_token": token,
        "expires_in_seconds": SESSION_TTL_HOURS * 3600,
        "profile": {
            "id": profile["id"],
            "name": profile["name"],
            "email": profile["email"],
            "company": profile["company"],
            "use_case": profile["use_case"],
            "verified": bool(profile["verified"]),
            "plan": profile["plan"] or "free",
        },
    }


@router.get("/v1/profile/me")
def profile_me(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, auth_type = resolve_profile_from_bearer(authorization, allow_api_key=True)
    return {
        "id": profile["id"],
        "name": profile["name"],
        "email": profile["email"],
        "company": profile["company"],
        "use_case": profile["use_case"],
        "verified": bool(profile["verified"]),
        "plan": profile["plan"] or "free",
        "auth_type": auth_type,
    }


@router.get("/v1/profile/status")
def profile_status(email: str = Query(...)) -> Dict[str, Any]:
    if not is_valid_email(email):
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Valid email is required"})

    conn = get_conn()
    row = conn.execute("SELECT id, verified, plan, created_at, updated_at FROM profiles WHERE lower(email)=lower(?)", (email.strip().lower(),)).fetchone()
    conn.close()

    if not row:
        return {"exists": False, "email": email.strip().lower()}
    return {
        "exists": True,
        "email": email.strip().lower(),
        "verified": bool(row["verified"]),
        "plan": row["plan"] or "free",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/v1/plans")
def get_plans() -> Dict[str, Any]:
    return {
        "plans": [
            {"code": "free", "name": "Free", "selected": False, "coming_soon": False},
            {"code": "pro", "name": "Pro", "selected": False, "coming_soon": True, "request_invoice": True},
            {"code": "certify", "name": "Certify", "selected": False, "coming_soon": True, "request_invoice": True},
        ]
    }


@router.post("/v1/plans/select")
def select_plan(body: PlanSelectRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    selected_plan = body.plan.lower()

    if selected_plan == "free":
        conn = get_conn()
        conn.execute("UPDATE profiles SET plan='free', updated_at=? WHERE id=?", (utcnow(), profile["id"]))
        conn.commit()
        conn.close()
        safe_log_activity(profile["id"], "plan_select", {"plan": "free"})
        return {"plan": "free", "selected": True, "coming_soon": False}

    safe_log_activity(profile["id"], "plan_select", {"plan": selected_plan, "coming_soon": True})
    return {
        "plan": selected_plan,
        "selected": False,
        "coming_soon": True,
        "request_invoice": True,
        "message": "Online checkout is being configured. Request invoice/contact sales.",
    }


@router.get("/v1/api-keys")
def list_api_keys(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    conn = get_conn()
    rows = conn.execute(
        "SELECT key_id, key_prefix, name, scopes_json, status, created_at, last_used_at, revoked_at FROM api_keys WHERE profile_id=? ORDER BY created_at DESC",
        (profile["id"],),
    ).fetchall()
    conn.close()

    return {
        "api_keys": [
            {
                "key_id": r["key_id"],
                "key_prefix": r["key_prefix"],
                "name": r["name"] or "Default key",
                "scopes": json.loads(r["scopes_json"] or "[]"),
                "status": r["status"] or "active",
                "created_at": r["created_at"],
                "last_used_at": r["last_used_at"],
                "revoked_at": r["revoked_at"],
            }
            for r in rows
            if r["key_id"]
        ]
    }


@router.post("/v1/api-keys")
def create_api_key(body: APIKeyCreateRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    conn = get_conn()

    active_count = conn.execute(
        "SELECT COUNT(*) AS c FROM api_keys WHERE profile_id=? AND COALESCE(status,'active')='active'",
        (profile["id"],),
    ).fetchone()["c"]

    if (profile["plan"] or "free") == "free" and active_count >= 1:
        conn.close()
        raise HTTPException(status_code=403, detail={"error": "free_plan_limit", "message": "Free plan allows first API key generation only"})

    raw_key = f"maisb_live_{secrets.token_urlsafe(32)}"
    key_hash = sha256(raw_key)
    key_id = f"key_{secrets.token_hex(8)}"
    key_prefix = raw_key[:14]
    now = utcnow()

    conn.execute(
        "INSERT INTO api_keys (key, plan, scan_count, email, created, key_id, profile_id, key_hash, key_prefix, name, scopes_json, status, created_at) VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)",
        (
            key_hash,
            profile["plan"] or "free",
            profile["email"],
            now,
            key_id,
            profile["id"],
            key_hash,
            key_prefix,
            (body.name or "Default key").strip() or "Default key",
            json.dumps(body.scopes, separators=(",", ":"), ensure_ascii=False),
            now,
        ),
    )

    conn.execute(
        "INSERT OR REPLACE INTO profile_api_keys (key_id, profile_id, email, key_hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (key_id, profile["id"], profile["email"], key_hash, now),
    )
    conn.commit()
    conn.close()

    safe_log_activity(profile["id"], "api_key_create", {"key_id": key_id, "name": body.name, "scopes": body.scopes})

    return {
        "key_id": key_id,
        "api_key": raw_key,
        "key_prefix": key_prefix,
        "name": (body.name or "Default key").strip() or "Default key",
        "scopes": body.scopes,
        "status": "active",
        "created_at": now,
        "warning": "Copy this API key now. It is shown only once.",
    }


@router.post("/v1/api-keys/{key_id}/rotate")
def rotate_api_key(key_id: str, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    conn = get_conn()
    row = conn.execute(
        "SELECT key_id FROM api_keys WHERE key_id=? AND profile_id=? AND COALESCE(status,'active')='active'",
        (key_id, profile["id"]),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "API key not found"})

    now = utcnow()
    conn.execute("UPDATE api_keys SET status='revoked', revoked_at=?, last_used_at=? WHERE key_id=?", (now, now, key_id))
    conn.execute("DELETE FROM profile_api_keys WHERE key_id=?", (key_id,))
    conn.commit()
    conn.close()

    created = create_api_key(APIKeyCreateRequest(name="Rotated key", scopes=["scan"]), authorization)
    safe_log_activity(profile["id"], "api_key_rotate", {"old_key_id": key_id, "new_key_id": created["key_id"]})
    return {"rotated": True, "old_key_id": key_id, "new": created}


@router.post("/v1/api-keys/{key_id}/revoke")
def revoke_api_key(key_id: str, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    now = utcnow()

    conn = get_conn()
    row = conn.execute(
        "SELECT key_id FROM api_keys WHERE key_id=? AND profile_id=? AND COALESCE(status,'active')='active'",
        (key_id, profile["id"]),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "API key not found"})

    conn.execute("UPDATE api_keys SET status='revoked', revoked_at=?, last_used_at=? WHERE key_id=?", (now, now, key_id))
    conn.execute("DELETE FROM profile_api_keys WHERE key_id=?", (key_id,))
    conn.commit()
    conn.close()

    safe_log_activity(profile["id"], "api_key_revoke", {"key_id": key_id})
    return {"revoked": True, "key_id": key_id, "revoked_at": now}


@router.get("/v1/api-keys/{key_id}/usage")
def api_key_usage(key_id: str, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    conn = get_conn()
    key = conn.execute(
        "SELECT key_id, key_hash, status, created_at, last_used_at FROM api_keys WHERE key_id=? AND profile_id=?",
        (key_id, profile["id"]),
    ).fetchone()
    if not key:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "API key not found"})

    counts = conn.execute(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN decision='BLOCKED' THEN 1 ELSE 0 END) AS blocked, MAX(created_at) AS last_scan FROM scan_events WHERE profile_id=? AND api_key_id=?",
        (profile["id"], key_id),
    ).fetchone()
    conn.close()

    return {
        "key_id": key_id,
        "status": key["status"] or "active",
        "created_at": key["created_at"],
        "last_used_at": key["last_used_at"],
        "usage": {
            "total_scans": int((counts["total"] or 0) if counts else 0),
            "blocked": int((counts["blocked"] or 0) if counts else 0),
            "last_scan_at": counts["last_scan"] if counts else None,
        },
    }


def _summary_from_events(events: List[sqlite3.Row]) -> Dict[str, Any]:
    total = len(events)
    blocked = sum(1 for r in events if (r["decision"] or "").upper() == "BLOCKED")
    review = sum(1 for r in events if (r["decision"] or "").upper() == "REVIEW")
    allowed = sum(1 for r in events if (r["decision"] or "").upper() == "ALLOWED")
    avg_risk = round(sum(float(r["risk_score"] or 0) for r in events) / total, 4) if total else 0.0
    return {
        "total_scans": total,
        "blocked": blocked,
        "review": review,
        "allowed": allowed,
        "avg_risk_score": avg_risk,
    }


@router.get("/v1/dashboard/analytics/scans-over-time")
def scans_over_time(range: str = Query("weekly", pattern="^(weekly|monthly)$"), authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    days = 7 if range == "weekly" else 30
    since = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat()
    events = collect_scan_events(profile["id"], since)

    buckets: Dict[str, int] = {}
    for row in events:
        day = (row["created_at"] or "")[:10]
        if day:
            buckets[day] = buckets.get(day, 0) + 1

    return {"range": range, "points": [{"date": d, "count": buckets[d]} for d in sorted(buckets.keys())]}


@router.get("/v1/dashboard/analytics/decision-breakdown")
def decision_breakdown(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    result: Dict[str, int] = {"ALLOWED": 0, "REVIEW": 0, "BLOCKED": 0}
    for row in events:
        key = (row["decision"] or "ALLOWED").upper()
        result[key] = result.get(key, 0) + 1
    return {"decisions": result}


@router.get("/v1/dashboard/analytics/risk-distribution")
def risk_distribution(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    bins = {"0.0-0.24": 0, "0.25-0.49": 0, "0.50-0.74": 0, "0.75-1.00": 0}
    for row in events:
        score = float(row["risk_score"] or 0)
        if score < 0.25:
            bins["0.0-0.24"] += 1
        elif score < 0.5:
            bins["0.25-0.49"] += 1
        elif score < 0.75:
            bins["0.50-0.74"] += 1
        else:
            bins["0.75-1.00"] += 1
    return {"distribution": bins}


@router.get("/v1/dashboard/analytics/top-risk-channels")
def top_risk_channels(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    agg: Dict[str, Dict[str, Any]] = {}
    for row in events:
        channel = row["channel"] or "unknown"
        item = agg.setdefault(channel, {"channel": channel, "count": 0, "risk_sum": 0.0})
        item["count"] += 1
        item["risk_sum"] += float(row["risk_score"] or 0)

    ranked = []
    for item in agg.values():
        count = max(1, int(item["count"]))
        ranked.append({"channel": item["channel"], "count": item["count"], "avg_risk": round(item["risk_sum"] / count, 4)})

    ranked.sort(key=lambda x: (-x["avg_risk"], -x["count"], x["channel"]))
    return {"channels": ranked[:5]}


@router.get("/v1/dashboard/security/risk-timeline")
def risk_timeline(range: str = Query("weekly", pattern="^(weekly|monthly)$"), authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    days = 7 if range == "weekly" else 30
    since = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat()
    events = collect_scan_events(profile["id"], since)

    timeline = []
    for row in events[-100:]:
        timeline.append({"created_at": row["created_at"], "risk_score": float(row["risk_score"] or 0), "decision": row["decision"]})
    return {"range": range, "timeline": timeline}


@router.get("/v1/dashboard/security/blocked-payloads")
def blocked_payloads(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = [r for r in collect_scan_events(profile["id"]) if (r["decision"] or "").upper() == "BLOCKED"]

    items = []
    for row in events[-100:]:
        items.append(
            {
                "event_id": row["id"],
                "trace_id": row["trace_id"],
                "channel": row["channel"],
                "objective": row["objective"],
                "risk_score": row["risk_score"],
                "taxonomy_class": row["taxonomy_class"],
                "boundary_status": row["boundary_status"],
                "created_at": row["created_at"],
                "payload_hash": None,
                "redacted_preview": None,
            }
        )
    return {"items": items}


@router.get("/v1/dashboard/security/channel-reputation")
def channel_reputation(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    by_channel: Dict[str, Dict[str, Any]] = {}
    for row in events:
        channel = row["channel"] or "unknown"
        item = by_channel.setdefault(channel, {"channel": channel, "events": 0, "blocked": 0, "trust_sum": 0.0})
        item["events"] += 1
        if (row["decision"] or "").upper() == "BLOCKED":
            item["blocked"] += 1
        item["trust_sum"] += 1.0 - float(row["risk_score"] or 0)

    result = []
    for item in by_channel.values():
        events_count = max(1, item["events"])
        result.append(
            {
                "channel": item["channel"],
                "events": item["events"],
                "blocked": item["blocked"],
                "trust_score": round(item["trust_sum"] / events_count, 4),
            }
        )
    result.sort(key=lambda x: (x["trust_score"], -x["events"], x["channel"]))
    return {"channels": result}


@router.get("/v1/dashboard/security/trust-degradation")
def trust_degradation(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    conn = get_conn()
    traces = conn.execute(
        "SELECT trace_id, channels_json, trust_score, degradation_score, final_decision, created_at, updated_at FROM cross_channel_traces WHERE profile_id=? ORDER BY updated_at DESC LIMIT 100",
        (profile["id"],),
    ).fetchall()
    conn.close()

    return {
        "traces": [
            {
                "trace_id": r["trace_id"],
                "channels": json.loads(r["channels_json"] or "[]"),
                "trust_score": r["trust_score"],
                "degradation_score": r["degradation_score"],
                "final_decision": r["final_decision"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in traces
        ]
    }


@router.get("/v1/dashboard/traces")
def list_traces(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    conn = get_conn()
    rows = conn.execute(
        "SELECT trace_id, channels_json, trust_score, degradation_score, final_decision, created_at, updated_at FROM cross_channel_traces WHERE profile_id=? ORDER BY updated_at DESC LIMIT 200",
        (profile["id"],),
    ).fetchall()
    conn.close()

    return {
        "traces": [
            {
                "trace_id": r["trace_id"],
                "channels": json.loads(r["channels_json"] or "[]"),
                "trust_degradation": r["degradation_score"],
                "final_decision": r["final_decision"],
                "why": decision_reason((r["final_decision"] or "ALLOWED").upper()),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    }


@router.get("/v1/dashboard/traces/{trace_id}")
def trace_detail(trace_id: str, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)

    conn = get_conn()
    row = conn.execute(
        "SELECT trace_id, channels_json, trust_score, degradation_score, final_decision, created_at, updated_at FROM cross_channel_traces WHERE trace_id=? AND profile_id=?",
        (trace_id, profile["id"]),
    ).fetchone()
    events = conn.execute(
        "SELECT id, decision, risk_score, taxonomy_class, channel, objective, boundary_status, created_at FROM scan_events WHERE trace_id=? AND profile_id=? ORDER BY created_at ASC",
        (trace_id, profile["id"]),
    ).fetchall()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Trace not found"})

    final_decision = (row["final_decision"] or "ALLOWED").upper()
    return {
        "trace_id": row["trace_id"],
        "channels": json.loads(row["channels_json"] or "[]"),
        "boundary_events": [
            {
                "event_id": e["id"],
                "decision": e["decision"],
                "risk_score": e["risk_score"],
                "taxonomy_class": e["taxonomy_class"],
                "channel": e["channel"],
                "objective": e["objective"],
                "boundary_status": e["boundary_status"],
                "created_at": e["created_at"],
            }
            for e in events
        ],
        "trust_score": row["trust_score"],
        "trust_degradation": row["degradation_score"],
        "final_decision": final_decision,
        "why": decision_reason(final_decision),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/v1/reports/export.csv")
def export_report_csv(authorization: Optional[str] = Header(None)):
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["id", "decision", "risk_score", "taxonomy_class", "channel", "objective", "trace_id", "boundary_status", "created_at"])
    writer.writeheader()
    for row in events:
        writer.writerow(
            {
                "id": row["id"],
                "decision": row["decision"],
                "risk_score": row["risk_score"],
                "taxonomy_class": row["taxonomy_class"],
                "channel": row["channel"],
                "objective": row["objective"],
                "trace_id": row["trace_id"],
                "boundary_status": row["boundary_status"],
                "created_at": row["created_at"],
            }
        )

    return PlainTextResponse(
        out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=maisb_report.csv"},
    )


@router.get("/v1/reports/export.json")
def export_report_json(authorization: Optional[str] = Header(None)):
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    return JSONResponse(
        {
            "profile_id": profile["id"],
            "generated_at": utcnow(),
            "events": [
                {
                    "id": row["id"],
                    "decision": row["decision"],
                    "risk_score": row["risk_score"],
                    "taxonomy_class": row["taxonomy_class"],
                    "channel": row["channel"],
                    "objective": row["objective"],
                    "trace_id": row["trace_id"],
                    "boundary_status": row["boundary_status"],
                    "created_at": row["created_at"],
                }
                for row in events
            ],
        }
    )


@router.post("/v1/reports/compliance")
def compliance_report(body: ComplianceRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    events = collect_scan_events(profile["id"])
    report_id = f"compliance_{secrets.token_hex(6)}"
    summary = _summary_from_events(events)
    safe_log_activity(profile["id"], "report_compliance", {"framework": body.framework, "report_id": report_id})
    return {
        "report_id": report_id,
        "framework": body.framework,
        "generated_at": utcnow(),
        "summary": summary,
        "status": "ready",
    }


@router.post("/v1/reports/schedule")
def schedule_report(body: ScheduleReportRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    schedule_id = f"sched_{secrets.token_hex(6)}"
    safe_log_activity(profile["id"], "report_schedule", {"cadence": body.cadence, "schedule_id": schedule_id})
    return {
        "schedule_id": schedule_id,
        "cadence": body.cadence,
        "status": "scheduled",
        "note": "MVP scheduler accepted. Delivery integrations can be expanded later.",
    }


@router.get("/v1/team")
def get_team(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=True)
    return {
        "team": [
            {
                "member_id": profile["id"],
                "email": profile["email"],
                "name": profile["name"],
                "role": "owner",
                "status": "active",
            }
        ],
        "plan": profile["plan"] or "free",
        "enterprise_actions": {"coming_soon": True},
    }


@router.post("/v1/team/invite")
def team_invite(body: TeamInviteRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    if not is_valid_email(body.email):
        raise HTTPException(status_code=422, detail={"error": "validation_error", "message": "Valid email is required"})

    invite_id = f"invite_{secrets.token_hex(6)}"
    safe_log_activity(profile["id"], "team_invite", {"invite_id": invite_id, "email": body.email, "role": body.role})
    return {
        "invited": True,
        "invite_id": invite_id,
        "email": body.email,
        "role": body.role,
        "status": "pending",
        "message": "MVP invite recorded for Free plan. Enterprise workflows remain coming soon.",
    }


@router.patch("/v1/team/{member_id}/role")
def team_role_patch(member_id: str, body: TeamRolePatchRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    profile, _ = resolve_profile_from_bearer(authorization, allow_api_key=False)
    safe_log_activity(profile["id"], "team_role_patch", {"member_id": member_id, "role": body.role})
    return {
        "member_id": member_id,
        "role": body.role,
        "coming_soon": True,
        "message": "Online team role management is being configured for enterprise workspaces.",
    }
