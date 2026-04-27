import sqlite3

DB_PATH = "usage.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

columns = [row[1] for row in c.execute("PRAGMA table_info(api_keys)").fetchall()]

if "scan_count" not in columns:
    c.execute("ALTER TABLE api_keys ADD COLUMN scan_count INTEGER DEFAULT 0")
    print("✅ Added scan_count column to api_keys")
else:
    print("✅ scan_count column already exists")

conn.commit()
conn.close()

print("✅ Migration complete")