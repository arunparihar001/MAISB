# migrate_quota.py
# Save at: E:\projects\maisb-monorepo\maisb\llm_proxy\migrate_quota.py
#
# HOW TO RUN:
#   python migrate_quota.py
#
# Purpose:
#   Ensures api_keys has scan_count for free-tier quota enforcement.

import sqlite3
import datetime

DB_PATH = "usage.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        key        TEXT PRIMARY KEY,
        plan       TEXT DEFAULT 'free',
        scan_count INTEGER DEFAULT 0,
        created    TEXT
    )
""")

columns = [row[1] for row in c.execute("PRAGMA table_info(api_keys)").fetchall()]

if "plan" not in columns:
    c.execute("ALTER TABLE api_keys ADD COLUMN plan TEXT DEFAULT 'free'")
    print("✅ Added plan column to api_keys")
else:
    print("✅ plan column already exists")

if "scan_count" not in columns:
    c.execute("ALTER TABLE api_keys ADD COLUMN scan_count INTEGER DEFAULT 0")
    print("✅ Added scan_count column to api_keys")
else:
    print("✅ scan_count column already exists")

if "created" not in columns:
    c.execute("ALTER TABLE api_keys ADD COLUMN created TEXT")
    print("✅ Added created column to api_keys")
else:
    print("✅ created column already exists")

c.execute(
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

print("✅ Quota migration complete")