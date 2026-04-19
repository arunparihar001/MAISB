# setup_db.py
# Save at: E:\projects\maisb-monorepo\maisb\llm_proxy\setup_db.py
#
# HOW TO RUN (run this ONCE before starting scan_api.py):
#   python setup_db.py
#
# This creates usage.db with the two tables and inserts a test API key.

import sqlite3
import datetime

DB_PATH = "usage.db"

conn = sqlite3.connect(DB_PATH)

# Table 1: api_keys  — stores all valid keys and their plan tier
conn.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        key     TEXT PRIMARY KEY,
        plan    TEXT,
        created TEXT
    )
""")

# Table 2: scans  — one row per scan call (usage log)
conn.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        api_key  TEXT,
        ts       TEXT,
        channel  TEXT,
        decision TEXT
    )
""")

# Insert the test key (free tier)
conn.execute(
    "INSERT OR IGNORE INTO api_keys VALUES (?, ?, ?)",
    ("maisb_live_test123", "free", datetime.datetime.utcnow().isoformat())
)

conn.commit()
conn.close()

print("✅  usage.db created with tables: api_keys, scans")
print("✅  Test key inserted: maisb_live_test123  (plan: free)")
print()
print("Next step: uvicorn scan_api:app --host 127.0.0.1 --port 8001 --reload")
