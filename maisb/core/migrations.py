"""
Safe Phase 1 database migrations.

SQLAlchemy create_all() creates new tables but does not alter existing ones.
This module adds the Phase 1 completion columns safely when your local SQLite
DB already exists from the first integration.
"""
from sqlalchemy import inspect, text
from maisb.core.database import engine


def _columns(table_name: str) -> set[str]:
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def run_phase1_migrations():
    api_key_cols = _columns("api_keys")
    statements = []

    if "role" not in api_key_cols:
        statements.append("ALTER TABLE api_keys ADD COLUMN role VARCHAR(50) DEFAULT 'viewer' NOT NULL")
    if "monthly_limit" not in api_key_cols:
        statements.append("ALTER TABLE api_keys ADD COLUMN monthly_limit INTEGER")
    if "usage_count" not in api_key_cols:
        statements.append("ALTER TABLE api_keys ADD COLUMN usage_count INTEGER DEFAULT 0 NOT NULL")
    if "usage_reset_at" not in api_key_cols:
        statements.append("ALTER TABLE api_keys ADD COLUMN usage_reset_at DATETIME")

    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
