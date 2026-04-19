# scan_api.py
# Save this file at: E:\projects\maisb-monorepo\maisb\llm_proxy\scan_api.py
#
# HOW TO RUN:
#   uvicorn scan_api:app --host 127.0.0.1 --port 8001 --reload
#
# FOR RAILWAY DEPLOYMENT, set start command to:
#   uvicorn scan_api:app --host 0.0.0.0 --port $PORT

import sqlite3
import datetime
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the classify function that already exists in main.py
from main import classify_payload

app = FastAPI(title="MAISB Scan API", version="1.0.0")

DB_PATH = "usage.db"

# ─────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# Helper: validate API key against database
# ─────────────────────────────────────────────────────────────

def validate_api_key(api_key: str) -> dict:
    """
    Returns the plan dict if key is valid, raises 401 otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT key, plan FROM api_keys WHERE key = ?", (api_key,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"key": row[0], "plan": row[1]}


# ─────────────────────────────────────────────────────────────
# Helper: log scan to database
# ─────────────────────────────────────────────────────────────

def log_scan(api_key: str, channel: str, decision: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scans VALUES (?, ?, ?, ?)",
        (api_key, datetime.datetime.utcnow().isoformat(), channel, decision)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# Helper: map decision to human-readable action
# ─────────────────────────────────────────────────────────────

RECOMMENDED_ACTIONS = {
    "BLOCKED": "Block: payload identified as prompt injection. Do not pass to LLM.",
    "ALLOWED": "Allow: payload appears clean. Safe to pass to LLM.",
    "REVIEW":  "Review: borderline payload. Inspect before passing to LLM.",
}

def get_recommended_action(decision: str) -> str:
    return RECOMMENDED_ACTIONS.get(decision, "Unknown decision — treat as blocked.")


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    # 1. Validate API key
    validate_api_key(req.api_key)

    # 2. Run the classifier (already built in main.py)
    start_ms = time.time()
    result = classify_payload(
        payload=req.payload,
        channel=req.channel,
        objective=req.objective
    )
    elapsed_ms = int((time.time() - start_ms) * 1000)

    decision       = result.get("decision", "BLOCKED")
    risk_score     = float(result.get("risk_score", 0.0))
    taxonomy_class = result.get("taxonomy_class", "T0")

    # 3. Log to database
    log_scan(req.api_key, req.channel, decision)

    # 4. Return response
    return ScanResponse(
        decision=decision,
        risk_score=risk_score,
        taxonomy_class=taxonomy_class,
        recommended_action=get_recommended_action(decision),
        processing_ms=elapsed_ms,
    )


@app.get("/usage")
def usage(api_key: str):
    # Validate key
    key_info = validate_api_key(api_key)

    # Count scans
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT COUNT(*) FROM scans WHERE api_key = ?", (api_key,)
    ).fetchone()
    conn.close()

    return {
        "api_key": api_key,
        "scan_count": row[0],
        "plan": key_info["plan"]
    }
