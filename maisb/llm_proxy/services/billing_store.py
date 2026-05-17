import datetime as dt
import json
import os
import sqlite3
from typing import Any, Dict, Optional

DB_PATH = os.environ.get("DB_PATH", "usage.db")


def _utcnow_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_billing_store() -> None:
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS paddle_webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            payload_json TEXT,
            received_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS paddle_subscriptions (
            email TEXT PRIMARY KEY,
            plan TEXT,
            status TEXT,
            customer_id TEXT,
            subscription_id TEXT,
            price_id TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def store_webhook_event(event_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO paddle_webhook_events(event_id,event_type,payload_json,received_at) VALUES (?,?,?,?)",
            (event_id, event_type, json.dumps(payload, separators=(",", ":")), _utcnow_iso()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def upsert_subscription(email: str, plan: str, status: str, customer_id: str, subscription_id: str, price_id: str) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO paddle_subscriptions(email,plan,status,customer_id,subscription_id,price_id,updated_at)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            plan=excluded.plan,
            status=excluded.status,
            customer_id=excluded.customer_id,
            subscription_id=excluded.subscription_id,
            price_id=excluded.price_id,
            updated_at=excluded.updated_at
        """,
        (email, plan, status, customer_id, subscription_id, price_id, _utcnow_iso()),
    )
    conn.execute("UPDATE api_keys SET plan=? WHERE lower(email)=lower(?)", (plan, email))
    conn.commit()
    conn.close()


def get_billing_status(email: Optional[str], api_key: Optional[str]) -> Dict[str, Any]:
    conn = _conn()
    resolved_email = email
    if not resolved_email and api_key:
        row = conn.execute("SELECT email FROM api_keys WHERE key=?", (api_key,)).fetchone()
        resolved_email = row["email"] if row else None
    sub = None
    if resolved_email:
        sub = conn.execute("SELECT * FROM paddle_subscriptions WHERE lower(email)=lower(?)", (resolved_email,)).fetchone()
    conn.close()
    return {
        "email": resolved_email,
        "status": sub["status"] if sub else "inactive",
        "plan": sub["plan"] if sub else "free",
        "price_id": sub["price_id"] if sub else None,
        "provider": "paddle",
    }
