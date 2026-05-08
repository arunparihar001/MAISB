# api/scan_api.py
# Production Scan API — FastAPI
#
# HOW TO RUN locally:
#   uvicorn api.scan_api:app --host 127.0.0.1 --port 8001 --reload
#
# Railway start command:
#   uvicorn api.scan_api:app --host 0.0.0.0 --port $PORT

import sqlite3
import datetime
import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.models import ScanRequest as PipelineScanRequest
from pipeline.runner import run_pipeline


DB_PATH = os.environ.get("DB_PATH", "usage.db")
FREE_TIER_MONTHLY_LIMIT = 1000
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")


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

    # ── Schema migration: add any columns that older DB versions are missing ──
    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(scans)").fetchall()
    }
    migrations = {
        "channel":        "ALTER TABLE scans ADD COLUMN channel TEXT",
        "objective":      "ALTER TABLE scans ADD COLUMN objective TEXT",
        "taxonomy_class": "ALTER TABLE scans ADD COLUMN taxonomy_class TEXT",
        "processing_ms":  "ALTER TABLE scans ADD COLUMN processing_ms INTEGER",
    }
    for col, sql in migrations.items():
        if col not in existing_cols:
            conn.execute(sql)

    # Seed test key
    conn.execute("""
        INSERT OR IGNORE INTO api_keys (key, plan, scan_count, created)
        VALUES (?, 'free', 0, ?)
    """, ("maisb_live_test123", datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

init_db()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="MAISB Scan API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://maisb-dashboard-static.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/response models ───────────────────────────────────────────────────

class ScanRequestBody(BaseModel):
    payload:    str
    channel:    str  = "unknown"
    objective:  str  = "general"
    api_key:    str
    session_id: str  = None


class ScanResponseBody(BaseModel):
    decision:           str
    risk_score:         float
    taxonomy_class:     str
    recommended_action: str
    processing_ms:      int


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_key_info(api_key: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT key, plan, scan_count FROM api_keys WHERE key = ?",
        (api_key,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"key": row[0], "plan": row[1] or "free", "scan_count": row[2] or 0}


def enforce_quota(api_key: str):
    info = get_key_info(api_key)
    if info["plan"] == "free" and info["scan_count"] >= FREE_TIER_MONTHLY_LIMIT:
        raise HTTPException(status_code=429, detail={
            "error": "quota_exceeded",
            "message": f"Free tier limit of {FREE_TIER_MONTHLY_LIMIT} scans/month reached.",
            "upgrade_url": "https://maisb.ai/pricing",
        })
    return info


def log_scan(api_key, decision, risk_score, taxonomy, channel, objective, ms):
    """Metadata-only log — NO payload stored."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO scans
            (api_key, decision, risk_score, taxonomy_class, channel, objective, processing_ms, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (api_key, decision, risk_score, taxonomy, channel, objective, ms,
          datetime.datetime.utcnow().isoformat()))
    conn.execute(
        "UPDATE api_keys SET scan_count = scan_count + 1 WHERE key = ?",
        (api_key,)
    )
    conn.commit()
    conn.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/v1/scan", response_model=ScanResponseBody)
def scan(body: ScanRequestBody):
    # 1. Validate key + quota
    enforce_quota(body.api_key)

    # 2. Build PipelineScanRequest
    pipeline_request = PipelineScanRequest(
        payload    = body.payload,
        channel    = body.channel,
        objective  = body.objective,
        api_key    = body.api_key,
        session_id = body.session_id,
    )

    # 3. Run the full 7-layer pipeline
    result = run_pipeline(pipeline_request)

    # 4. Log metadata (no payload)
    log_scan(
        body.api_key,
        result.decision,
        result.risk_score,
        result.taxonomy_class,
        body.channel,
        body.objective,
        result.processing_ms,
    )

    return ScanResponseBody(
        decision           = result.decision,
        risk_score         = result.risk_score,
        taxonomy_class     = result.taxonomy_class,
        recommended_action = result.recommended_action,
        processing_ms      = result.processing_ms,
    )


@app.get("/usage")
def usage(api_key: str):
    info = get_key_info(api_key)
    return {"plan": info["plan"], "scan_count": info["scan_count"]}


@app.post("/admin/reset-monthly-counts", include_in_schema=False)
def reset_monthly_counts(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE api_keys SET scan_count = 0 WHERE plan = 'free'")
    conn.commit()
    conn.close()
    return {"reset": True}


@app.get("/admin/scans-schema", include_in_schema=False)
def scans_schema(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = sqlite3.connect(DB_PATH)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(scans)").fetchall()]
    conn.close()
    return {
        "table": "scans",
        "columns": cols,
        "payload_retention": "disabled" if "payload" not in cols else "WARNING: payload present",
    }