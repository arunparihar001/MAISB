# maisb/llm_proxy/api/scan_api.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Enterprise Phase 3 API — v2.3.0
#
# Railway Root Directory:
#   /maisb/llm_proxy
#
# Railway Start Command:
#   uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT
#
# This file is self-contained for Phase 1 staging.
# It does NOT depend on sibling folder maisb/core, because Railway root is
# currently maisb/llm_proxy.
# ─────────────────────────────────────────────────────────────────────────────

import datetime
import difflib
import hashlib
import json
import os
import secrets
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from api.phase3_dashboard import router as phase3_router
from pydantic import BaseModel, Field

# Make local llm_proxy imports work on Railway and locally.
CURRENT_FILE = Path(__file__).resolve()
LLM_PROXY_DIR = CURRENT_FILE.parents[1]

if str(LLM_PROXY_DIR) not in sys.path:
    sys.path.insert(0, str(LLM_PROXY_DIR))

from core.models import ScanRequest as PipelineScanRequest
from pipeline.runner import run_pipeline


DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")

FREE_TIER_MONTHLY_LIMIT = 1000
PRO_TIER_MONTHLY_LIMIT = 50_000

DEFAULT_TENANT_ID = "default"
DEFAULT_PRIVACY_MODE = "standard"
DEFAULT_RETENTION_DAYS = 90

PHASE2_VERSION = "2.3.0"

# Phase 2 adaptive channel trust scores.
# Low-trust channels add supply-chain risk when payloads move across surfaces.
CHANNEL_TRUST_SCORES: Dict[str, float] = {
    "internal_api": 0.93,
    "authenticated_user": 0.85,
    "api_response": 0.72,
    "file_upload": 0.40,
    "pdf_file": 0.35,
    "ocr_engine": 0.30,
    "browser_plugin": 0.22,
    "clipboard": 0.15,
    "webview": 0.12,
    "qr": 0.10,
    "qr_code": 0.10,
    "push_notification": 0.08,
    "notification": 0.08,
    "nfc_tag": 0.08,
    "deep_link": 0.05,
    "share_intent": 0.05,
    "agent": 0.45,
    "llm": 0.65,
    "unknown": 0.30,
}

TRANSFORM_RISK: Dict[str, float] = {
    "none": 0.00,
    "copy": 0.02,
    "minor_edit": 0.06,
    "format_conversion": 0.10,
    "ocr": 0.15,
    "context_inject": 0.25,
    "major_rewrite": 0.30,
    "unknown_transform": 0.18,
}


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def utcnow() -> str:
    return datetime.datetime.utcnow().isoformat()


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value or {}, separators=(",", ":"), ensure_ascii=False)


def json_loads(value: Optional[str], default: Any = None) -> Any:
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def require_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


def mask_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    if len(raw_key) <= 18:
        return raw_key[:6] + "****"
    return raw_key[:14] + "****"


def sanitize_payload_preview(payload: str, privacy_mode: str = DEFAULT_PRIVACY_MODE, limit: int = 100) -> str:
    text = payload or ""

    if privacy_mode == "strict":
        return "[redacted]"

    preview = text[:limit]

    if privacy_mode == "minimal":
        return f"[length={len(text)} chars]"

    # standard mode: keep preview but remove obvious newlines/tabs
    preview = preview.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return preview


