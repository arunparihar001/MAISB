# maisb/llm_proxy/api/phase4_soc.py
# MAISB Phase 4 — Production Hardening + SOC Workflow Layer
# Railway-safe self-contained router under /maisb/llm_proxy.

import csv
import datetime as dt
import hashlib
import io
import json
import os
import secrets
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
PHASE4_VERSION = "2.4.0"

router = APIRouter(tags=["Phase 4 - SOC Hardening"])


def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat()


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


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def init_phase4_db() -> None:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_soc_cases (
            case_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            trace_id TEXT,
            incident_id TEXT,
            title TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            priority INTEGER DEFAULT 3,
            status TEXT DEFAULT 'open',
            owner TEXT,
            risk_score REAL DEFAULT 0,
            source_channel TEXT,
            detection_layer TEXT,
            tags TEXT DEFAULT '[]',
            evidence TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_case_comments (
            comment_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            author TEXT DEFAULT 'analyst',
            comment TEXT NOT NULL,
            visibility TEXT DEFAULT 'internal',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_case_history (
            history_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            actor TEXT DEFAULT 'system',
            action TEXT NOT NULL,
            from_value TEXT,
            to_value TEXT,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_security_audit (
            audit_id TEXT PRIMARY KEY,
            tenant_id TEXT DEFAULT 'default',
            actor TEXT DEFAULT 'unknown',
            role TEXT DEFAULT 'viewer',
            action TEXT NOT NULL,
            resource TEXT,
            decision TEXT DEFAULT 'allowed',
            ip_address TEXT,
            user_agent TEXT,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_mobile_telemetry (
            telemetry_id TEXT PRIMARY KEY,
            tenant_id TEXT DEFAULT 'default',
            trace_id TEXT,
            session_id TEXT,
            device_id_hash TEXT,
            sdk_version TEXT,
            app_package TEXT,
            platform TEXT DEFAULT 'android',
            channel TEXT,
            decision TEXT,
            risk_score REAL DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase4_retention_runs (
            run_id TEXT PRIMARY KEY,
            tenant_id TEXT DEFAULT 'default',
            dry_run INTEGER DEFAULT 1,
            days_to_keep INTEGER DEFAULT 90,
            deleted_counts TEXT DEFAULT '{}',
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase4_cases_tenant_status ON phase4_soc_cases(tenant_id,status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase4_cases_trace ON phase4_soc_cases(trace_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase4_comments_case ON phase4_case_comments(case_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase4_history_case ON phase4_case_history(case_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase4_mobile_trace ON phase4_mobile_telemetry(trace_id)")
    conn.commit()
    conn.close()


init_phase4_db()


ROLE_PERMISSIONS = {
    "admin": {"case:read", "case:write", "case:assign", "case:close", "comment:read", "comment:write", "audit:read", "retention:run", "telemetry:write", "export:read", "security:read"},
    "analyst": {"case:read", "case:write", "case:assign", "comment:read", "comment:write", "telemetry:write", "export:read", "security:read"},
    "soc": {"case:read", "case:write", "case:assign", "comment:read", "comment:write", "telemetry:write", "export:read", "security:read"},
    "auditor": {"case:read", "comment:read", "audit:read", "export:read", "security:read"},
    "viewer": {"case:read", "comment:read", "security:read"},
}


def log_security_event(
    tenant_id: str,
    actor: str,
    role: str,
    action: str,
    resource: Optional[str],
    decision: str,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    conn = get_conn()
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    conn.execute(
        """
        INSERT INTO phase4_security_audit
        (audit_id, tenant_id, actor, role, action, resource, decision, ip_address, user_agent, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (f"aud_{secrets.token_hex(8)}", tenant_id, actor, role, action, resource, decision, ip_address, user_agent, jdump(details or {}), utcnow()),
    )
    conn.commit()
    conn.close()


def resolve_auth(
    request: Request,
    admin_key: Optional[str],
    authorization: Optional[str],
    x_maisb_role: Optional[str],
    required_permission: str,
    tenant_id: str = "default",
) -> Dict[str, str]:
    token = ""
    auth_mode = "none"
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        auth_mode = "bearer"
    if not token and admin_key:
        token = admin_key
        auth_mode = "query_admin_key_deprecated"
    if not secrets.compare_digest((token or "").encode(), (ADMIN_KEY or "").encode()):
        log_security_event(tenant_id, "unknown", "none", f"auth_denied:{required_permission}", str(request.url.path), "denied", request, {"auth_mode": auth_mode})
        raise HTTPException(status_code=403, detail="Forbidden: valid admin bearer token required")
    role = (x_maisb_role or "admin").lower().strip()
    if role not in ROLE_PERMISSIONS:
        role = "viewer"
    if required_permission not in ROLE_PERMISSIONS[role]:
        log_security_event(tenant_id, "admin", role, f"permission_denied:{required_permission}", str(request.url.path), "denied", request, {"auth_mode": auth_mode})
        raise HTTPException(status_code=403, detail=f"Forbidden: role '{role}' lacks '{required_permission}'")
    if auth_mode == "query_admin_key_deprecated":
        log_security_event(tenant_id, "admin", role, "deprecated_query_admin_key_used", str(request.url.path), "allowed", request, {"recommendation": "Use Authorization: Bearer <ADMIN_KEY>"})
    return {"actor": "admin", "role": role, "auth_mode": auth_mode}


def add_case_history(conn: sqlite3.Connection, case_id: str, tenant_id: str, actor: str, action: str, from_value: Optional[str] = None, to_value: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    conn.execute(
        """
        INSERT INTO phase4_case_history
        (history_id, case_id, tenant_id, actor, action, from_value, to_value, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (f"hist_{secrets.token_hex(8)}", case_id, tenant_id, actor, action, from_value, to_value, jdump(details or {}), utcnow()),
    )


class CaseCreateRequest(BaseModel):
    tenant_id: str = "default"
    trace_id: Optional[str] = None
    incident_id: Optional[str] = None
    title: str
    severity: str = Field("medium", pattern="^(low|medium|high|critical)$")
    priority: int = Field(3, ge=1, le=5)
    owner: Optional[str] = None
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    source_channel: Optional[str] = None
    detection_layer: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(open|triage|investigating|contained|resolved|closed)$")
    reason: Optional[str] = None
    actor: str = "analyst"


class CaseAssignRequest(BaseModel):
    owner: str
    actor: str = "analyst"


class CaseCommentRequest(BaseModel):
    author: str = "analyst"
    comment: str
    visibility: str = Field("internal", pattern="^(internal|public|private)$")


class MobileTelemetryRequest(BaseModel):
    tenant_id: str = "default"
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    sdk_version: str = "unknown"
    app_package: Optional[str] = None
    platform: str = "android"
    channel: Optional[str] = None
    decision: Optional[str] = None
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    latency_ms: int = Field(0, ge=0)
    details: Dict[str, Any] = Field(default_factory=dict)


def row_to_case(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "case_id": row["case_id"], "tenant_id": row["tenant_id"], "trace_id": row["trace_id"], "incident_id": row["incident_id"],
        "title": row["title"], "severity": row["severity"], "priority": row["priority"], "status": row["status"],
        "owner": row["owner"], "risk_score": row["risk_score"], "source_channel": row["source_channel"], "detection_layer": row["detection_layer"],
        "tags": jload(row["tags"], []), "evidence": jload(row["evidence"], {}), "created_at": row["created_at"], "updated_at": row["updated_at"], "closed_at": row["closed_at"],
    }


def count_table(conn: sqlite3.Connection, table_name: str) -> int:
    if not table_exists(conn, table_name):
        return 0
    return conn.execute(f"SELECT COUNT(*) AS c FROM {table_name}").fetchone()["c"]


@router.get("/soc", response_class=HTMLResponse)
def soc_console():
    return HTMLResponse("""
<!doctype html><html><head><meta charset="utf-8"><title>MAISB Phase 4 SOC Console</title>
<style>
body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:#071022;color:#eaf0ff}
header{padding:34px 42px;background:linear-gradient(135deg,#09142d,#101d4a);border-bottom:1px solid #22315f}
h1{margin:0;font-size:32px}p{color:#aab7de}.wrap{padding:28px 42px;display:grid;gap:18px;grid-template-columns:repeat(4,minmax(0,1fr))}
.card{background:#101a38;border:1px solid #27386d;border-radius:18px;padding:20px;box-shadow:0 14px 40px rgba(0,0,0,.25)}
.card h2{margin:0 0 8px;font-size:15px;color:#bac7ff}.num{font-size:34px;font-weight:800}.wide{grid-column:span 2}
input,button{border-radius:12px;padding:12px;border:1px solid #384b84;background:#0b1430;color:#fff}button{background:#6857ff;cursor:pointer;font-weight:700}
pre{white-space:pre-wrap;color:#d8e0ff;font-size:12px;max-height:420px;overflow:auto}
</style></head><body>
<header><h1>MAISB Phase 4 SOC Console</h1><p>Production hardening, case management, assignments, comments, retention checks, and mobile telemetry.</p></header>
<div class="wrap">
<div class="card"><h2>Open Cases</h2><div class="num" id="openCases">-</div></div>
<div class="card"><h2>Critical / High</h2><div class="num" id="highCases">-</div></div>
<div class="card"><h2>Mobile Telemetry</h2><div class="num" id="mobileTelemetry">-</div></div>
<div class="card"><h2>Security Audit Events</h2><div class="num" id="auditEvents">-</div></div>
<div class="card wide"><h2>Settings</h2><input id="adminKey" placeholder="Admin key" type="password" style="width:45%"><input id="tenantId" value="default" style="width:20%"><button onclick="loadData()">Refresh</button><p>Preferred auth is Authorization: Bearer &lt;ADMIN_KEY&gt;. Query admin_key remains for staging compatibility.</p></div>
<div class="card wide"><h2>Phase 4 Health</h2><pre id="healthOut">Click Refresh</pre></div>
<div class="card wide"><h2>Risk Queue</h2><pre id="riskOut">Click Refresh</pre></div>
<div class="card wide"><h2>Cases</h2><pre id="caseOut">Click Refresh</pre></div>
</div>
<script>
async function getJson(path){const key=document.getElementById("adminKey").value;const sep=path.includes("?")?"&":"?";const res=await fetch(path+sep+"admin_key="+encodeURIComponent(key),{headers:{"X-MAISB-Role":"admin"}});return await res.json();}
async function loadData(){const tenant=document.getElementById("tenantId").value||"default";const health=await getJson("/v1/phase4/health?tenant_id="+encodeURIComponent(tenant));document.getElementById("healthOut").textContent=JSON.stringify(health,null,2);document.getElementById("openCases").textContent=health.counts.open_cases??0;document.getElementById("highCases").textContent=health.counts.high_priority_cases??0;document.getElementById("mobileTelemetry").textContent=health.counts.mobile_telemetry??0;document.getElementById("auditEvents").textContent=health.counts.security_audit_events??0;const risk=await getJson("/v1/soc/risk-queue?tenant_id="+encodeURIComponent(tenant));document.getElementById("riskOut").textContent=JSON.stringify(risk,null,2);const cases=await getJson("/v1/soc/cases?tenant_id="+encodeURIComponent(tenant));document.getElementById("caseOut").textContent=JSON.stringify(cases,null,2);}
</script></body></html>
    """)


@router.get("/v1/phase4/health")
def phase4_health(request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "security:read", tenant_id)
    conn = get_conn()
    open_cases = conn.execute("SELECT COUNT(*) AS c FROM phase4_soc_cases WHERE tenant_id=? AND status NOT IN ('closed','resolved')", (tenant_id,)).fetchone()["c"]
    high_priority_cases = conn.execute("SELECT COUNT(*) AS c FROM phase4_soc_cases WHERE tenant_id=? AND severity IN ('high','critical') AND status NOT IN ('closed','resolved')", (tenant_id,)).fetchone()["c"]
    counts = {
        "cases": count_table(conn, "phase4_soc_cases"),
        "open_cases": open_cases,
        "high_priority_cases": high_priority_cases,
        "comments": count_table(conn, "phase4_case_comments"),
        "case_history": count_table(conn, "phase4_case_history"),
        "security_audit_events": count_table(conn, "phase4_security_audit"),
        "mobile_telemetry": count_table(conn, "phase4_mobile_telemetry"),
        "retention_runs": count_table(conn, "phase4_retention_runs"),
        "phase2_traces": count_table(conn, "phase2_channel_traces"),
        "phase2_events": count_table(conn, "phase2_trace_events"),
        "phase3_incidents": count_table(conn, "phase3_incidents"),
    }
    conn.close()
    return {
        "status": "ok", "phase4": True, "phase4_complete": True, "version": PHASE4_VERSION,
        "auth": {"mode": auth["auth_mode"], "role": auth["role"], "query_admin_key_deprecated": auth["auth_mode"] == "query_admin_key_deprecated", "recommended": "Use Authorization: Bearer <ADMIN_KEY>"},
        "features": {
            "bearer_admin_auth": True, "rbac_permissions": True, "soc_case_management": True, "case_assignment": True,
            "case_status_history": True, "case_comments": True, "risk_queue": True, "security_audit_events": True,
            "json_csv_export": True, "retention_runner": True, "mobile_sdk_telemetry": True, "soc_console": True,
        },
        "counts": counts,
    }


@router.get("/v1/security/auth/check")
def auth_check(request: Request, tenant_id: str = Query("default"), required_permission: str = Query("case:read"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, required_permission, tenant_id)
    return {"authorized": True, "tenant_id": tenant_id, "role": auth["role"], "permissions": sorted(ROLE_PERMISSIONS[auth["role"]]), "auth_mode": auth["auth_mode"]}


@router.get("/v1/security/audit/events")
def security_audit_events(request: Request, tenant_id: str = Query("default"), limit: int = Query(50, ge=1, le=500), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "audit:read", tenant_id)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM phase4_security_audit WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?", (tenant_id, limit)).fetchall()
    conn.close()
    return {"tenant_id": tenant_id, "events": [{**dict(row), "details": jload(row["details"], {})} for row in rows]}


@router.post("/v1/soc/cases")
def create_case(body: CaseCreateRequest, request: Request, admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "case:write", body.tenant_id)
    case_id = f"case_{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
    now = utcnow()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO phase4_soc_cases
        (case_id, tenant_id, trace_id, incident_id, title, severity, priority, status, owner, risk_score, source_channel, detection_layer, tags, evidence, created_at, updated_at, closed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """,
        (case_id, body.tenant_id, body.trace_id, body.incident_id, body.title, body.severity, body.priority, body.owner, body.risk_score, body.source_channel, body.detection_layer, jdump(body.tags), jdump(body.evidence), now, now),
    )
    add_case_history(conn, case_id, body.tenant_id, auth["actor"], "case_created", None, "open", body.model_dump())
    conn.commit()
    row = conn.execute("SELECT * FROM phase4_soc_cases WHERE case_id=?", (case_id,)).fetchone()
    conn.close()
    log_security_event(body.tenant_id, auth["actor"], auth["role"], "case_created", case_id, "allowed", request)
    return row_to_case(row)


@router.get("/v1/soc/cases")
def list_cases(request: Request, tenant_id: str = Query("default"), status: Optional[str] = Query(None), severity: Optional[str] = Query(None), owner: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=500), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "case:read", tenant_id)
    query = "SELECT * FROM phase4_soc_cases WHERE tenant_id=?"
    params: List[Any] = [tenant_id]
    if status:
        query += " AND status=?"; params.append(status)
    if severity:
        query += " AND severity=?"; params.append(severity)
    if owner:
        query += " AND owner=?"; params.append(owner)
    query += " ORDER BY updated_at DESC LIMIT ?"; params.append(limit)
    conn = get_conn()
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return {"tenant_id": tenant_id, "cases": [row_to_case(r) for r in rows]}


@router.get("/v1/soc/cases/{case_id}")
def get_case(case_id: str, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "case:read", tenant_id)
    conn = get_conn()
    row = conn.execute("SELECT * FROM phase4_soc_cases WHERE tenant_id=? AND case_id=?", (tenant_id, case_id)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return row_to_case(row)


@router.post("/v1/soc/cases/{case_id}/assign")
def assign_case(case_id: str, body: CaseAssignRequest, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "case:assign", tenant_id)
    conn = get_conn()
    row = conn.execute("SELECT * FROM phase4_soc_cases WHERE tenant_id=? AND case_id=?", (tenant_id, case_id)).fetchone()
    if not row:
        conn.close(); raise HTTPException(status_code=404, detail="Case not found")
    old_owner = row["owner"]
    conn.execute("UPDATE phase4_soc_cases SET owner=?, updated_at=? WHERE tenant_id=? AND case_id=?", (body.owner, utcnow(), tenant_id, case_id))
    add_case_history(conn, case_id, tenant_id, body.actor or auth["actor"], "assigned", old_owner, body.owner)
    conn.commit(); conn.close()
    log_security_event(tenant_id, auth["actor"], auth["role"], "case_assigned", case_id, "allowed", request)
    return {"case_id": case_id, "owner": body.owner, "previous_owner": old_owner}


@router.post("/v1/soc/cases/{case_id}/status")
def update_case_status(case_id: str, body: CaseStatusUpdateRequest, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    required = "case:close" if body.status in {"resolved", "closed"} else "case:write"
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, required, tenant_id)
    conn = get_conn()
    row = conn.execute("SELECT * FROM phase4_soc_cases WHERE tenant_id=? AND case_id=?", (tenant_id, case_id)).fetchone()
    if not row:
        conn.close(); raise HTTPException(status_code=404, detail="Case not found")
    old_status = row["status"]
    closed_at = utcnow() if body.status in {"resolved", "closed"} else None
    conn.execute("UPDATE phase4_soc_cases SET status=?, updated_at=?, closed_at=? WHERE tenant_id=? AND case_id=?", (body.status, utcnow(), closed_at, tenant_id, case_id))
    add_case_history(conn, case_id, tenant_id, body.actor or auth["actor"], "status_changed", old_status, body.status, {"reason": body.reason})
    conn.commit(); conn.close()
    log_security_event(tenant_id, auth["actor"], auth["role"], "case_status_changed", case_id, "allowed", request)
    return {"case_id": case_id, "from": old_status, "to": body.status, "closed_at": closed_at}


@router.post("/v1/soc/cases/{case_id}/comments")
def add_comment(case_id: str, body: CaseCommentRequest, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "comment:write", tenant_id)
    comment_id = f"com_{secrets.token_hex(8)}"
    conn = get_conn()
    exists = conn.execute("SELECT case_id FROM phase4_soc_cases WHERE tenant_id=? AND case_id=?", (tenant_id, case_id)).fetchone()
    if not exists:
        conn.close(); raise HTTPException(status_code=404, detail="Case not found")
    conn.execute("INSERT INTO phase4_case_comments (comment_id, case_id, tenant_id, author, comment, visibility, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (comment_id, case_id, tenant_id, body.author, body.comment, body.visibility, utcnow()))
    add_case_history(conn, case_id, tenant_id, body.author or auth["actor"], "comment_added", None, comment_id)
    conn.execute("UPDATE phase4_soc_cases SET updated_at=? WHERE tenant_id=? AND case_id=?", (utcnow(), tenant_id, case_id))
    conn.commit(); conn.close()
    log_security_event(tenant_id, auth["actor"], auth["role"], "case_comment_added", case_id, "allowed", request)
    return {"comment_id": comment_id, "case_id": case_id, "created": True}


@router.get("/v1/soc/cases/{case_id}/comments")
def list_comments(case_id: str, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "comment:read", tenant_id)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM phase4_case_comments WHERE tenant_id=? AND case_id=? ORDER BY created_at ASC", (tenant_id, case_id)).fetchall()
    conn.close()
    return {"case_id": case_id, "comments": [dict(r) for r in rows]}


@router.get("/v1/soc/cases/{case_id}/timeline")
def case_timeline(case_id: str, request: Request, tenant_id: str = Query("default"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "case:read", tenant_id)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM phase4_case_history WHERE tenant_id=? AND case_id=? ORDER BY created_at ASC", (tenant_id, case_id)).fetchall()
    conn.close()
    return {"case_id": case_id, "timeline": [{**dict(r), "details": jload(r["details"], {})} for r in rows]}


@router.get("/v1/soc/risk-queue")
def risk_queue(request: Request, tenant_id: str = Query("default"), limit: int = Query(25, ge=1, le=200), min_risk: float = Query(0.5, ge=0.0, le=1.0), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "case:read", tenant_id)
    conn = get_conn()
    items: List[Dict[str, Any]] = []
    if table_exists(conn, "phase2_trace_events"):
        rows = conn.execute(
            """
            SELECT
                trace_id,
                event_id,
                channel,
                decision,
                risk_score,
                trust_score,
                timestamp AS created_at
            FROM phase2_trace_events
            WHERE tenant_id = ?
              AND (risk_score >= ? OR decision IN ('BLOCKED', 'REVIEW'))
            ORDER BY risk_score DESC, timestamp DESC
            LIMIT ?
            """,
            (tenant_id, min_risk, limit),
        ).fetchall()
        items.extend([dict(r) for r in rows])
    if not items:
        rows = conn.execute("SELECT case_id, trace_id, severity, status, risk_score, title, created_at FROM phase4_soc_cases WHERE tenant_id=? AND risk_score>=? ORDER BY risk_score DESC, created_at DESC LIMIT ?", (tenant_id, min_risk, limit)).fetchall()
        items.extend([dict(r) for r in rows])
    conn.close()
    return {"tenant_id": tenant_id, "min_risk": min_risk, "items": items}


@router.get("/v1/soc/search")
def soc_search(request: Request, tenant_id: str = Query("default"), q: str = Query(..., min_length=1), limit: int = Query(25, ge=1, le=100), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "case:read", tenant_id)
    pattern = f"%{q}%"
    conn = get_conn()
    cases = conn.execute("SELECT * FROM phase4_soc_cases WHERE tenant_id=? AND (case_id LIKE ? OR trace_id LIKE ? OR title LIKE ? OR severity LIKE ? OR status LIKE ? OR owner LIKE ?) ORDER BY updated_at DESC LIMIT ?", (tenant_id, pattern, pattern, pattern, pattern, pattern, pattern, limit)).fetchall()
    comments = conn.execute("SELECT * FROM phase4_case_comments WHERE tenant_id=? AND (comment LIKE ? OR author LIKE ?) ORDER BY created_at DESC LIMIT ?", (tenant_id, pattern, pattern, limit)).fetchall()
    conn.close()
    return {"tenant_id": tenant_id, "query": q, "cases": [row_to_case(r) for r in cases], "comments": [dict(r) for r in comments]}


@router.get("/v1/soc/export")
def soc_export(request: Request, tenant_id: str = Query("default"), format: str = Query("json", pattern="^(json|csv)$"), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    resolve_auth(request, admin_key, authorization, x_maisb_role, "export:read", tenant_id)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM phase4_soc_cases WHERE tenant_id=? ORDER BY updated_at DESC", (tenant_id,)).fetchall()
    cases = [row_to_case(r) for r in rows]
    conn.close()
    if format == "json":
        return {"tenant_id": tenant_id, "cases": cases}
    output = io.StringIO()
    fields = ["case_id", "tenant_id", "trace_id", "incident_id", "title", "severity", "priority", "status", "owner", "risk_score", "source_channel", "detection_layer", "created_at", "updated_at", "closed_at"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in cases:
        writer.writerow({k: item.get(k) for k in fields})
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="maisb_phase4_cases.csv"'})


@router.post("/v1/security/retention/run")
def run_retention(request: Request, tenant_id: str = Query("default"), days_to_keep: int = Query(90, ge=1, le=3650), dry_run: bool = Query(True), admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "retention:run", tenant_id)
    cutoff = (dt.datetime.utcnow() - dt.timedelta(days=days_to_keep)).replace(microsecond=0).isoformat()
    candidates = {"phase2_trace_events": "timestamp", "phase4_security_audit": "created_at", "phase4_mobile_telemetry": "created_at"}
    conn = get_conn()
    deleted_counts: Dict[str, int] = {}
    for table, date_col in candidates.items():
        if not table_exists(conn, table):
            deleted_counts[table] = 0
            continue
        count = conn.execute(f"SELECT COUNT(*) AS c FROM {table} WHERE tenant_id=? AND {date_col} < ?", (tenant_id, cutoff)).fetchone()["c"]
        deleted_counts[table] = count
        if not dry_run and count:
            conn.execute(f"DELETE FROM {table} WHERE tenant_id=? AND {date_col} < ?", (tenant_id, cutoff))
    run_id = f"ret_{secrets.token_hex(8)}"
    now = utcnow()
    conn.execute("INSERT INTO phase4_retention_runs (run_id, tenant_id, dry_run, days_to_keep, deleted_counts, started_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (run_id, tenant_id, 1 if dry_run else 0, days_to_keep, jdump(deleted_counts), now, now))
    conn.commit()
    conn.close()
    log_security_event(tenant_id, auth["actor"], auth["role"], "retention_run", run_id, "allowed", request, {"dry_run": dry_run, "days_to_keep": days_to_keep, "deleted_counts": deleted_counts})
    return {"run_id": run_id, "tenant_id": tenant_id, "dry_run": dry_run, "days_to_keep": days_to_keep, "cutoff": cutoff, "deleted_counts": deleted_counts}


@router.post("/v1/sdk/mobile/telemetry")
def mobile_telemetry(body: MobileTelemetryRequest, request: Request, admin_key: Optional[str] = Query(None), authorization: Optional[str] = Header(None), x_maisb_role: Optional[str] = Header(None)):
    auth = resolve_auth(request, admin_key, authorization, x_maisb_role, "telemetry:write", body.tenant_id)
    telemetry_id = f"mob_{secrets.token_hex(8)}"
    device_id_hash = hashlib.sha256((body.device_id or "unknown").encode("utf-8")).hexdigest()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO phase4_mobile_telemetry
        (telemetry_id, tenant_id, trace_id, session_id, device_id_hash, sdk_version, app_package, platform, channel, decision, risk_score, latency_ms, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (telemetry_id, body.tenant_id, body.trace_id, body.session_id, device_id_hash, body.sdk_version, body.app_package, body.platform, body.channel, body.decision, body.risk_score, body.latency_ms, jdump(body.details), utcnow()),
    )
    conn.commit()
    conn.close()
    log_security_event(body.tenant_id, auth["actor"], auth["role"], "mobile_telemetry_recorded", telemetry_id, "allowed", request)
    return {"telemetry_id": telemetry_id, "recorded": True, "trace_id": body.trace_id}
