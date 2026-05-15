# maisb/llm_proxy/api/phase2_trace.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Phase 2 — Cross-Channel Trace Engine
#
# Self-contained Railway-safe implementation.
# Place this file in:
#   MAISB/maisb/llm_proxy/api/phase2_trace.py
#
# Why self-contained?
# Your Phase 1 live deployment uses Railway root:
#   /maisb/llm_proxy
# so this file avoids importing sibling maisb/core modules at runtime.
# ─────────────────────────────────────────────────────────────────────────────

import datetime
import difflib
import hashlib
import json
import os
import secrets
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("DB_PATH", "usage.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
DEFAULT_TENANT_ID = os.environ.get("DEFAULT_TENANT_ID", "default")

PHASE2_VERSION = "2.2.0"

# Adaptive trust scores. Low trust means higher supply-chain risk.
CHANNEL_TRUST_SCORES: Dict[str, float] = {
    "internal_api": 0.93,
    "authenticated_user": 0.85,
    "api_response": 0.72,
    "file_upload": 0.40,
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
    "pdf_file": 0.35,
    "ocr_engine": 0.30,
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

router = APIRouter(tags=["Phase 2 - Trace Engine"])


# ── Models ───────────────────────────────────────────────────────────────────

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


# ── DB helpers ────────────────────────────────────────────────────────────────

def utcnow() -> str:
    return datetime.datetime.utcnow().isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def require_admin(admin_key: str) -> None:
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def preview_payload(payload: str, max_len: int = 160) -> str:
    text = " ".join((payload or "").split())
    return text[:max_len]


def generate_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def init_phase2_db() -> None:
    conn = get_conn()

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

    conn.commit()
    conn.close()


# Initialize on import so routes work immediately.
init_phase2_db()


# ── Trust scoring ─────────────────────────────────────────────────────────────

def reputation_adjustment(tenant_id: str, channel: str) -> float:
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

    if not row or row["event_count"] == 0:
        return 0.0

    event_count = max(1, int(row["event_count"]))
    bad_ratio = (int(row["blocked_count"]) + 0.5 * int(row["review_count"])) / event_count
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

    rep_delta = reputation_adjustment(tenant_id, normalized_channel)
    if rep_delta:
        adjustments.append({"factor": "channel_reputation", "delta": rep_delta})

    final = base + sum(float(a["delta"]) for a in adjustments)
    final = max(0.0, min(1.0, final))

    if final >= 0.75:
        level = "high"
    elif final >= 0.45:
        level = "medium"
    elif final >= 0.20:
        level = "low"
    else:
        level = "critical_low"

    return {
        "channel": normalized_channel,
        "base_trust": round(base, 3),
        "adjustments": adjustments,
        "trust_score": round(final, 3),
        "trust_level": level,
    }


def update_channel_reputation(tenant_id: str, channel: str, trust_score: float, decision: Optional[str]) -> None:
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
        old_count = int(existing["event_count"])
        new_count = old_count + 1
        old_score = float(existing["trust_score"])
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


# ── Trace engine ──────────────────────────────────────────────────────────────

def detect_transform(previous_hash: Optional[str], previous_payload_preview: Optional[str], payload: str, channel: str) -> str:
    if not previous_hash:
        return "none"

    current_hash = sha256_text(payload)
    if previous_hash == current_hash:
        return "copy"

    ch = (channel or "").lower()
    if "ocr" in ch:
        return "ocr"
    if ch in {"agent", "llm", "api_response"}:
        return "context_inject"

    prev = previous_payload_preview or ""
    curr = preview_payload(payload)
    if prev and curr:
        ratio = difflib.SequenceMatcher(None, prev.lower(), curr.lower()).ratio()
        if ratio >= 0.85:
            return "minor_edit"
        if ratio <= 0.35:
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
    nodes = []
    edges = []

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


def combine_risk(payload_risk: Optional[float], trust_degradation: List[Dict[str, Any]]) -> float:
    payload_component = float(payload_risk or 0.0)
    trust_component = trust_degradation[-1]["cumulative_loss"] if trust_degradation else 0.0
    return round(min(1.0, (payload_component * 0.70) + (trust_component * 0.30)), 3)


def load_trace(trace_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
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


def create_or_extend_trace(
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
    payload_hash = sha256_text(payload)
    normalized_channel = (channel or "unknown").strip().lower()

    prev_trace = load_trace(previous_trace_id, tenant_id) if previous_trace_id else None
    prev_journey = prev_trace["journey"] if prev_trace else []
    prev_current_hash = prev_trace["current_hash"] if prev_trace else None
    prev_preview = prev_journey[-1].get("payload_preview") if prev_journey else None

    trust_result = calculate_dynamic_trust(normalized_channel, context, tenant_id)
    transform = detect_transform(prev_current_hash, prev_preview, payload, normalized_channel)

    step = {
        "channel": normalized_channel,
        "timestamp": now,
        "hash": payload_hash,
        "payload_preview": preview_payload(payload),
        "transform": transform,
        "objective": objective,
        "risk_score": risk_score if risk_score is not None else 0.0,
        "decision": decision,
        "trust_score": trust_result["trust_score"],
        "trust_level": trust_result["trust_level"],
        "metadata": metadata,
    }

    journey = prev_journey + [step]
    trust_degradation = calculate_trust_degradation(journey)
    propagation_graph = build_propagation_graph(journey)
    final_risk = combine_risk(risk_score, trust_degradation)

    if decision == "BLOCKED":
        detection_layer = normalized_channel
    elif prev_trace and prev_trace.get("detection_layer"):
        detection_layer = prev_trace["detection_layer"]
    else:
        detection_layer = None

    trace_id = generate_id("trace")

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

    event_id = generate_id("event")
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
            preview_payload(payload),
            float(risk_score or 0.0),
            float(trust_result["trust_score"]),
            decision,
            json_dumps(metadata),
            now,
        ),
    )
    conn.commit()
    conn.close()

    update_channel_reputation(tenant_id, normalized_channel, float(trust_result["trust_score"]), decision)

    explanation = generate_decision_explanation(
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


def record_scan_trace_safe(
    tenant_id: str,
    payload: str,
    channel: str,
    objective: str,
    decision: str,
    risk_score: float,
    taxonomy_class: Optional[str] = None,
    previous_trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Safe helper for integrating Phase 2 into /v1/scan.
    It never breaks the existing scan path; if tracing fails, scan still works.
    """
    try:
        extra_metadata = metadata or {}
        extra_metadata.update({
            "taxonomy_class": taxonomy_class,
            "session_id": session_id,
            "recorded_from": "v1_scan",
        })

        trace = create_or_extend_trace(
            tenant_id=tenant_id,
            payload=payload,
            channel=channel,
            objective=objective,
            previous_trace_id=previous_trace_id,
            risk_score=risk_score,
            decision=decision,
            metadata=extra_metadata,
            context={},
        )
        return trace["trace_id"]
    except Exception:
        return None


# ── Explainability ────────────────────────────────────────────────────────────

def classify_risk(risk_score: float) -> str:
    if risk_score >= 0.80:
        return "critical"
    if risk_score >= 0.50:
        return "high"
    if risk_score >= 0.25:
        return "medium"
    return "low"


def generate_decision_explanation(
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
    risk_level = classify_risk(float(risk_score or 0.0))

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
        reasoning.append("Final decision is BLOCKED because model/policy/trace risk is not acceptable.")
        confidence = min(0.99, max(0.80, risk_score))
    elif normalized_decision == "REVIEW":
        reasoning.append("Final decision is REVIEW because moderate risk requires human or policy review.")
        confidence = 0.70
    else:
        reasoning.append("Final decision is ALLOWED because risk and trust checks passed.")
        confidence = max(0.50, 1.0 - risk_score)

    if policy_action:
        reasoning.append(f"Policy engine action was {policy_action}.")

    explanation_id = generate_id("explain")

    result = {
        "explanation_id": explanation_id,
        "trace_id": trace_id,
        "tenant_id": tenant_id,
        "decision": normalized_decision,
        "confidence": round(float(confidence), 3),
        "reasoning": reasoning,
        "risk_factors": risk_factors,
        "triggered_layers": infer_triggered_layers(channel, taxonomy_class, trust_degradation),
        "matched_signatures": infer_matched_signatures(taxonomy_class, risk_score),
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


def infer_triggered_layers(channel: str, taxonomy_class: Optional[str], trust_degradation: List[Dict[str, Any]]) -> List[str]:
    layers = ["pipeline"]
    if taxonomy_class and taxonomy_class != "T0":
        layers.append("taxonomy")
    if channel:
        layers.append(f"channel:{channel}")
    if trust_degradation and trust_degradation[-1]["cumulative_loss"] >= 0.50:
        layers.append("cross_channel_trace")
    return layers


def infer_matched_signatures(taxonomy_class: Optional[str], risk_score: float) -> List[str]:
    signatures = []
    if taxonomy_class:
        signatures.append(taxonomy_class)
    if risk_score >= 0.80:
        signatures.append("high_risk_prompt_or_policy_threshold")
    return signatures


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/v1/phase2/health")
def phase2_health() -> Dict[str, Any]:
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


@router.post("/v1/trace/payload")
def trace_payload(body: TracePayloadRequest) -> Dict[str, Any]:
    return create_or_extend_trace(
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


@router.get("/v1/trace/{trace_id}")
def get_trace(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)) -> Dict[str, Any]:
    trace = load_trace(trace_id, tenant_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@router.post("/v1/trace/{trace_id}/event")
def add_trace_event(trace_id: str, body: TraceEventRequest, tenant_id: str = Query(DEFAULT_TENANT_ID)) -> Dict[str, Any]:
    existing = load_trace(trace_id, tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trace not found")

    return create_or_extend_trace(
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


@router.get("/v1/trace/{trace_id}/supply-chain")
def get_supply_chain(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)) -> Dict[str, Any]:
    trace = load_trace(trace_id, tenant_id)
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


@router.post("/v1/trust/score")
def trust_score(body: TrustScoreRequest) -> Dict[str, Any]:
    return calculate_dynamic_trust(body.channel, body.context, body.tenant_id)


@router.get("/v1/trust/channels")
def channel_trust(admin_key: str = Query(...), tenant_id: str = Query(DEFAULT_TENANT_ID)) -> Dict[str, Any]:
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


@router.post("/v1/explain/decision")
def explain_decision(body: ExplainDecisionRequest) -> Dict[str, Any]:
    trace = load_trace(body.trace_id, body.tenant_id) if body.trace_id else None
    trust_degradation = trace["trust_degradation"] if trace else []

    return generate_decision_explanation(
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


@router.get("/v1/explain/{trace_id}")
def explain_trace(trace_id: str, tenant_id: str = Query(DEFAULT_TENANT_ID)) -> Dict[str, Any]:
    trace = load_trace(trace_id, tenant_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    last_step = trace["journey"][-1] if trace["journey"] else {}

    return generate_decision_explanation(
        tenant_id=tenant_id,
        decision=last_step.get("decision") or "TRACE_RECORDED",
        risk_score=float(last_step.get("risk_score") or trace["final_risk_score"] or 0.0),
        channel=last_step.get("channel", "unknown"),
        objective=last_step.get("objective", "general"),
        trace_id=trace_id,
        taxonomy_class=last_step.get("metadata", {}).get("taxonomy_class"),
        trust_degradation=trace["trust_degradation"],
    )
