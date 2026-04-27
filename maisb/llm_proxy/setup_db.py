# setup_db.py
# Save at: E:\projects\maisb-monorepo\maisb\llm_proxy\setup_db.py
#
# HOW TO RUN:
#   python setup_db.py
#
# This creates usage.db with:
#   1. api_keys table for API key auth and free-tier quota
#   2. scans table for metadata-only scan logging
#
# No payloads are stored in SQLite.

import sqlite3
import datetime

DB_PATH = "usage.db"


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
    Final scans schema:
        id
        api_key
        decision
        risk_score
        taxonomy_class
        ts

    No payload column.
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

    # Copy only safe metadata. Never copy payload.
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

print("✅ usage.db ready")
print("✅ api_keys table ready with scan_count quota support")
print("✅ scans table ready with metadata-only no-payload schema")
print("✅ Test key inserted: maisb_live_test123  (plan: free)")
print()
print("Next step:")
print("  uvicorn scan_api:app --host 127.0.0.1 --port 8001 --reload")