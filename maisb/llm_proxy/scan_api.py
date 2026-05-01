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
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import classify_payload, CompleteIn


# ── constants ─────────────────────────────────────────────────

DB_PATH = "usage.db"
FREE_TIER_MONTHLY_LIMIT = 1000


# ── database setup / migrations ───────────────────────────────

def get_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,)
    ).fetchone()
    return row is not None


def migrate_api_keys_table(conn: sqlite3.Connection):
    """
    Ensures api_keys supports free-tier quota enforcement.
    Keeps old keys and adds scan_count if missing.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key        TEXT PRIMARY KEY,
            plan       TEXT DEFAULT 'free',
            scan_count INTEGER DEFAULT 0,
            created    TEXT
        )
    """)

    columns = get_columns(conn, "api_keys")

    if "plan" not in columns:
        conn.execute("ALTER TABLE api_keys ADD COLUMN plan TEXT DEFAULT 'free'")

    if "scan_count" not in columns:
        conn.execute("ALTER TABLE api_keys ADD COLUMN scan_count INTEGER DEFAULT 0")

    if "created" not in columns:
        conn.execute("ALTER TABLE api_keys ADD COLUMN created TEXT")


def migrate_scans_table(conn: sqlite3.Connection):
    """
    Ensures scans table has NO payload column.

    Final schema:
        id
        api_key
        decision
        risk_score
        taxonomy_class
        ts

    If an old scans table exists, this migrates safe metadata only.
    It intentionally never copies a payload column.
    """
    if not table_exists(conn, "scans"):
        conn.execute("""
            CREATE TABLE scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT,
                decision TEXT,
                risk_score REAL,
                taxonomy_class TEXT,
                ts TEXT
            )
        """)
        return

    columns = get_columns(conn, "scans")

    correct_schema = columns == [
        "id",
        "api_key",
        "decision",
        "risk_score",
        "taxonomy_class",
        "ts",
    ]

    if correct_schema:
        return

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            decision TEXT,
            risk_score REAL,
            taxonomy_class TEXT,
            ts TEXT
        )
    """)

    # Old schema variants supported:
    # 1. api_key, ts, channel, decision
    # 2. api_key, payload, decision, risk_score
    # 3. api_key, decision, risk_score, taxonomy_class, ts
    #
    # Important: payload is NEVER copied.
    if "risk_score" in columns and "taxonomy_class" in columns and "ts" in columns:
        conn.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, risk_score, taxonomy_class, ts
            FROM scans
        """)
    elif "risk_score" in columns and "ts" in columns:
        conn.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, risk_score, '', ts
            FROM scans
        """)
    elif "ts" in columns:
        conn.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, 0.0, '', ts
            FROM scans
        """)
    else:
        conn.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, COALESCE(risk_score, 0.0), '', ?
            FROM scans
        """, (datetime.datetime.utcnow().isoformat(),))

    conn.execute("DROP TABLE scans")
    conn.execute("ALTER TABLE scans_new RENAME TO scans")


def init_db():
    conn = sqlite3.connect(DB_PATH)

    migrate_api_keys_table(conn)
    migrate_scans_table(conn)

    conn.execute(
        """
        INSERT OR IGNORE INTO api_keys (key, plan, scan_count, created)
        VALUES (?, ?, ?, ?)
        """,
        (
            "maisb_live_test123",
            "free",
            0,
            datetime.datetime.utcnow().isoformat()
        )
    )

    conn.commit()
    conn.close()


init_db()

app = FastAPI(title="MAISB Scan API", version="1.0.0")

# Dashboard / browser CORS support
# This allows your hosted dashboard and local dev servers to call the Railway API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://maisb-dashboard.vercel.app",
        "https://maisb-dashboard-static.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "plan": row[1] or "free",
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


def log_scan(api_key: str, decision: str, risk_score: float, taxonomy_class: str):
    """
    Metadata-only scan log.

    IMPORTANT:
    This function does NOT store req.payload.
    Payload is processed in memory only by classify_payload().
    """
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO scans (api_key, decision, risk_score, taxonomy_class, ts)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            api_key,
            decision,
            risk_score,
            taxonomy_class,
            datetime.datetime.utcnow().isoformat()
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
    # Payload is used here in memory only.
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

    # 3. Log metadata only. No payload is saved.
    log_scan(req.api_key, decision, risk_score, taxonomy_class)

    # 4. Increment usage after successful classification
    increment_scan_count(req.api_key)

    # 5. Return response
    return ScanResponse(
        decision=decision,
        risk_score=risk_score,
        taxonomy_class=taxonomy_class,
        recommended_action=RECOMMENDED_ACTIONS[decision],
        processing_ms=elapsed_ms,
    )


@app.post("/admin/reset-monthly-counts", include_in_schema=False)
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
async def usage(api_key: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT plan, scan_count FROM api_keys WHERE key = ?",
        (api_key,)
    )

    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")

    plan, scan_count = row

    return {
        "plan": plan,
        "scan_count": scan_count
    }


@app.get("/admin/scans-schema", include_in_schema=False)
def scans_schema(admin_key: str):
    """
    Optional debug endpoint.
    Use this to verify Railway DB schema.
    Remove later if you want.
    """
    if admin_key != os.environ.get("ADMIN_KEY", "change_me"):
        raise HTTPException(status_code=403, detail="Forbidden")

    conn = sqlite3.connect(DB_PATH)
    columns = get_columns(conn, "scans")
    conn.close()

    return {
        "table": "scans",
        "columns": columns,
        "payload_retention": "disabled" if "payload" not in columns else "payload_column_present"
    }