# ─────────────────────────────────────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()

    # Legacy/free key table for backwards compatibility.
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

    # Enterprise tenant table.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_tenants (
            tenant_id               TEXT PRIMARY KEY,
            name                    TEXT NOT NULL,
            config_json             TEXT,
            metadata_retention_days INTEGER DEFAULT 90,
            max_api_keys            INTEGER DEFAULT 10,
            features_json           TEXT,
            is_active               INTEGER DEFAULT 1,
            created_at              TEXT,
            updated_at              TEXT
        )
    """)

    # Enterprise API key table.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_api_keys (
            key_id        TEXT PRIMARY KEY,
            tenant_id     TEXT NOT NULL,
            key_hash      TEXT NOT NULL UNIQUE,
            scopes_json   TEXT,
            role          TEXT DEFAULT 'viewer',
            monthly_limit INTEGER,
            usage_count   INTEGER DEFAULT 0,
            created_at    TEXT,
            expires_at    TEXT,
            revoked_at    TEXT,
            last_used     TEXT,
            is_active     INTEGER DEFAULT 1
        )
    """)

    # Enterprise policy table.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_policies (
            policy_id                   TEXT PRIMARY KEY,
            tenant_id                   TEXT NOT NULL,
            name                        TEXT NOT NULL,
            description                 TEXT,
            version                     INTEGER DEFAULT 1,
            rules_json                  TEXT,
            channel_rules_json          TEXT,
            objective_restrictions_json TEXT,
            is_active                   INTEGER DEFAULT 1,
            created_at                  TEXT,
            updated_at                  TEXT
        )
    """)

    # Audit logs.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_audit_logs (
            log_id        TEXT PRIMARY KEY,
            tenant_id     TEXT NOT NULL,
            timestamp     TEXT,
            event_type    TEXT,
            actor_id      TEXT,
            action        TEXT,
            resource      TEXT,
            details_json  TEXT,
            previous_hash TEXT,
            hash          TEXT
        )
    """)


    # Phase 2 cross-channel trace tables.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase2_channel_traces (
            trace_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            parent_trace_id TEXT,
            source_channel TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            current_hash TEXT NOT NULL,
            journey_json TEXT NOT NULL,
            trust_degradation_json TEXT NOT NULL,
            propagation_graph_json TEXT NOT NULL,
            final_risk_score REAL DEFAULT 0.0,
            detection_layer TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase2_trace_events (
            event_id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            transform TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            payload_preview TEXT,
            risk_score REAL DEFAULT 0.0,
            trust_score REAL DEFAULT 0.0,
            decision TEXT,
            metadata_json TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase2_channel_reputation (
            tenant_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            trust_score REAL DEFAULT 0.5,
            event_count INTEGER DEFAULT 0,
            blocked_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            last_seen TEXT,
            PRIMARY KEY (tenant_id, channel)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase2_explanations (
            explanation_id TEXT PRIMARY KEY,
            trace_id TEXT,
            tenant_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            reasoning_json TEXT NOT NULL,
            risk_factors_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Governance retention/privacy.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_retention (
            tenant_id      TEXT PRIMARY KEY,
            retention_days INTEGER DEFAULT 90,
            privacy_mode   TEXT DEFAULT 'standard',
            updated_at     TEXT
        )
    """)

    # Safe migrations for old local DBs.
    scan_cols = {r["name"] for r in conn.execute("PRAGMA table_info(scans)").fetchall()}
    for col, sql in {
        "channel": "ALTER TABLE scans ADD COLUMN channel TEXT",
        "objective": "ALTER TABLE scans ADD COLUMN objective TEXT",
        "taxonomy_class": "ALTER TABLE scans ADD COLUMN taxonomy_class TEXT",
        "processing_ms": "ALTER TABLE scans ADD COLUMN processing_ms INTEGER",
    }.items():
        if col not in scan_cols:
            conn.execute(sql)

    key_cols = {r["name"] for r in conn.execute("PRAGMA table_info(api_keys)").fetchall()}
    if "email" not in key_cols:
        conn.execute("ALTER TABLE api_keys ADD COLUMN email TEXT")

    # Legacy test key.
    conn.execute(
        "INSERT OR IGNORE INTO api_keys (key, plan, scan_count, created) VALUES (?, 'free', 0, ?)",
        ("maisb_live_test123", utcnow()),
    )

    conn.commit()
    conn.close()


def ensure_default_enterprise():
    conn = get_conn()

    tenant = conn.execute(
        "SELECT tenant_id FROM enterprise_tenants WHERE tenant_id = ?",
        (DEFAULT_TENANT_ID,),
    ).fetchone()

    if not tenant:
        conn.execute(
            """
            INSERT INTO enterprise_tenants
            (tenant_id, name, config_json, metadata_retention_days, max_api_keys, features_json, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                DEFAULT_TENANT_ID,
                "Default Tenant",
                json_dumps({"created_by": "phase1_bootstrap"}),
                DEFAULT_RETENTION_DAYS,
                10,
                json_dumps({
                    "multi_tenant": True,
                    "api_keys": True,
                    "scopes": True,
                    "usage_limits": True,
                    "policy_engine": True,
                    "audit_logging": True,
                    "retention": True,
                    "privacy_modes": True,
                    "rbac": True,
                }),
                utcnow(),
                utcnow(),
            ),
        )

    policy = conn.execute(
        "SELECT policy_id FROM enterprise_policies WHERE tenant_id = ? AND is_active = 1",
        (DEFAULT_TENANT_ID,),
    ).fetchone()

    if not policy:
        conn.execute(
            """
            INSERT INTO enterprise_policies
            (policy_id, tenant_id, name, description, version, rules_json, channel_rules_json,
             objective_restrictions_json, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                "policy_82b835c54088",
                DEFAULT_TENANT_ID,
                "Default Enterprise Policy",
                "Default policy created for Phase 1 enterprise staging.",
                1,
                json_dumps([]),
                json_dumps({
                    "clipboard": {"block_threshold": 0.80, "review_threshold": 0.50},
                    "webview": {"block_threshold": 0.75, "review_threshold": 0.45},
                    "qr": {"block_threshold": 0.70, "review_threshold": 0.40},
                    "deep_link": {"block_threshold": 0.70, "review_threshold": 0.40},
                    "notification": {"block_threshold": 0.75, "review_threshold": 0.45},
                    "file_upload": {"block_threshold": 0.80, "review_threshold": 0.50},
                    "api_response": {"block_threshold": 0.85, "review_threshold": 0.55},
                    "unknown": {"block_threshold": 0.80, "review_threshold": 0.50},
                }),
                json_dumps({}),
                utcnow(),
                utcnow(),
            ),
        )

    retention = conn.execute(
        "SELECT tenant_id FROM enterprise_retention WHERE tenant_id = ?",
        (DEFAULT_TENANT_ID,),
    ).fetchone()

    if not retention:
        conn.execute(
            """
            INSERT INTO enterprise_retention
            (tenant_id, retention_days, privacy_mode, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (DEFAULT_TENANT_ID, DEFAULT_RETENTION_DAYS, DEFAULT_PRIVACY_MODE, utcnow()),
        )

    conn.commit()
    conn.close()


init_db()
ensure_default_enterprise()


# ─────────────────────────────────────────────────────────────────────────────
# RBAC / scopes
# ─────────────────────────────────────────────────────────────────────────────

ALL_SCOPES = [
    "scan",
    "policy:read",
    "policy:write",
    "audit:read",
    "tenant:read",
    "tenant:write",
    "governance:read",
    "governance:write",
    "key:read",
    "key:write",
]

ROLE_PERMISSIONS = {
    "admin": [
        "scan",
        "policy:read",
        "policy:write",
        "audit:read",
        "tenant:read",
        "tenant:write",
        "governance:read",
        "governance:write",
        "key:read",
        "key:write",
    ],
    "analyst": [
        "scan",
        "policy:read",
        "audit:read",
        "governance:read",
    ],
    "viewer": [
        "policy:read",
        "governance:read",
    ],
    "auditor": [
        "audit:read",
        "policy:read",
        "governance:read",
    ],
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role or "viewer", [])


# ─────────────────────────────────────────────────────────────────────────────
# Audit logging
# ─────────────────────────────────────────────────────────────────────────────

def compute_audit_hash(
    log_id: str,
    tenant_id: str,
    timestamp: str,
    event_type: str,
    action: str,
    details_json: str,
    previous_hash: Optional[str],
) -> str:
    raw = "|".join([
        log_id,
        tenant_id,
        timestamp,
        event_type or "",
        action or "",
        details_json or "",
        previous_hash or "",
    ])
    return hash_value(raw)


def log_audit(
    tenant_id: str,
    event_type: str,
    action: str,
    actor_id: str = "system",
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    conn = get_conn()

    last_log = conn.execute(
        "SELECT hash FROM enterprise_audit_logs WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT 1",
        (tenant_id,),
    ).fetchone()

    previous_hash = last_log["hash"] if last_log else None
    log_id = f"log_{uuid4().hex[:8]}"
    timestamp = utcnow()
    details_json = json_dumps(details or {})

    log_hash = compute_audit_hash(
        log_id=log_id,
        tenant_id=tenant_id,
        timestamp=timestamp,
        event_type=event_type,
        action=action,
        details_json=details_json,
        previous_hash=previous_hash,
    )

    conn.execute(
        """
        INSERT INTO enterprise_audit_logs
        (log_id, tenant_id, timestamp, event_type, actor_id, action, resource, details_json, previous_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            tenant_id,
            timestamp,
            event_type,
            actor_id,
            action,
            resource,
            details_json,
            previous_hash,
            log_hash,
        ),
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Enterprise auth
# ─────────────────────────────────────────────────────────────────────────────

def generate_raw_api_key() -> str:
    return f"maisb_{secrets.token_urlsafe(32)}"


def create_enterprise_key(
    tenant_id: str,
    scopes: List[str],
    role: str,
    monthly_limit: Optional[int],
    expires_in_days: Optional[int],
) -> Dict[str, Any]:
    conn = get_conn()

    tenant = conn.execute(
        "SELECT tenant_id FROM enterprise_tenants WHERE tenant_id = ? AND is_active = 1",
        (tenant_id,),
    ).fetchone()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found or inactive")

    role = role or "viewer"
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    scopes = scopes or ["scan"]

    for scope in scopes:
        if scope not in ALL_SCOPES:
            raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}")

    raw_key = generate_raw_api_key()
    key_id = f"key_{secrets.token_hex(8)}"
    key_hash = hash_value(raw_key)

    expires_at = None
    if expires_in_days:
        expires_at = (
            datetime.datetime.utcnow() + datetime.timedelta(days=expires_in_days)
        ).isoformat()

    conn.execute(
        """
        INSERT INTO enterprise_api_keys
        (key_id, tenant_id, key_hash, scopes_json, role, monthly_limit, usage_count,
         created_at, expires_at, revoked_at, last_used, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, NULL, NULL, 1)
        """,
        (
            key_id,
            tenant_id,
            key_hash,
            json_dumps(scopes),
            role,
            monthly_limit,
            utcnow(),
            expires_at,
        ),
    )

    conn.commit()
    conn.close()

    log_audit(
        tenant_id=tenant_id,
        event_type="KEY_GENERATED",
        actor_id="admin",
        action="create",
        resource=key_id,
        details={
            "role": role,
            "scopes": scopes,
            "monthly_limit": monthly_limit,
            "expires_in_days": expires_in_days,
        },
    )

    return {
        "key_id": key_id,
        "raw_key": raw_key,
        "tenant_id": tenant_id,
        "scopes": scopes,
        "role": role,
        "monthly_limit": monthly_limit,
        "expires_in_days": expires_in_days,
        "warning": "Copy raw_key now. It will not be shown again.",
    }


def authenticate_enterprise_key(
    raw_key: str,
    tenant_id: Optional[str],
    required_scope: str = "scan",
    required_permission: str = "scan",
    consume_usage: bool = False,
) -> Optional[Dict[str, Any]]:
    if not raw_key:
        return None

    key_hash = hash_value(raw_key)
    conn = get_conn()

    row = conn.execute(
        "SELECT * FROM enterprise_api_keys WHERE key_hash = ?",
        (key_hash,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    if int(row["is_active"] or 0) != 1:
        conn.close()
        raise HTTPException(status_code=401, detail="API key inactive")

    if row["revoked_at"]:
        conn.close()
        raise HTTPException(status_code=401, detail="API key revoked")

    if tenant_id and row["tenant_id"] != tenant_id:
        conn.close()
        raise HTTPException(status_code=403, detail="API key does not belong to this tenant")

    if row["expires_at"]:
        try:
            expires = datetime.datetime.fromisoformat(row["expires_at"])
            if datetime.datetime.utcnow() > expires:
                conn.close()
                raise HTTPException(status_code=401, detail="API key expired")
        except HTTPException:
            raise
        except Exception:
            pass

    scopes = json_loads(row["scopes_json"], [])
    role = row["role"] or "viewer"

    if required_scope and required_scope not in scopes:
        conn.close()
        raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")

    if required_permission and not role_has_permission(role, required_permission):
        conn.close()
        raise HTTPException(status_code=403, detail=f"Role '{role}' lacks permission: {required_permission}")

    usage_count = int(row["usage_count"] or 0)
    monthly_limit = row["monthly_limit"]

    if monthly_limit is not None:
        monthly_limit = int(monthly_limit)
        if usage_count >= monthly_limit:
            conn.close()
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Enterprise key monthly limit of {monthly_limit:,} scans reached.",
                },
            )

    if consume_usage:
        usage_count += 1
        conn.execute(
            "UPDATE enterprise_api_keys SET usage_count = ?, last_used = ? WHERE key_id = ?",
            (usage_count, utcnow(), row["key_id"]),
        )
    else:
        conn.execute(
            "UPDATE enterprise_api_keys SET last_used = ? WHERE key_id = ?",
            (utcnow(), row["key_id"]),
        )

    conn.commit()
    conn.close()

    return {
        "key_id": row["key_id"],
        "tenant_id": row["tenant_id"],
        "scopes": scopes,
        "role": role,
        "monthly_limit": monthly_limit,
        "usage_count": usage_count,
        "enterprise": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Policy engine
# ─────────────────────────────────────────────────────────────────────────────

def get_active_policy(tenant_id: str) -> Dict[str, Any]:
    conn = get_conn()

    row = conn.execute(
        """
        SELECT * FROM enterprise_policies
        WHERE tenant_id = ? AND is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (tenant_id,),
    ).fetchone()

    conn.close()

    if not row:
        ensure_default_enterprise()
        return get_active_policy(DEFAULT_TENANT_ID)

    return {
        "policy_id": row["policy_id"],
        "name": row["name"],
        "version": row["version"],
        "rules": json_loads(row["rules_json"], []),
        "channel_rules": json_loads(row["channel_rules_json"], {}),
        "objective_restrictions": json_loads(row["objective_restrictions_json"], {}),
        "is_active": bool(row["is_active"]),
    }


def evaluate_policy(
    tenant_id: str,
    payload: str,
    channel: str,
    objective: str,
    risk_score: float,
) -> Dict[str, Any]:
    policy = get_active_policy(tenant_id)

    objective_restrictions = policy.get("objective_restrictions") or {}
    if objective and objective in objective_restrictions:
        restriction = objective_restrictions[objective] or {}
        if restriction.get("blocked"):
            return {
                "action": "BLOCK",
                "policy_id": policy["policy_id"],
                "reasoning": [f"Objective '{objective}' is blocked by policy"],
            }

    channel_rules = policy.get("channel_rules") or {}
    channel_config = channel_rules.get(channel) or channel_rules.get("unknown") or {}

    block_threshold = float(channel_config.get("block_threshold", 0.80))
    review_threshold = float(channel_config.get("review_threshold", 0.50))

    if risk_score >= block_threshold:
        return {
            "action": "BLOCK",
            "policy_id": policy["policy_id"],
            "reasoning": [
                f"Risk score {risk_score:.2f} exceeds block threshold {block_threshold:.2f}",
                f"Channel '{channel}' policy violation",
            ],
        }

    if risk_score >= review_threshold:
        return {
            "action": "REVIEW",
            "policy_id": policy["policy_id"],
            "reasoning": [
                f"Risk score {risk_score:.2f} exceeds review threshold {review_threshold:.2f}",
                f"Manual review recommended for channel '{channel}'",
            ],
        }

    rules = policy.get("rules") or []
    for rule in sorted(rules, key=lambda r: r.get("priority", 999)):
        condition = rule.get("condition", {})
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        matched = False

        if field == "risk_score":
            if operator == ">":
                matched = risk_score > value
            elif operator == ">=":
                matched = risk_score >= value
            elif operator == "<":
                matched = risk_score < value
            elif operator == "<=":
                matched = risk_score <= value
            elif operator == "==":
                matched = risk_score == value

        elif field == "channel":
            matched = channel == value

        elif field == "objective":
            matched = objective == value

        elif field == "payload_contains":
            matched = str(value).lower() in (payload or "").lower()

        if matched:
            return {
                "action": rule.get("action", "REVIEW"),
                "policy_id": policy["policy_id"],
                "rule_id": rule.get("rule_id"),
                "reasoning": [rule.get("description", "Custom rule matched")],
            }

    return {
        "action": "ALLOW",
        "policy_id": policy["policy_id"],
        "reasoning": ["Passed all policy checks"],
    }


def apply_final_decision(pipeline_decision: str, policy_action: str) -> str:
    normalized = (pipeline_decision or "REVIEW").upper()

    if normalized == "BLOCKED":
        return "BLOCKED"

    if policy_action == "BLOCK":
        return "BLOCKED"

    if normalized == "REVIEW":
        return "REVIEW"

    if policy_action == "REVIEW":
        return "REVIEW"

    return "ALLOWED"


def recommended_action_for(decision: str, original_recommendation: str) -> str:
    if decision == "BLOCKED":
        return "Block: injection detected or policy threshold exceeded. Do not pass this payload to the LLM."

    if decision == "REVIEW":
        return "Review: payload requires manual or higher-confidence validation before reaching the LLM."

    return original_recommendation or "Allow: payload appears clean and aligned with objective."


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MAISB Enterprise Phase 3 API",
    version="2.3.0",
    description=(
        "Mobile AI Security Benchmark — Enterprise Phase 1 API\n\n"
        "**Run a scan:** POST /v1/scan\n\n"
        "**Enterprise health:** GET /v1/enterprise/health\n\n"
        "**Generate enterprise API key:** POST /v1/auth/generate-key\n\n"
        "**View active policy:** GET /v1/policies/active\n\n"
        "**View audit logs:** GET /v1/audit/logs\n\n"
        "**View retention governance:** GET /v1/governance/retention\n\n**Phase 2 health:** GET /v1/phase2/health\n\n**Trace payload:** POST /v1/trace/payload\n\n**Phase 3 health:** GET /v1/phase3/health\n\n**Dashboard:** GET /dashboard"
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
        "*",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 3 dashboard + telemetry router
app.include_router(phase3_router)



# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class ScanRequestBody(BaseModel):
    payload: str
    channel: str = "unknown"
    objective: str = "general"
    api_key: str
    session_id: Optional[str] = None
    tenant_id: str = DEFAULT_TENANT_ID
    previous_trace_id: Optional[str] = None


class ScanResponseBody(BaseModel):
    decision: str
    risk_score: float
    taxonomy_class: str
    recommended_action: str
    processing_ms: int
    trace_id: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None


class KeyCreateRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    scopes: List[str] = Field(default_factory=lambda: ["scan"])
    role: str = "viewer"
    monthly_limit: Optional[int] = None
    expires_in_days: Optional[int] = None


class TenantCreateRequest(BaseModel):
    tenant_id: Optional[str] = None
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class PolicyCreateRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    name: str = "Custom Policy"
    description: Optional[str] = None
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    channel_rules: Dict[str, Any] = Field(default_factory=dict)
    objective_restrictions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class RetentionUpdateRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    retention_days: int = DEFAULT_RETENTION_DAYS
    privacy_mode: str = DEFAULT_PRIVACY_MODE



class TracePayloadRequest(BaseModel):
    payload: str
    channel: str = "unknown"
    tenant_id: str = DEFAULT_TENANT_ID
    previous_trace_id: Optional[str] = None
    objective: str = "general"
    session_id: Optional[str] = None
    risk_score: Optional[float] = None
    decision: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class TraceEventRequest(BaseModel):
    payload: str
    channel: str
    transform: Optional[str] = None
    risk_score: Optional[float] = None
    decision: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class TrustScoreRequest(BaseModel):
    channel: str
    tenant_id: str = DEFAULT_TENANT_ID
    context: Dict[str, Any] = Field(default_factory=dict)


class ExplainDecisionRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    decision: str
    risk_score: float
    channel: str = "unknown"
    objective: str = "general"
    trace_id: Optional[str] = None
    taxonomy_class: Optional[str] = None
    policy_action: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Cross-Channel Trace Engine
# ─────────────────────────────────────────────────────────────────────────────

def phase2_payload_hash(payload: str) -> str:
    return hashlib.sha256((payload or "").encode("utf-8")).hexdigest()


def phase2_payload_preview(payload: str, max_len: int = 160) -> str:
    return " ".join((payload or "").split())[:max_len]


def phase2_generate_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def phase2_reputation_adjustment(tenant_id: str, channel: str) -> float:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT event_count, blocked_count, review_count
        FROM phase2_channel_reputation
        WHERE tenant_id = ? AND channel = ?
        """,
        (tenant_id, channel),
    ).fetchone()
    conn.close()

    if not row or int(row["event_count"] or 0) == 0:
        return 0.0

    event_count = max(1, int(row["event_count"]))
    bad_ratio = (int(row["blocked_count"] or 0) + 0.5 * int(row["review_count"] or 0)) / event_count
    return max(-0.25, -bad_ratio * 0.25)


def calculate_dynamic_trust(channel: str, context: Optional[Dict[str, Any]] = None, tenant_id: str = DEFAULT_TENANT_ID) -> Dict[str, Any]:
    context = context or {}
    normalized_channel = (channel or "unknown").strip().lower()
    base = CHANNEL_TRUST_SCORES.get(normalized_channel, CHANNEL_TRUST_SCORES["unknown"])
    adjustments: List[Dict[str, Any]] = []

    if context.get("user_authenticated") is True:
        adjustments.append({"factor": "user_authenticated", "delta": 0.15})
    elif context.get("user_authenticated") is False:
        adjustments.append({"factor": "anonymous_or_unverified_user", "delta": -0.15})

    session_age = context.get("session_age_minutes")
    if isinstance(session_age, (int, float)) and session_age > 60:
        adjustments.append({"factor": "stale_session", "delta": -0.10})

    if context.get("geo_consistent") is False:
        adjustments.append({"factor": "geographic_inconsistency", "delta": -0.20})

    if context.get("device_trusted") is True:
        adjustments.append({"factor": "trusted_device", "delta": 0.10})
    elif context.get("device_trusted") is False:
        adjustments.append({"factor": "untrusted_device", "delta": -0.10})

    reputation_delta = phase2_reputation_adjustment(tenant_id, normalized_channel)
    if reputation_delta:
        adjustments.append({"factor": "channel_reputation", "delta": reputation_delta})

    trust_score = max(0.0, min(1.0, base + sum(float(a["delta"]) for a in adjustments)))

    if trust_score >= 0.75:
        trust_level = "high"
    elif trust_score >= 0.45:
        trust_level = "medium"
    elif trust_score >= 0.20:
        trust_level = "low"
    else:
        trust_level = "critical_low"

    return {
        "channel": normalized_channel,
        "base_trust": round(base, 3),
        "adjustments": adjustments,
        "trust_score": round(trust_score, 3),
        "trust_level": trust_level,
    }


def update_phase2_channel_reputation(tenant_id: str, channel: str, trust_score: float, decision: Optional[str]) -> None:
    normalized_decision = (decision or "").upper()
    blocked_inc = 1 if normalized_decision == "BLOCKED" else 0
    review_inc = 1 if normalized_decision == "REVIEW" else 0

    conn = get_conn()
    existing = conn.execute(
        """
        SELECT event_count, blocked_count, review_count, trust_score
        FROM phase2_channel_reputation
        WHERE tenant_id = ? AND channel = ?
        """,
        (tenant_id, channel),
    ).fetchone()

    if existing:
        old_count = int(existing["event_count"] or 0)
        new_count = old_count + 1
        old_score = float(existing["trust_score"] or 0.5)
        new_score = ((old_score * old_count) + trust_score) / new_count

        conn.execute(
            """
            UPDATE phase2_channel_reputation
            SET trust_score = ?, event_count = ?, blocked_count = blocked_count + ?,
                review_count = review_count + ?, last_seen = ?
            WHERE tenant_id = ? AND channel = ?
            """,
            (new_score, new_count, blocked_inc, review_inc, utcnow(), tenant_id, channel),
        )
    else:
        conn.execute(
            """
            INSERT INTO phase2_channel_reputation
            (tenant_id, channel, trust_score, event_count, blocked_count, review_count, last_seen)
            VALUES (?, ?, ?, 1, ?, ?, ?)
            """,
            (tenant_id, channel, trust_score, blocked_inc, review_inc, utcnow()),
        )

    conn.commit()
    conn.close()


def load_phase2_trace(trace_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    if tenant_id:
        row = conn.execute(
            "SELECT * FROM phase2_channel_traces WHERE trace_id = ? AND tenant_id = ?",
            (trace_id, tenant_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM phase2_channel_traces WHERE trace_id = ?",
            (trace_id,),
        ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "trace_id": row["trace_id"],
        "tenant_id": row["tenant_id"],
        "parent_trace_id": row["parent_trace_id"],
        "source_channel": row["source_channel"],
        "source_hash": row["source_hash"],
        "current_hash": row["current_hash"],
        "journey": json_loads(row["journey_json"], []),
        "trust_degradation": json_loads(row["trust_degradation_json"], []),
        "propagation_graph": json_loads(row["propagation_graph_json"], {"nodes": [], "edges": []}),
        "final_risk_score": row["final_risk_score"],
        "detection_layer": row["detection_layer"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def detect_phase2_transform(previous_hash: Optional[str], previous_payload_preview: Optional[str], payload: str, channel: str) -> str:
    if not previous_hash:
        return "none"

    current_hash = phase2_payload_hash(payload)
    if previous_hash == current_hash:
        return "copy"

    ch = (channel or "").lower()
    if "ocr" in ch:
        return "ocr"
    if ch in {"agent", "llm", "api_response"}:
        return "context_inject"

    previous_preview = previous_payload_preview or ""
    current_preview = phase2_payload_preview(payload)
    if previous_preview and current_preview:
        similarity = difflib.SequenceMatcher(None, previous_preview.lower(), current_preview.lower()).ratio()
        if similarity >= 0.85:
            return "minor_edit"
        if similarity <= 0.35:
            return "major_rewrite"

    if ch in {"pdf_file", "file_upload", "webview"}:
        return "format_conversion"

    return "unknown_transform"


def calculate_trust_degradation(journey: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    degradation: List[Dict[str, Any]] = []
    cumulative_loss = 0.0

    for index, step in enumerate(journey):
        channel = step.get("channel", "unknown")
        transform = step.get("transform", "unknown_transform")
        trust_score = float(step.get("trust_score", CHANNEL_TRUST_SCORES.get(channel, 0.3)))
        transform_risk = TRANSFORM_RISK.get(transform, TRANSFORM_RISK["unknown_transform"])
        channel_loss = max(0.0, 1.0 - trust_score)
        step_loss = min(1.0, (channel_loss * 0.35) + transform_risk)
        cumulative_loss = min(1.0, cumulative_loss + step_loss)

        degradation.append({
            "index": index,
            "channel": channel,
            "transform": transform,
            "trust_score": round(trust_score, 3),
            "step_loss": round(step_loss, 3),
            "cumulative_loss": round(cumulative_loss, 3),
        })

    return degradation


def build_propagation_graph(journey: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for index, step in enumerate(journey):
        node_id = f"n{index}"
        nodes.append({
            "id": node_id,
            "channel": step.get("channel"),
            "hash": step.get("hash"),
            "timestamp": step.get("timestamp"),
            "trust_score": step.get("trust_score"),
            "decision": step.get("decision"),
        })

        if index > 0:
            edges.append({
                "from": f"n{index - 1}",
                "to": node_id,
                "transform": step.get("transform"),
            })

    return {"nodes": nodes, "edges": edges}


def combine_phase2_risk(payload_risk: Optional[float], trust_degradation: List[Dict[str, Any]]) -> float:
    payload_component = float(payload_risk or 0.0)
    trust_component = trust_degradation[-1]["cumulative_loss"] if trust_degradation else 0.0
    return round(min(1.0, (payload_component * 0.70) + (trust_component * 0.30)), 3)


def classify_phase2_risk(risk_score: float) -> str:
    if risk_score >= 0.80:
        return "critical"
    if risk_score >= 0.50:
        return "high"
    if risk_score >= 0.25:
        return "medium"
    return "low"


def infer_phase2_triggered_layers(channel: str, taxonomy_class: Optional[str], trust_degradation: List[Dict[str, Any]]) -> List[str]:
    layers = ["pipeline"]
    if taxonomy_class and taxonomy_class != "T0":
        layers.append("taxonomy")
    if channel:
        layers.append(f"channel:{channel}")
    if trust_degradation and trust_degradation[-1]["cumulative_loss"] >= 0.50:
        layers.append("cross_channel_trace")
    return layers


def infer_phase2_matched_signatures(taxonomy_class: Optional[str], risk_score: float) -> List[str]:
    signatures: List[str] = []
    if taxonomy_class:
        signatures.append(taxonomy_class)
    if risk_score >= 0.80:
        signatures.append("high_risk_prompt_or_policy_threshold")
    return signatures


def generate_phase2_explanation(
    tenant_id: str,
    decision: str,
    risk_score: float,
    channel: str,
    objective: str,
    trace_id: Optional[str] = None,
    taxonomy_class: Optional[str] = None,
    policy_action: Optional[str] = None,
    trust_degradation: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    trust_degradation = trust_degradation or []
    normalized_decision = (decision or "REVIEW").upper()
    risk_level = classify_phase2_risk(float(risk_score or 0.0))

    reasoning: List[str] = []
    risk_factors: Dict[str, Any] = {
        "pipeline_risk": round(float(risk_score or 0.0), 3),
        "risk_level": risk_level,
        "channel": channel,
        "objective": objective,
    }

    if taxonomy_class:
        risk_factors["taxonomy_class"] = taxonomy_class

    if trust_degradation:
        risk_factors["trust_degradation"] = trust_degradation[-1]["cumulative_loss"]
        if trust_degradation[-1]["cumulative_loss"] >= 0.50:
            reasoning.append("Cross-channel trust degradation is high.")

    if risk_score >= 0.80:
        reasoning.append("Pipeline risk exceeded the block threshold.")
    elif risk_score >= 0.50:
        reasoning.append("Pipeline risk exceeded the review threshold.")
    else:
        reasoning.append("Pipeline risk is below review threshold.")

    if normalized_decision == "BLOCKED":
        reasoning.append("Final decision is BLOCKED because model, policy, or trace risk is not acceptable.")
        confidence = min(0.99, max(0.80, float(risk_score or 0.0)))
    elif normalized_decision == "REVIEW":
        reasoning.append("Final decision is REVIEW because moderate risk requires human or policy review.")
        confidence = 0.70
    else:
        reasoning.append("Final decision is ALLOWED because risk and trust checks passed.")
        confidence = max(0.50, 1.0 - float(risk_score or 0.0))

    if policy_action:
        reasoning.append(f"Policy engine action was {policy_action}.")

    explanation_id = phase2_generate_id("explain")

    result = {
        "explanation_id": explanation_id,
        "trace_id": trace_id,
        "tenant_id": tenant_id,
        "decision": normalized_decision,
        "confidence": round(float(confidence), 3),
        "reasoning": reasoning,
        "risk_factors": risk_factors,
        "triggered_layers": infer_phase2_triggered_layers(channel, taxonomy_class, trust_degradation),
        "matched_signatures": infer_phase2_matched_signatures(taxonomy_class, float(risk_score or 0.0)),
        "semantic_analysis": {
            "objective": objective,
            "channel_context": channel,
            "risk_language": risk_level,
        },
        "trust_degradation": trust_degradation,
    }

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO phase2_explanations
        (explanation_id, trace_id, tenant_id, decision, confidence,
         reasoning_json, risk_factors_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            explanation_id,
            trace_id,
            tenant_id,
            normalized_decision,
            result["confidence"],
            json_dumps(reasoning),
            json_dumps(risk_factors),
            utcnow(),
        ),
    )
    conn.commit()
    conn.close()

    return result


def create_or_extend_phase2_trace(
    tenant_id: str,
    payload: str,
    channel: str,
    objective: str = "general",
    previous_trace_id: Optional[str] = None,
    risk_score: Optional[float] = None,
    decision: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = metadata or {}
    context = context or {}
    now = utcnow()
    payload_hash = phase2_payload_hash(payload)
    normalized_channel = (channel or "unknown").strip().lower()

    previous_trace = load_phase2_trace(previous_trace_id, tenant_id) if previous_trace_id else None
    previous_journey = previous_trace["journey"] if previous_trace else []
    previous_hash = previous_trace["current_hash"] if previous_trace else None
    previous_preview = previous_journey[-1].get("payload_preview") if previous_journey else None

    trust_result = calculate_dynamic_trust(normalized_channel, context, tenant_id)
    transform = detect_phase2_transform(previous_hash, previous_preview, payload, normalized_channel)

    step = {
        "channel": normalized_channel,
        "timestamp": now,
        "hash": payload_hash,
        "payload_preview": phase2_payload_preview(payload),
        "transform": transform,
        "objective": objective,
        "risk_score": risk_score if risk_score is not None else 0.0,
        "decision": decision,
        "trust_score": trust_result["trust_score"],
        "trust_level": trust_result["trust_level"],
        "metadata": metadata,
    }

    journey = previous_journey + [step]
    trust_degradation = calculate_trust_degradation(journey)
    propagation_graph = build_propagation_graph(journey)
    final_risk = combine_phase2_risk(risk_score, trust_degradation)

    if decision == "BLOCKED":
        detection_layer = normalized_channel
    elif previous_trace and previous_trace.get("detection_layer"):
        detection_layer = previous_trace["detection_layer"]
    else:
        detection_layer = None

    trace_id = phase2_generate_id("trace")

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO phase2_channel_traces
        (trace_id, tenant_id, parent_trace_id, source_channel, source_hash, current_hash,
         journey_json, trust_degradation_json, propagation_graph_json, final_risk_score,
         detection_layer, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """,
        (
            trace_id,
            tenant_id,
            previous_trace_id,
            journey[0]["channel"],
            journey[0]["hash"],
            payload_hash,
            json_dumps(journey),
            json_dumps(trust_degradation),
            json_dumps(propagation_graph),
            final_risk,
            detection_layer,
            now,
            now,
        ),
    )

    event_id = phase2_generate_id("event")
    conn.execute(
        """
        INSERT INTO phase2_trace_events
        (event_id, trace_id, tenant_id, channel, transform, payload_hash,
         payload_preview, risk_score, trust_score, decision, metadata_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            trace_id,
            tenant_id,
            normalized_channel,
            transform,
            payload_hash,
            phase2_payload_preview(payload),
            float(risk_score or 0.0),
            float(trust_result["trust_score"]),
            decision,
            json_dumps(metadata),
            now,
        ),
    )
    conn.commit()
    conn.close()

    update_phase2_channel_reputation(tenant_id, normalized_channel, float(trust_result["trust_score"]), decision)

    explanation = generate_phase2_explanation(
        tenant_id=tenant_id,
        decision=decision or "TRACE_RECORDED",
        risk_score=float(risk_score or final_risk),
        channel=normalized_channel,
        objective=objective,
        trace_id=trace_id,
        taxonomy_class=metadata.get("taxonomy_class"),
        policy_action=metadata.get("policy_action"),
        trust_degradation=trust_degradation,
    )

    return {
        "trace_id": trace_id,
        "event_id": event_id,
        "tenant_id": tenant_id,
        "source_channel": journey[0]["channel"],
        "current_channel": normalized_channel,
        "payload_hash": payload_hash,
        "journey": journey,
        "trust_degradation": trust_degradation,
        "propagation_graph": propagation_graph,
        "final_risk_score": final_risk,
        "detection_layer": detection_layer,
        "explanation": explanation,
    }


def record_scan_phase2_trace_safe(
    tenant_id: str,
    payload: str,
    channel: str,
    objective: str,
    decision: str,
    risk_score: float,
    taxonomy_class: Optional[str] = None,
    previous_trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    policy_action: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    try:
        return create_or_extend_phase2_trace(
            tenant_id=tenant_id,
            payload=payload,
            channel=channel,
            objective=objective,
            previous_trace_id=previous_trace_id,
            risk_score=risk_score,
            decision=decision,
            metadata={
                "taxonomy_class": taxonomy_class,
                "session_id": session_id,
                "policy_action": policy_action,
                "recorded_from": "v1_scan",
            },
            context={},
        )
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/phase2/health", tags=["Phase 2"])
def phase2_health():
    conn = get_conn()
    traces = conn.execute("SELECT COUNT(*) AS c FROM phase2_channel_traces").fetchone()["c"]
    events = conn.execute("SELECT COUNT(*) AS c FROM phase2_trace_events").fetchone()["c"]
    explanations = conn.execute("SELECT COUNT(*) AS c FROM phase2_explanations").fetchone()["c"]
    conn.close()

    return {
        "status": "ok",
        "phase2": True,
        "phase2_complete": True,
        "version": PHASE2_VERSION,
        "features": {
            "cross_channel_trace": True,
            "dynamic_trust_scoring": True,
            "propagation_graph": True,
            "decision_explanations": True,
            "channel_reputation": True,
        },
        "counts": {
            "traces": traces,
            "events": events,
            "explanations": explanations,
        },
    }


@app.post("/v1/trace/payload", tags=["Phase 2"])
def trace_payload(body: TracePayloadRequest):
    return create_or_extend_phase2_trace(
        tenant_id=body.tenant_id,
        payload=body.payload,
        channel=body.channel,
        objective=body.objective,
        previous_trace_id=body.previous_trace_id,
        risk_score=body.risk_score,
        decision=body.decision,
        metadata=body.metadata,
        context=body.context,
    )


@app.get("/v1/trace/{trace_id}", tags=["Phase 2"])
def get_trace(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)):
    trace = load_phase2_trace(trace_id, tenant_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.post("/v1/trace/{trace_id}/event", tags=["Phase 2"])
def add_trace_event(trace_id: str, body: TraceEventRequest, tenant_id: str = Query(DEFAULT_TENANT_ID)):
    existing = load_phase2_trace(trace_id, tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trace not found")

    return create_or_extend_phase2_trace(
        tenant_id=tenant_id,
        payload=body.payload,
        channel=body.channel,
        objective=body.metadata.get("objective", "general"),
        previous_trace_id=trace_id,
        risk_score=body.risk_score,
        decision=body.decision,
        metadata=body.metadata,
        context=body.context,
    )


@app.get("/v1/trace/{trace_id}/supply-chain", tags=["Phase 2"])
def get_supply_chain(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)):
    trace = load_phase2_trace(trace_id, tenant_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return {
        "trace_id": trace_id,
        "tenant_id": tenant_id,
        "journey": trace["journey"],
        "trust_degradation": trace["trust_degradation"],
        "propagation_graph": trace["propagation_graph"],
        "final_risk_score": trace["final_risk_score"],
        "detection_layer": trace["detection_layer"],
    }


@app.post("/v1/trust/score", tags=["Phase 2"])
def trust_score(body: TrustScoreRequest):
    return calculate_dynamic_trust(body.channel, body.context, body.tenant_id)


@app.get("/v1/trust/channels", tags=["Phase 2"])
def channel_trust(admin_key: str = Query(...), tenant_id: str = Query(DEFAULT_TENANT_ID)):
    require_admin(admin_key)

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT channel, trust_score, event_count, blocked_count, review_count, last_seen
        FROM phase2_channel_reputation
        WHERE tenant_id = ?
        ORDER BY event_count DESC, channel ASC
        """,
        (tenant_id,),
    ).fetchall()
    conn.close()

    return {
        "tenant_id": tenant_id,
        "base_scores": CHANNEL_TRUST_SCORES,
        "reputation": [dict(row) for row in rows],
    }


@app.post("/v1/explain/decision", tags=["Phase 2"])
def explain_decision(body: ExplainDecisionRequest):
    trace = load_phase2_trace(body.trace_id, body.tenant_id) if body.trace_id else None
    trust_degradation = trace["trust_degradation"] if trace else []

    return generate_phase2_explanation(
        tenant_id=body.tenant_id,
        decision=body.decision,
        risk_score=body.risk_score,
        channel=body.channel,
        objective=body.objective,
        trace_id=body.trace_id,
        taxonomy_class=body.taxonomy_class,
        policy_action=body.policy_action,
        trust_degradation=trust_degradation,
    )


@app.get("/v1/explain/{trace_id}", tags=["Phase 2"])
def explain_trace(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)):
    trace = load_phase2_trace(trace_id, tenant_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    last_step = trace["journey"][-1] if trace["journey"] else {}

    return generate_phase2_explanation(
        tenant_id=tenant_id,
        decision=last_step.get("decision") or "TRACE_RECORDED",
        risk_score=float(last_step.get("risk_score") or trace["final_risk_score"] or 0.0),
        channel=last_step.get("channel", "unknown"),
        objective=last_step.get("objective", "general"),
        trace_id=trace_id,
        taxonomy_class=last_step.get("metadata", {}).get("taxonomy_class"),
        trust_degradation=trace["trust_degradation"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# System endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "2.3.0", "phase2": True, "phase3": True}


@app.get("/", tags=["System"])
def root():
    return {
        "name": "MAISB Enterprise Phase 2 API",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "GET /health",
        "scan": "POST /v1/scan",
        "enterprise_health": "GET /v1/enterprise/health",
        "enterprise_keys": "POST /v1/auth/generate-key",
        "active_policy": "GET /v1/policies/active",
        "audit_logs": "GET /v1/audit/logs",
        "governance_retention": "GET /v1/governance/retention",
        "phase2_health": "GET /v1/phase2/health",
        "trace_payload": "POST /v1/trace/payload",
        "trace_supply_chain": "GET /v1/trace/{trace_id}/supply-chain",
        "trust_score": "POST /v1/trust/score",
        "explain_trace": "GET /v1/explain/{trace_id}",
        "phase3_health": "GET /v1/phase3/health",
        "dashboard": "GET /dashboard",
        "dashboard_summary": "GET /v1/dashboard/summary",
    }


@app.get("/v1/enterprise/health", tags=["Enterprise"])
def enterprise_health():
    conn = get_conn()

    tenants = conn.execute("SELECT COUNT(*) AS c FROM enterprise_tenants").fetchone()["c"]
    policies = conn.execute("SELECT COUNT(*) AS c FROM enterprise_policies").fetchone()["c"]
    audit_logs = conn.execute("SELECT COUNT(*) AS c FROM enterprise_audit_logs").fetchone()["c"]

    conn.close()

    return {
        "status": "ok",
        "enterprise": True,
        "phase1_complete": True,
        "tenants": tenants,
        "policies": policies,
        "audit_logs": audit_logs,
        "features": {
            "multi_tenant": True,
            "api_keys": True,
            "scopes": True,
            "usage_limits": True,
            "policy_engine": True,
            "audit_logging": True,
            "retention": True,
            "privacy_modes": True,
            "rbac": True,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tenant endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/enterprise/tenants", tags=["Enterprise"])
def create_tenant(body: TenantCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)

    tenant_id = body.tenant_id or f"tenant_{uuid4().hex[:10]}"

    conn = get_conn()

    existing = conn.execute(
        "SELECT tenant_id FROM enterprise_tenants WHERE tenant_id = ?",
        (tenant_id,),
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Tenant already exists")

    conn.execute(
        """
        INSERT INTO enterprise_tenants
        (tenant_id, name, config_json, metadata_retention_days, max_api_keys, features_json, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (
            tenant_id,
            body.name,
            json_dumps(body.config),
            DEFAULT_RETENTION_DAYS,
            10,
            json_dumps({
                "multi_tenant": True,
                "api_keys": True,
                "scopes": True,
                "usage_limits": True,
                "policy_engine": True,
                "audit_logging": True,
                "retention": True,
                "privacy_modes": True,
                "rbac": True,
            }),
            utcnow(),
            utcnow(),
        ),
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO enterprise_retention
        (tenant_id, retention_days, privacy_mode, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (tenant_id, DEFAULT_RETENTION_DAYS, DEFAULT_PRIVACY_MODE, utcnow()),
    )

    conn.commit()
    conn.close()

    log_audit(
        tenant_id=tenant_id,
        event_type="TENANT_CREATED",
        actor_id="admin",
        action="create",
        resource=tenant_id,
        details={"name": body.name},
    )

    return {"tenant_id": tenant_id, "name": body.name, "created": True}


@app.get("/v1/enterprise/tenants", tags=["Enterprise"])
def list_tenants(admin_key: str = Query(...)):
    require_admin(admin_key)

    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM enterprise_tenants ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return {
        "tenants": [
            {
                "tenant_id": r["tenant_id"],
                "name": r["name"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"],
                "metadata_retention_days": r["metadata_retention_days"],
                "max_api_keys": r["max_api_keys"],
            }
            for r in rows
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Auth endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/auth/scopes", tags=["Auth"])
def get_scopes(admin_key: str = Query(...)):
    require_admin(admin_key)
    return {
        "scopes": ALL_SCOPES,
        "roles": ROLE_PERMISSIONS,
    }


@app.post("/v1/auth/generate-key", tags=["Auth"])
def generate_key(body: KeyCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)

    return create_enterprise_key(
        tenant_id=body.tenant_id,
        scopes=body.scopes,
        role=body.role,
        monthly_limit=body.monthly_limit,
        expires_in_days=body.expires_in_days,
    )


@app.get("/v1/auth/keys", tags=["Auth"])
def list_enterprise_keys(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    admin_key: str = Query(...),
):
    require_admin(admin_key)

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT key_id, tenant_id, scopes_json, role, monthly_limit, usage_count,
               created_at, expires_at, revoked_at, last_used, is_active
        FROM enterprise_api_keys
        WHERE tenant_id = ?
        ORDER BY created_at DESC
        """,
        (tenant_id,),
    ).fetchall()
    conn.close()

    return {
        "tenant_id": tenant_id,
        "keys": [
            {
                "key_id": r["key_id"],
                "tenant_id": r["tenant_id"],
                "scopes": json_loads(r["scopes_json"], []),
                "role": r["role"],
                "monthly_limit": r["monthly_limit"],
                "usage_count": r["usage_count"],
                "created_at": r["created_at"],
                "expires_at": r["expires_at"],
                "revoked_at": r["revoked_at"],
                "last_used": r["last_used"],
                "is_active": bool(r["is_active"]),
            }
            for r in rows
        ],
    }


@app.post("/v1/auth/revoke-key/{key_id}", tags=["Auth"])
def revoke_key(
    key_id: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    admin_key: str = Query(...),
):
    require_admin(admin_key)

    conn = get_conn()
    row = conn.execute(
        "SELECT key_id FROM enterprise_api_keys WHERE key_id = ? AND tenant_id = ?",
        (key_id, tenant_id),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Key not found")

    conn.execute(
        "UPDATE enterprise_api_keys SET revoked_at = ?, is_active = 0 WHERE key_id = ?",
        (utcnow(), key_id),
    )
    conn.commit()
    conn.close()

    log_audit(
        tenant_id=tenant_id,
        event_type="KEY_REVOKED",
        actor_id="admin",
        action="revoke",
        resource=key_id,
        details={},
    )

    return {"success": True, "key_id": key_id, "tenant_id": tenant_id}


@app.post("/v1/auth/rotate-key/{key_id}", tags=["Auth"])
def rotate_key(
    key_id: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    admin_key: str = Query(...),
):
    require_admin(admin_key)

    conn = get_conn()
    old = conn.execute(
        "SELECT * FROM enterprise_api_keys WHERE key_id = ? AND tenant_id = ?",
        (key_id, tenant_id),
    ).fetchone()

    if not old:
        conn.close()
        raise HTTPException(status_code=404, detail="Key not found")

    scopes = json_loads(old["scopes_json"], ["scan"])
    role = old["role"] or "viewer"
    monthly_limit = old["monthly_limit"]

    conn.execute(
        "UPDATE enterprise_api_keys SET revoked_at = ?, is_active = 0 WHERE key_id = ?",
        (utcnow(), key_id),
    )
    conn.commit()
    conn.close()

    new_key = create_enterprise_key(
        tenant_id=tenant_id,
        scopes=scopes,
        role=role,
        monthly_limit=monthly_limit,
        expires_in_days=None,
    )

    log_audit(
        tenant_id=tenant_id,
        event_type="KEY_ROTATED",
        actor_id="admin",
        action="rotate",
        resource=key_id,
        details={"new_key_id": new_key["key_id"]},
    )

    return {
        "old_key_id": key_id,
        "new_key_id": new_key["key_id"],
        "raw_key": new_key["raw_key"],
        "tenant_id": tenant_id,
        "warning": "Copy raw_key now. It will not be shown again.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Policy endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/policies/active", tags=["Policy"])
def active_policy(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    admin_key: str = Query(...),
):
    require_admin(admin_key)
    return {"tenant_id": tenant_id, "policy": get_active_policy(tenant_id)}


@app.post("/v1/policies", tags=["Policy"])
def create_policy(body: PolicyCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)

    conn = get_conn()

    if body.is_active:
        conn.execute(
            "UPDATE enterprise_policies SET is_active = 0 WHERE tenant_id = ?",
            (body.tenant_id,),
        )

    policy_id = f"policy_{uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO enterprise_policies
        (policy_id, tenant_id, name, description, version, rules_json, channel_rules_json,
         objective_restrictions_json, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            policy_id,
            body.tenant_id,
            body.name,
            body.description,
            1,
            json_dumps(body.rules),
            json_dumps(body.channel_rules),
            json_dumps(body.objective_restrictions),
            1 if body.is_active else 0,
            utcnow(),
            utcnow(),
        ),
    )

    conn.commit()
    conn.close()

    log_audit(
        tenant_id=body.tenant_id,
        event_type="POLICY_CHANGE",
        actor_id="admin",
        action="create",
        resource=policy_id,
        details={"name": body.name},
    )

    return {"created": True, "policy_id": policy_id, "tenant_id": body.tenant_id}


# ─────────────────────────────────────────────────────────────────────────────
# Governance endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/governance/retention", tags=["Governance"])
def get_retention(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    admin_key: str = Query(...),
):
    require_admin(admin_key)

    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM enterprise_retention WHERE tenant_id = ?",
        (tenant_id,),
    ).fetchone()

    if not row:
        conn.execute(
            """
            INSERT INTO enterprise_retention
            (tenant_id, retention_days, privacy_mode, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (tenant_id, DEFAULT_RETENTION_DAYS, DEFAULT_PRIVACY_MODE, utcnow()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM enterprise_retention WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchone()

    conn.close()

    delete_before = (
        datetime.datetime.utcnow() - datetime.timedelta(days=int(row["retention_days"]))
    ).isoformat()

    return {
        "tenant_id": tenant_id,
        "retention_days": row["retention_days"],
        "privacy_mode": row["privacy_mode"],
        "delete_before": delete_before,
    }


@app.post("/v1/governance/retention", tags=["Governance"])
def update_retention(body: RetentionUpdateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)

    if body.privacy_mode not in {"standard", "minimal", "strict"}:
        raise HTTPException(status_code=400, detail="privacy_mode must be standard, minimal, or strict")

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO enterprise_retention
        (tenant_id, retention_days, privacy_mode, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(tenant_id)
        DO UPDATE SET
            retention_days = excluded.retention_days,
            privacy_mode = excluded.privacy_mode,
            updated_at = excluded.updated_at
        """,
        (body.tenant_id, body.retention_days, body.privacy_mode, utcnow()),
    )
    conn.commit()
    conn.close()

    log_audit(
        tenant_id=body.tenant_id,
        event_type="RETENTION_UPDATED",
        actor_id="admin",
        action="update",
        resource=body.tenant_id,
        details={
            "retention_days": body.retention_days,
            "privacy_mode": body.privacy_mode,
        },
    )

    return {
        "tenant_id": body.tenant_id,
        "retention_days": body.retention_days,
        "privacy_mode": body.privacy_mode,
        "updated": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Audit endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/audit/logs", tags=["Audit"])
def audit_logs(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    limit: int = Query(50, ge=1, le=500),
    admin_key: str = Query(...),
):
    require_admin(admin_key)

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT * FROM enterprise_audit_logs
        WHERE tenant_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (tenant_id, limit),
    ).fetchall()
    conn.close()

    return {
        "tenant_id": tenant_id,
        "logs": [
            {
                "log_id": r["log_id"],
                "timestamp": r["timestamp"],
                "event_type": r["event_type"],
                "actor_id": r["actor_id"],
                "action": r["action"],
                "resource": r["resource"],
                "details": json_loads(r["details_json"], {}),
                "previous_hash": r["previous_hash"],
                "hash": r["hash"],
            }
            for r in rows
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Scan endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/scan", response_model=ScanResponseBody, tags=["Scan"])
def scan(body: ScanRequestBody, request: Request):
    requested_tenant_id = request.headers.get("X-Tenant-ID") or body.tenant_id or DEFAULT_TENANT_ID

    enterprise_key = authenticate_enterprise_key(
        raw_key=body.api_key,
        tenant_id=requested_tenant_id,
        required_scope="scan",
        required_permission="scan",
        consume_usage=True,
    )

    legacy_key = None

    if not enterprise_key:
        conn = get_conn()
        row = conn.execute(
            "SELECT key, plan, scan_count FROM api_keys WHERE key = ?",
            (body.api_key,),
        ).fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid API key")

        plan = row["plan"] or "free"
        scan_count = int(row["scan_count"] or 0)
        limit = PRO_TIER_MONTHLY_LIMIT if plan == "pro" else FREE_TIER_MONTHLY_LIMIT

        if scan_count >= limit:
            conn.close()
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": f"{plan.title()} plan limit of {limit:,} scans/month reached.",
                },
            )

        legacy_key = {
            "key": row["key"],
            "plan": plan,
            "scan_count": scan_count,
        }

        conn.close()

    tenant_id = enterprise_key["tenant_id"] if enterprise_key else DEFAULT_TENANT_ID

    result = run_pipeline(
        PipelineScanRequest(
            payload=body.payload,
            channel=body.channel,
            objective=body.objective,
            api_key=body.api_key,
            session_id=body.session_id,
        )
    )

    policy_result = evaluate_policy(
        tenant_id=tenant_id,
        payload=body.payload,
        channel=body.channel,
        objective=body.objective,
        risk_score=result.risk_score,
    )

    final_decision = apply_final_decision(
        pipeline_decision=result.decision,
        policy_action=policy_result["action"],
    )

    retention_conn = get_conn()
    retention = retention_conn.execute(
        "SELECT privacy_mode FROM enterprise_retention WHERE tenant_id = ?",
        (tenant_id,),
    ).fetchone()
    retention_conn.close()

    privacy_mode = retention["privacy_mode"] if retention else DEFAULT_PRIVACY_MODE

    log_audit(
        tenant_id=tenant_id,
        event_type="SCAN",
        actor_id="sdk",
        action="scan",
        resource=None,
        details={
            "channel": body.channel,
            "objective": body.objective,
            "decision": final_decision,
            "risk_score": round(float(result.risk_score), 2),
            "taxonomy_class": result.taxonomy_class,
            "payload_preview": sanitize_payload_preview(body.payload, privacy_mode=privacy_mode),
            "policy_reasoning": policy_result.get("reasoning", []),
        },
    )

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO scans
        (api_key, decision, risk_score, taxonomy_class, channel, objective, processing_ms, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            mask_key(body.api_key),
            final_decision,
            result.risk_score,
            result.taxonomy_class,
            body.channel,
            body.objective,
            result.processing_ms,
            utcnow(),
        ),
    )

    if legacy_key:
        conn.execute(
            "UPDATE api_keys SET scan_count = scan_count + 1 WHERE key = ?",
            (body.api_key,),
        )

    conn.commit()
    conn.close()

    phase2_trace = record_scan_phase2_trace_safe(
        tenant_id=tenant_id,
        payload=body.payload,
        channel=body.channel,
        objective=body.objective,
        decision=final_decision,
        risk_score=result.risk_score,
        taxonomy_class=result.taxonomy_class,
        previous_trace_id=body.previous_trace_id,
        session_id=body.session_id,
        policy_action=policy_result.get("action"),
    )

    return ScanResponseBody(
        decision=final_decision,
        risk_score=result.risk_score,
        taxonomy_class=result.taxonomy_class,
        recommended_action=recommended_action_for(final_decision, result.recommended_action),
        processing_ms=result.processing_ms,
        trace_id=phase2_trace.get("trace_id") if phase2_trace else None,
        trace=phase2_trace,
    )


@app.get("/usage", tags=["Auth"])
def usage(api_key: str):
    enterprise_key = authenticate_enterprise_key(
        raw_key=api_key,
        tenant_id=None,
        required_scope=None,
        required_permission=None,
        consume_usage=False,
    )

    if enterprise_key:
        limit = enterprise_key.get("monthly_limit")
        usage_count = enterprise_key.get("usage_count", 0)

        return {
            "plan": "enterprise",
            "tenant_id": enterprise_key["tenant_id"],
            "key_id": enterprise_key["key_id"],
            "role": enterprise_key["role"],
            "scopes": enterprise_key["scopes"],
            "scan_count": usage_count,
            "limit": limit,
            "remaining": None if limit is None else max(0, limit - usage_count),
        }

    conn = get_conn()
    row = conn.execute(
        "SELECT key, plan, scan_count FROM api_keys WHERE key = ?",
        (api_key,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")

    plan = row["plan"] or "free"
    limit = PRO_TIER_MONTHLY_LIMIT if plan == "pro" else FREE_TIER_MONTHLY_LIMIT
    scan_count = int(row["scan_count"] or 0)

    return {
        "plan": plan,
        "scan_count": scan_count,
        "limit": limit,
        "remaining": max(0, limit - scan_count),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Legacy admin endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/admin/reset-monthly-counts", include_in_schema=False)
def reset_monthly_counts(admin_key: str):
    require_admin(admin_key)

    conn = get_conn()
    conn.execute("UPDATE api_keys SET scan_count = 0")
    conn.execute("UPDATE enterprise_api_keys SET usage_count = 0")
    conn.commit()
    conn.close()

    return {"reset": True}


@app.get("/admin/stats", include_in_schema=False)
def stats(admin_key: str):
    require_admin(admin_key)

    conn = get_conn()

    total_scans = conn.execute("SELECT COUNT(*) AS c FROM scans").fetchone()["c"]
    total_legacy_keys = conn.execute("SELECT COUNT(*) AS c FROM api_keys").fetchone()["c"]
    total_enterprise_keys = conn.execute("SELECT COUNT(*) AS c FROM enterprise_api_keys").fetchone()["c"]

    blocked = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='BLOCKED'").fetchone()["c"]
    allowed = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='ALLOWED'").fetchone()["c"]
    review = conn.execute("SELECT COUNT(*) AS c FROM scans WHERE decision='REVIEW'").fetchone()["c"]

    conn.close()

    return {
        "total_api_keys": total_legacy_keys + total_enterprise_keys,
        "total_scans": total_scans,
        "decisions": {
            "BLOCKED": blocked,
            "ALLOWED": allowed,
            "REVIEW": review,
        },
    }
