# maisb/llm_proxy/api/phase3_dashboard.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Phase 3 — Analyst Dashboard + Telemetry Layer
#
# Place this file in:
#   MAISB/maisb/llm_proxy/api/phase3_dashboard.py
#
# It is Railway-safe and self-contained. It reads the existing SQLite usage DB
# and the Phase 2 trace tables:
#   phase2_channel_traces
#   phase2_trace_events
#   phase2_channel_reputation
#   phase2_explanations
#
# No new dependency is required.
# ─────────────────────────────────────────────────────────────────────────────

import csv
import datetime
import io
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")
PHASE3_VERSION = "2.3.0"

router = APIRouter(tags=["Phase 3 - Dashboard & Telemetry"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def utcnow() -> str:
    return datetime.datetime.utcnow().isoformat()


def cutoff_iso(hours: int) -> str:
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_admin(admin_key: str) -> None:
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row) if row else {}


def init_phase3_db() -> None:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase3_dashboard_views (
            view_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            config_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phase3_incidents (
            incident_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            trace_id TEXT,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            title TEXT NOT NULL,
            details_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_phase3_db()


# ── Models ───────────────────────────────────────────────────────────────────

class IncidentCreateRequest(BaseModel):
    tenant_id: str = DEFAULT_TENANT_ID
    trace_id: Optional[str] = None
    severity: str = "medium"
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)


class IncidentUpdateRequest(BaseModel):
    status: str = "closed"


# ── DB reads ──────────────────────────────────────────────────────────────────

def get_phase2_counts(conn: sqlite3.Connection, tenant_id: str) -> Dict[str, int]:
    counts = {"traces": 0, "events": 0, "explanations": 0, "reputation_rows": 0}
    table_map = {
        "traces": "phase2_channel_traces",
        "events": "phase2_trace_events",
        "explanations": "phase2_explanations",
        "reputation_rows": "phase2_channel_reputation",
    }

    for key, table in table_map.items():
        if table_exists(conn, table):
            row = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE tenant_id=?",
                (tenant_id,),
            ).fetchone()
            counts[key] = int(row["c"] or 0)

    return counts


def get_decision_summary(conn: sqlite3.Connection, tenant_id: str, hours: int) -> List[Dict[str, Any]]:
    if not table_exists(conn, "phase2_trace_events"):
        return []

    rows = conn.execute(
        """
        SELECT COALESCE(decision, 'UNKNOWN') AS decision,
               COUNT(*) AS count,
               ROUND(AVG(COALESCE(risk_score, 0)), 3) AS avg_risk,
               MAX(timestamp) AS last_seen
        FROM phase2_trace_events
        WHERE tenant_id = ? AND timestamp >= ?
        GROUP BY COALESCE(decision, 'UNKNOWN')
        ORDER BY count DESC
        """,
        (tenant_id, cutoff_iso(hours)),
    ).fetchall()

    return [row_to_dict(r) for r in rows]


def get_channel_summary(conn: sqlite3.Connection, tenant_id: str, hours: int) -> List[Dict[str, Any]]:
    if not table_exists(conn, "phase2_trace_events"):
        return []

    rows = conn.execute(
        """
        SELECT channel,
               COUNT(*) AS events,
               SUM(CASE WHEN decision='BLOCKED' THEN 1 ELSE 0 END) AS blocked,
               SUM(CASE WHEN decision='REVIEW' THEN 1 ELSE 0 END) AS review,
               ROUND(AVG(COALESCE(risk_score, 0)), 3) AS avg_risk,
               ROUND(AVG(COALESCE(trust_score, 0)), 3) AS avg_trust,
               MAX(timestamp) AS last_seen
        FROM phase2_trace_events
        WHERE tenant_id = ? AND timestamp >= ?
        GROUP BY channel
        ORDER BY events DESC, blocked DESC
        """,
        (tenant_id, cutoff_iso(hours)),
    ).fetchall()

    return [row_to_dict(r) for r in rows]


def get_recent_events(conn: sqlite3.Connection, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
    if not table_exists(conn, "phase2_trace_events"):
        return []

    rows = conn.execute(
        """
        SELECT event_id, trace_id, channel, transform, payload_preview,
               risk_score, trust_score, decision, timestamp
        FROM phase2_trace_events
        WHERE tenant_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (tenant_id, limit),
    ).fetchall()

    return [row_to_dict(r) for r in rows]


def get_recent_traces(conn: sqlite3.Connection, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
    if not table_exists(conn, "phase2_channel_traces"):
        return []

    rows = conn.execute(
        """
        SELECT trace_id, parent_trace_id, source_channel, final_risk_score,
               detection_layer, status, created_at, updated_at, journey_json,
               trust_degradation_json, propagation_graph_json
        FROM phase2_channel_traces
        WHERE tenant_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (tenant_id, limit),
    ).fetchall()

    traces = []
    for row in rows:
        item = row_to_dict(row)
        item["journey"] = json_loads(item.pop("journey_json", None), [])
        item["trust_degradation"] = json_loads(item.pop("trust_degradation_json", None), [])
        item["propagation_graph"] = json_loads(item.pop("propagation_graph_json", None), {"nodes": [], "edges": []})
        traces.append(item)

    return traces


def get_reputation(conn: sqlite3.Connection, tenant_id: str) -> List[Dict[str, Any]]:
    if not table_exists(conn, "phase2_channel_reputation"):
        return []

    rows = conn.execute(
        """
        SELECT channel, ROUND(trust_score, 3) AS trust_score, event_count,
               blocked_count, review_count, last_seen
        FROM phase2_channel_reputation
        WHERE tenant_id = ?
        ORDER BY event_count DESC, blocked_count DESC, channel ASC
        """,
        (tenant_id,),
    ).fetchall()

    return [row_to_dict(r) for r in rows]


def get_open_incidents(conn: sqlite3.Connection, tenant_id: str) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT incident_id, trace_id, severity, status, title, details_json,
               created_at, updated_at
        FROM phase3_incidents
        WHERE tenant_id = ? AND status != 'closed'
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (tenant_id,),
    ).fetchall()

    incidents = []
    for row in rows:
        item = row_to_dict(row)
        item["details"] = json_loads(item.pop("details_json", None), {})
        incidents.append(item)
    return incidents


def calculate_kpis(decision_summary: List[Dict[str, Any]], channel_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(int(d.get("count", 0)) for d in decision_summary)
    blocked = sum(int(d.get("count", 0)) for d in decision_summary if str(d.get("decision", "")).upper() == "BLOCKED")
    review = sum(int(d.get("count", 0)) for d in decision_summary if str(d.get("decision", "")).upper() == "REVIEW")
    allowed = sum(int(d.get("count", 0)) for d in decision_summary if str(d.get("decision", "")).upper() in {"ALLOWED", "ALLOW"})

    high_risk_channels = [
        c for c in channel_summary
        if float(c.get("avg_risk") or 0.0) >= 0.5 or int(c.get("blocked") or 0) > 0
    ]

    return {
        "total_events_window": total,
        "blocked": blocked,
        "review": review,
        "allowed": allowed,
        "block_rate": round(blocked / total, 3) if total else 0.0,
        "review_rate": round(review / total, 3) if total else 0.0,
        "high_risk_channel_count": len(high_risk_channels),
    }


# ── API endpoints ─────────────────────────────────────────────────────────────

@router.get("/v1/phase3/health")
def phase3_health() -> Dict[str, Any]:
    conn = get_conn()
    counts = get_phase2_counts(conn, DEFAULT_TENANT_ID)
    incident_count = conn.execute(
        "SELECT COUNT(*) AS c FROM phase3_incidents WHERE tenant_id=?",
        (DEFAULT_TENANT_ID,),
    ).fetchone()["c"]
    conn.close()

    return {
        "status": "ok",
        "phase3": True,
        "phase3_complete": True,
        "version": PHASE3_VERSION,
        "features": {
            "analyst_dashboard": True,
            "telemetry_summary": True,
            "trace_timeline": True,
            "trace_graph_view": True,
            "decision_summary": True,
            "channel_reputation_admin_view": True,
            "incident_notes": True,
            "json_csv_export": True,
        },
        "phase2_counts": counts,
        "incidents": int(incident_count or 0),
    }


@router.get("/v1/dashboard/summary")
def dashboard_summary(
    admin_key: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    hours: int = Query(24, ge=1, le=24 * 30),
) -> Dict[str, Any]:
    if admin_key:
        require_admin(admin_key)
    elif authorization:
        try:
            from api.profile_routes import resolve_profile_from_bearer  # type: ignore
            resolve_profile_from_bearer(authorization, allow_api_key=True)
        except Exception:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = get_conn()
    counts = get_phase2_counts(conn, tenant_id)
    decisions = get_decision_summary(conn, tenant_id, hours)
    channels = get_channel_summary(conn, tenant_id, hours)
    recent_events = get_recent_events(conn, tenant_id, 10)
    reputation = get_reputation(conn, tenant_id)
    incidents = get_open_incidents(conn, tenant_id)
    conn.close()

    return {
        "tenant_id": tenant_id,
        "window_hours": hours,
        "generated_at": utcnow(),
        "counts": counts,
        "kpis": calculate_kpis(decisions, channels),
        "decision_summary": decisions,
        "channel_summary": channels,
        "channel_reputation": reputation,
        "recent_events": recent_events,
        "open_incidents": incidents,
    }


@router.get("/v1/dashboard/decisions")
def dashboard_decisions(
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    hours: int = Query(24, ge=1, le=24 * 30),
) -> Dict[str, Any]:
    require_admin(admin_key)
    conn = get_conn()
    data = get_decision_summary(conn, tenant_id, hours)
    conn.close()
    return {"tenant_id": tenant_id, "window_hours": hours, "decisions": data}


@router.get("/v1/dashboard/channels")
def dashboard_channels(
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    hours: int = Query(24, ge=1, le=24 * 30),
) -> Dict[str, Any]:
    require_admin(admin_key)
    conn = get_conn()
    data = get_channel_summary(conn, tenant_id, hours)
    reputation = get_reputation(conn, tenant_id)
    conn.close()
    return {"tenant_id": tenant_id, "window_hours": hours, "channels": data, "reputation": reputation}


@router.get("/v1/dashboard/recent-traces")
def dashboard_recent_traces(
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    limit: int = Query(20, ge=1, le=200),
) -> Dict[str, Any]:
    require_admin(admin_key)
    conn = get_conn()
    data = get_recent_traces(conn, tenant_id, limit)
    conn.close()
    return {"tenant_id": tenant_id, "traces": data}


@router.get("/v1/dashboard/timeline")
def dashboard_timeline(
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    require_admin(admin_key)
    conn = get_conn()
    data = get_recent_events(conn, tenant_id, limit)
    conn.close()
    return {"tenant_id": tenant_id, "timeline": data}


@router.get("/v1/dashboard/trace-graph/{trace_id}")
def dashboard_trace_graph(
    trace_id: str,
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> Dict[str, Any]:
    require_admin(admin_key)

    conn = get_conn()
    if not table_exists(conn, "phase2_channel_traces"):
        conn.close()
        raise HTTPException(status_code=404, detail="Phase 2 trace table not found")

    row = conn.execute(
        """
        SELECT trace_id, tenant_id, source_channel, final_risk_score, detection_layer,
               journey_json, trust_degradation_json, propagation_graph_json,
               created_at, updated_at
        FROM phase2_channel_traces
        WHERE trace_id = ? AND tenant_id = ?
        """,
        (trace_id, tenant_id),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")

    item = row_to_dict(row)
    item["journey"] = json_loads(item.pop("journey_json", None), [])
    item["trust_degradation"] = json_loads(item.pop("trust_degradation_json", None), [])
    item["propagation_graph"] = json_loads(item.pop("propagation_graph_json", None), {"nodes": [], "edges": []})
    return item


@router.get("/v1/dashboard/export")
def dashboard_export(
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(200, ge=1, le=5000),
):
    require_admin(admin_key)

    conn = get_conn()
    events = get_recent_events(conn, tenant_id, limit)
    conn.close()

    if format == "json":
        return JSONResponse({"tenant_id": tenant_id, "events": events, "exported_at": utcnow()})

    out = io.StringIO()
    writer = csv.DictWriter(
        out,
        fieldnames=[
            "event_id", "trace_id", "channel", "transform", "payload_preview",
            "risk_score", "trust_score", "decision", "timestamp",
        ],
    )
    writer.writeheader()
    for row in events:
        writer.writerow(row)

    return PlainTextResponse(
        out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=maisb_phase3_events.csv"},
    )


@router.post("/v1/dashboard/incidents")
def create_incident(body: IncidentCreateRequest, admin_key: str = Query(...)) -> Dict[str, Any]:
    require_admin(admin_key)

    incident_id = f"inc_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"
    now = utcnow()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO phase3_incidents
        (incident_id, tenant_id, trace_id, severity, status, title, details_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)
        """,
        (
            incident_id,
            body.tenant_id,
            body.trace_id,
            body.severity,
            body.title,
            json.dumps(body.details, ensure_ascii=False),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "incident_id": incident_id,
        "tenant_id": body.tenant_id,
        "trace_id": body.trace_id,
        "severity": body.severity,
        "status": "open",
        "created": True,
    }


@router.post("/v1/dashboard/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: str,
    body: IncidentUpdateRequest,
    admin_key: str = Query(...),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> Dict[str, Any]:
    require_admin(admin_key)

    conn = get_conn()
    cur = conn.execute(
        """
        UPDATE phase3_incidents
        SET status = ?, updated_at = ?
        WHERE incident_id = ? AND tenant_id = ?
        """,
        (body.status, utcnow(), incident_id, tenant_id),
    )
    conn.commit()
    conn.close()

    return {"incident_id": incident_id, "tenant_id": tenant_id, "updated": cur.rowcount > 0, "status": body.status}


# ── Browser dashboard ─────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>MAISB Phase 3 Analyst Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root { --bg:#0b1020; --panel:#111936; --muted:#9aa4c7; --text:#eef2ff; --line:#27345f; --ok:#38d996; --warn:#f4c95d; --bad:#ff647c; --blue:#7aa2ff; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: ui-sans-serif, system-ui, Segoe UI, Arial; background: radial-gradient(circle at top left,#17265a,#0b1020 45%); color:var(--text); }
    header { padding:28px 32px; border-bottom:1px solid var(--line); }
    h1 { margin:0; font-size:28px; }
    .sub { color:var(--muted); margin-top:6px; }
    .wrap { padding:24px 32px; max-width:1400px; margin:0 auto; }
    .controls, .grid, .wide { margin-bottom:20px; }
    .controls { display:grid; grid-template-columns: 1.5fr 1.5fr 1fr .8fr auto; gap:12px; align-items:end; }
    label { font-size:12px; color:var(--muted); display:block; margin-bottom:6px; }
    input { width:100%; padding:12px 14px; border:1px solid var(--line); border-radius:12px; background:#0e1530; color:var(--text); outline:none; }
    button { padding:12px 18px; border:0; border-radius:12px; background:linear-gradient(135deg,#7aa2ff,#7c5cff); color:white; font-weight:700; cursor:pointer; }
    .grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:14px; }
    .card, .panel { background:rgba(17,25,54,.88); border:1px solid var(--line); border-radius:18px; box-shadow:0 16px 40px rgba(0,0,0,.25); }
    .card { padding:18px; }
    .k { color:var(--muted); font-size:13px; }
    .v { font-size:30px; font-weight:800; margin-top:8px; }
    .wide { display:grid; grid-template-columns: 1.1fr .9fr; gap:14px; }
    .panel { padding:18px; min-height:300px; }
    h2 { margin:0 0 14px; font-size:18px; }
    .row { display:grid; grid-template-columns: 120px 1fr 90px; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,.08); align-items:center; }
    .bar { height:10px; border-radius:999px; background:#0b1020; overflow:hidden; }
    .bar span { display:block; height:100%; background:linear-gradient(90deg,var(--blue),#7c5cff); }
    .pill { display:inline-block; padding:5px 9px; border-radius:999px; font-size:12px; font-weight:700; }
    .ALLOWED { background:rgba(56,217,150,.15); color:var(--ok); }
    .REVIEW { background:rgba(244,201,93,.15); color:var(--warn); }
    .BLOCKED { background:rgba(255,100,124,.15); color:var(--bad); }
    table { width:100%; border-collapse: collapse; }
    th, td { padding:10px; border-bottom:1px solid rgba(255,255,255,.08); text-align:left; font-size:13px; vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    .small { color:var(--muted); font-size:12px; }
    .error { color:var(--bad); padding:12px; display:none; }
    @media (max-width: 900px) { .controls,.grid,.wide { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<header>
  <h1>MAISB Phase 3 Analyst Dashboard</h1>
  <div class="sub">Telemetry, trace timeline, channel reputation, and decision summaries built on Phase 2 data.</div>
</header>
<div class="wrap">
  <div class="controls">
    <div><label>API Base URL</label><input id="baseUrl" value="" placeholder="leave empty for current host" /></div>
    <div><label>Admin Key</label><input id="adminKey" value="change_me_in_production" type="password" /></div>
    <div><label>Tenant ID</label><input id="tenantId" value="default" /></div>
    <div><label>Window Hours</label><input id="hours" value="24" type="number" min="1" max="720" /></div>
    <button onclick="loadDashboard()">Refresh</button>
  </div>
  <div id="err" class="error card"></div>

  <div class="grid">
    <div class="card"><div class="k">Events in Window</div><div id="kEvents" class="v">-</div></div>
    <div class="card"><div class="k">Blocked</div><div id="kBlocked" class="v">-</div></div>
    <div class="card"><div class="k">Review</div><div id="kReview" class="v">-</div></div>
    <div class="card"><div class="k">Block Rate</div><div id="kBlockRate" class="v">-</div></div>
  </div>

  <div class="wide">
    <div class="panel">
      <h2>Decision Summary</h2>
      <div id="decisionBars"></div>
    </div>
    <div class="panel">
      <h2>Channel Reputation</h2>
      <div id="reputation"></div>
    </div>
  </div>

  <div class="wide">
    <div class="panel">
      <h2>Recent Timeline</h2>
      <table>
        <thead><tr><th>Time</th><th>Channel</th><th>Decision</th><th>Risk</th><th>Preview</th></tr></thead>
        <tbody id="timeline"></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>Recent Trace Graphs</h2>
      <div id="traces"></div>
    </div>
  </div>
</div>

<script>
function apiBase() {
  const v = document.getElementById("baseUrl").value.trim();
  return v || window.location.origin;
}
function params(extra={}) {
  const p = new URLSearchParams({
    admin_key: document.getElementById("adminKey").value,
    tenant_id: document.getElementById("tenantId").value,
    hours: document.getElementById("hours").value,
    ...extra
  });
  return p.toString();
}
function pct(v) { return Math.round((v || 0) * 100) + "%"; }
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
async function getJSON(path) {
  const res = await fetch(apiBase() + path);
  if (!res.ok) throw new Error(path + " -> " + res.status + " " + await res.text());
  return await res.json();
}
async function loadDashboard() {
  const err = document.getElementById("err");
  err.style.display = "none";
  try {
    const data = await getJSON("/v1/dashboard/summary?" + params());
    const recent = await getJSON("/v1/dashboard/recent-traces?" + params({limit: 8}));

    document.getElementById("kEvents").textContent = data.kpis.total_events_window;
    document.getElementById("kBlocked").textContent = data.kpis.blocked;
    document.getElementById("kReview").textContent = data.kpis.review;
    document.getElementById("kBlockRate").textContent = pct(data.kpis.block_rate);

    const maxDecision = Math.max(1, ...data.decision_summary.map(d => d.count));
    document.getElementById("decisionBars").innerHTML = data.decision_summary.map(d => `
      <div class="row">
        <div><span class="pill ${esc(d.decision)}">${esc(d.decision)}</span></div>
        <div class="bar"><span style="width:${(d.count/maxDecision)*100}%"></span></div>
        <div>${d.count} <span class="small">avg ${d.avg_risk ?? 0}</span></div>
      </div>
    `).join("") || "<div class='small'>No decision data yet.</div>";

    document.getElementById("reputation").innerHTML = data.channel_reputation.map(r => `
      <div class="row">
        <div>${esc(r.channel)}</div>
        <div class="bar"><span style="width:${(r.trust_score || 0)*100}%"></span></div>
        <div>${r.trust_score} <span class="small">${r.event_count} events</span></div>
      </div>
    `).join("") || "<div class='small'>No reputation data yet.</div>";

    document.getElementById("timeline").innerHTML = data.recent_events.map(e => `
      <tr>
        <td class="small">${esc(e.timestamp)}</td>
        <td>${esc(e.channel)}</td>
        <td><span class="pill ${esc(e.decision)}">${esc(e.decision)}</span></td>
        <td>${e.risk_score}</td>
        <td class="small">${esc(e.payload_preview)}</td>
      </tr>
    `).join("") || "<tr><td colspan='5' class='small'>No events yet.</td></tr>";

    document.getElementById("traces").innerHTML = recent.traces.map(t => {
      const steps = (t.journey || []).map((s,i) => `<span class="pill">${i+1}. ${esc(s.channel)}</span>`).join(" → ");
      const loss = (t.trust_degradation || []).slice(-1)[0]?.cumulative_loss ?? 0;
      return `<div class="card" style="margin-bottom:10px">
        <div><b>${esc(t.trace_id)}</b></div>
        <div class="small">risk ${t.final_risk_score} | trust loss ${loss} | detection ${esc(t.detection_layer || "-")}</div>
        <div style="margin-top:8px">${steps || "<span class='small'>No steps</span>"}</div>
      </div>`;
    }).join("") || "<div class='small'>No traces yet.</div>";
  } catch (e) {
    err.textContent = e.message;
    err.style.display = "block";
  }
}
loadDashboard();
</script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
