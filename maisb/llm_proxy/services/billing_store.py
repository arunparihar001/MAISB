from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from typing import Any, Optional

DB_PATH = os.environ.get("DB_PATH", "usage.db")


def _utcnow() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_billing_store() -> None:
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paddle_webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            payload_json TEXT,
            received_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paddle_subscriptions (
            email TEXT PRIMARY KEY,
            plan TEXT,
            status TEXT,
            customer_id TEXT,
            subscription_id TEXT,
            price_id TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_webhook_event(event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO paddle_webhook_events(event_id,event_type,payload_json,received_at) VALUES (?,?,?,?)",
            (event_id, event_type, json.dumps(payload, separators=(",", ":")), _utcnow()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def upsert_subscription(email: str, plan: str, status: str, customer_id: str = "", subscription_id: str = "", price_id: str = "") -> None:
    conn = _conn()
    conn.execute("""
        INSERT INTO paddle_subscriptions(email,plan,status,customer_id,subscription_id,price_id,updated_at)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            plan=excluded.plan,
            status=excluded.status,
            customer_id=COALESCE(NULLIF(excluded.customer_id,''), paddle_subscriptions.customer_id),
            subscription_id=COALESCE(NULLIF(excluded.subscription_id,''), paddle_subscriptions.subscription_id),
            price_id=COALESCE(NULLIF(excluded.price_id,''), paddle_subscriptions.price_id),
            updated_at=excluded.updated_at
    """, (email, plan, status, customer_id, subscription_id, price_id, _utcnow()))
    try:
        conn.execute("UPDATE api_keys SET plan=? WHERE lower(email)=lower(?)", (plan, email))
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def get_billing_status(email: Optional[str] = None, api_key: Optional[str] = None) -> dict[str, Any]:
    conn = _conn()
    resolved_email = email
    if not resolved_email and api_key:
        try:
            row = conn.execute("SELECT email FROM api_keys WHERE key=?", (api_key,)).fetchone()
            resolved_email = row["email"] if row else None
        except sqlite3.OperationalError:
            resolved_email = None
    row = None
    if resolved_email:
        row = conn.execute("SELECT * FROM paddle_subscriptions WHERE lower(email)=lower(?)", (resolved_email,)).fetchone()
    conn.close()
    return {
        "email": resolved_email,
        "provider": "paddle",
        "plan": row["plan"] if row else "free",
        "status": row["status"] if row else "inactive",
        "price_id": row["price_id"] if row else None,
        "updated_at": row["updated_at"] if row else None,
    }
