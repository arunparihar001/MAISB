# migrate_no_payload.py
# Save at: E:\projects\maisb-monorepo\maisb\llm_proxy\migrate_no_payload.py
#
# HOW TO RUN:
#   python migrate_no_payload.py
#
# Purpose:
#   Migrates the scans table to metadata-only logging.
#   It removes any payload column by creating a clean scans table
#   and copying only safe metadata.

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


conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

if not table_exists(conn, "scans"):
    c.execute("""
        CREATE TABLE scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            decision TEXT,
            risk_score REAL,
            taxonomy_class TEXT,
            ts TEXT
        )
    """)
    print("✅ Created scans table with no-payload schema")
else:
    old_columns = get_columns(conn, "scans")
    print("Old scans columns:", old_columns)

    c.execute("""
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
    if "risk_score" in old_columns and "taxonomy_class" in old_columns and "ts" in old_columns:
        c.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, risk_score, taxonomy_class, ts
            FROM scans
        """)
    elif "risk_score" in old_columns and "ts" in old_columns:
        c.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, risk_score, '', ts
            FROM scans
        """)
    elif "ts" in old_columns:
        c.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, 0.0, '', ts
            FROM scans
        """)
    else:
        c.execute("""
            INSERT INTO scans_new (api_key, decision, risk_score, taxonomy_class, ts)
            SELECT api_key, decision, COALESCE(risk_score, 0.0), '', ?
            FROM scans
        """, (datetime.datetime.utcnow().isoformat(),))

    c.execute("DROP TABLE scans")
    c.execute("ALTER TABLE scans_new RENAME TO scans")

conn.commit()

new_columns = get_columns(conn, "scans")
conn.close()

print("New scans columns:", new_columns)

if "payload" in new_columns:
    print("❌ ERROR: payload column still exists")
else:
    print("✅ Migration complete")
    print("✅ Payload column removed")
    print("✅ scans table now stores metadata only")