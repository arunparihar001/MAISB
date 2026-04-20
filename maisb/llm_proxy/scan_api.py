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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import classify_payload, CompleteIn

# ── constants ─────────────────────────────────────────────────
DB_PATH = "usage.db"

# ── auto-create DB on every startup (safe on Railway) ─────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS api_keys
                    (key TEXT PRIMARY KEY, plan TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scans
                    (api_key TEXT, ts TEXT, channel TEXT, decision TEXT)""")
    conn.execute("INSERT OR IGNORE INTO api_keys VALUES ('maisb_live_test123','free','2026-04-20')")
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
    "REVIEW":  "Review: partial attack signal present. Inspect before passing to LLM.",
    "ALLOWED": "Allow: payload appears clean and aligned with objective.",
}

# ── db helpers ────────────────────────────────────────────────

def validate_api_key(api_key: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT key, plan FROM api_keys WHERE key = ?", (api_key,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"key": row[0], "plan": row[1]}

def log_scan(api_key: str, channel: str, decision: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scans VALUES (?, ?, ?, ?)",
        (api_key, datetime.datetime.utcnow().isoformat(), channel, decision)
    )
    conn.commit()
    conn.close()

# ── endpoints ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    validate_api_key(req.api_key)

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
    log_scan(req.api_key, req.channel, decision)

    return ScanResponse(
        decision=decision,
        risk_score=risk_score,
        taxonomy_class=taxonomy_class,
        recommended_action=RECOMMENDED_ACTIONS[decision],
        processing_ms=elapsed_ms,
    )

@app.get("/usage")
def usage(api_key: str):
    key_info = validate_api_key(api_key)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT COUNT(*) FROM scans WHERE api_key = ?", (api_key,)
    ).fetchone()
    conn.close()
    return {"api_key": api_key, "scan_count": row[0], "plan": key_info["plan"]}
