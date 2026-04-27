# scan_api.py
# Save at: E:\projects\maisb-monorepo\maisb\llm_proxy\scan_api.py
#
# HOW TO RUN locally:
#   uvicorn scan_api:app --host 127.0.0.1 --port 8001 --reload
#
# Railway start command:
#   uvicorn scan_api:app --host 0.0.0.0 --port $PORT

import sqlite3
import datetime
import time
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import classify_payload, CompleteIn

# ── constants ─────────────────────────────────────────────────

DB_PATH = "usage.db"
FREE_TIER_MONTHLY_LIMIT = 1000

# ── auto-create DB on every startup safe on Railway ────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key        TEXT PRIMARY KEY,
            plan       TEXT DEFAULT 'free',
            scan_count INTEGER DEFAULT 0,
            created    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            api_key  TEXT,
            ts       TEXT,
            channel  TEXT,
            decision TEXT
        )
    """)

    conn.execute(
        """
        INSERT OR IGNORE INTO api_keys (key, plan, scan_count, created)
        VALUES (?, ?, ?, ?)
        """,
        (
            "maisb_live_test123",
            "free",
            0,
            "2026-04-20"
        )
    )

    # Migration safety: add scan_count if an old api_keys table already exists
    columns = [row[1] for row in conn.execute("PRAGMA table_info(api_keys)").fetchall()]
    if "scan_count" not in columns:
        conn.execute("ALTER TABLE api_keys ADD COLUMN scan_count INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


init_db()

app = FastAPI(title="MAISB Scan API", version="1.0.0")

# ── models ────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    payload: str
    channel: str
    objective: str
    api_key: str


class ScanResponse(BaseModel):
    decision: str
    risk_score: float
    taxonomy_class: str
    recommended_action: str
    processing_ms: int


# ── decision logic ────────────────────────────────────────────

def derive_decision(analysis) -> tuple[str, float, str]:
    s = analysis.attack_score

    if analysis.high_confidence_attack:
        decision = "BLOCKED"
    elif s > 0:
        decision = "REVIEW"
    else:
        decision = "ALLOWED"

    if s >= 6:
        risk_score = min(0.90 + (s - 6) * 0.02, 0.99)
    elif s >= 3:
        risk_score = 0.50 + (s - 3) * 0.13
    elif s >= 1:
        risk_score = 0.20 + (s - 1) * 0.15
    else:
        risk_score = 0.00

    reasons = " ".join(analysis.attack_reasons).lower()

    if not reasons or s == 0:
        taxonomy = "T0"
    elif analysis.hidden_instruction:
        taxonomy = "T7"
    elif "instruction-override" in reasons and len(analysis.attack_reasons) > 1:
        taxonomy = "T8"
    elif "instruction-override" in reasons:
        taxonomy = "T1"
    elif "confirmation-bypass" in reasons:
        taxonomy = "T2"
    elif "exfiltration" in reasons or "export" in reasons:
        taxonomy = "T3"
    elif "bulk-action" in reasons:
        taxonomy = "T4"
    elif "suspicious destination" in reasons:
        taxonomy = "T5"
    elif "malicious maisb" in reasons:
        taxonomy = "T6"
    else:
        taxonomy = "T8"

    return decision, round(risk_score, 2), taxonomy


RECOMMENDED_ACTIONS = {
    "BLOCKED": "Block: prompt injection detected. Do not pass this payload to the LLM.",
    "REVIEW": "Review: partial attack signal present. Inspect before passing to LLM.",
    "ALLOWED": "Allow: payload appears clean and aligned with objective.",
}

# ── db helpers ────────────────────────────────────────────────

def get_api_key_info(api_key: str) -> dict:
    conn = sqlite3.connect(DB_PATH)

    row = conn.execute(
        """
        SELECT key, plan, scan_count
        FROM api_keys
        WHERE key = ?
        """,
        (api_key,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "key": row[0],
        "plan": row[1],
        "scan_count": row[2] or 0,
    }


def enforce_quota(api_key: str) -> dict:
    key_info = get_api_key_info(api_key)

    if (
        key_info["plan"] == "free"
        and key_info["scan_count"] >= FREE_TIER_MONTHLY_LIMIT
    ):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"Free tier limit of {FREE_TIER_MONTHLY_LIMIT} scans/month reached.",
                "upgrade_url": "https://maisb.ai/pricing"
            }
        )

    return key_info


def increment_scan_count(api_key: str):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE api_keys
        SET scan_count = scan_count + 1
        WHERE key = ?
        """,
        (api_key,)
    )

    conn.commit()
    conn.close()


def log_scan(api_key: str, channel: str, decision: str):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO scans (api_key, ts, channel, decision)
        VALUES (?, ?, ?, ?)
        """,
        (
            api_key,
            datetime.datetime.utcnow().isoformat(),
            channel,
            decision
        )
    )

    conn.commit()
    conn.close()


# ── endpoints ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    # 1. Validate API key and enforce free-tier quota
    enforce_quota(req.api_key)

    # 2. Run scan/classification
    complete_req = CompleteIn(
        content=req.payload,
        provenance=req.channel,
        objective=req.objective,
        defense_profile="D5",
    )

    start = time.time()
    analysis = classify_payload(complete_req)
    elapsed_ms = int((time.time() - start) * 1000)

    decision, risk_score, taxonomy_class = derive_decision(analysis)

    # 3. Log scan and increment usage only after successful classification
    log_scan(req.api_key, req.channel, decision)
    increment_scan_count(req.api_key)

    # 4. Return response
    return ScanResponse(
        decision=decision,
        risk_score=risk_score,
        taxonomy_class=taxonomy_class,
        recommended_action=RECOMMENDED_ACTIONS[decision],
        processing_ms=elapsed_ms,
    )


@app.post("/admin/reset-monthly-counts")
def reset_monthly_counts(admin_key: str):
    if admin_key != os.environ.get("ADMIN_KEY", "change_me"):
        raise HTTPException(status_code=403, detail="Forbidden")

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE api_keys
        SET scan_count = 0
        WHERE plan = 'free'
        """
    )

    conn.commit()
    conn.close()

    return {"reset": True}


@app.get("/usage")
def usage(api_key: str):
    key_info = get_api_key_info(api_key)

    return {
        "api_key": api_key,
        "scan_count": key_info["scan_count"],
        "plan": key_info["plan"],
        "free_tier_limit": FREE_TIER_MONTHLY_LIMIT,
        "remaining": (
            max(FREE_TIER_MONTHLY_LIMIT - key_info["scan_count"], 0)
            if key_info["plan"] == "free"
            else None
        )
    }