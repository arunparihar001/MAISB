"""Retention policy management for tenant-scoped enterprise data."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from maisb.core.models.tenant import Tenant


@dataclass
class RetentionPolicy:
    tenant_id: str
    retention_days: int
    privacy_mode: str
    delete_before: datetime


def get_retention_policy(db: Session, tenant_id: str) -> RetentionPolicy:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise ValueError("Tenant not found")

    days = tenant.metadata_retention_days or 90
    config = tenant.config or {}
    privacy_mode = config.get("privacy_mode", "standard")

    return RetentionPolicy(
        tenant_id=tenant_id,
        retention_days=days,
        privacy_mode=privacy_mode,
        delete_before=datetime.utcnow() - timedelta(days=days),
    )


def update_retention_policy(db: Session, tenant_id: str, retention_days: int | None = None, privacy_mode: str | None = None) -> RetentionPolicy:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise ValueError("Tenant not found")

    if retention_days is not None:
        if retention_days < 1 or retention_days > 3650:
            raise ValueError("retention_days must be between 1 and 3650")
        tenant.metadata_retention_days = retention_days

    config = tenant.config or {}
    if privacy_mode:
        config["privacy_mode"] = privacy_mode
        tenant.config = config

    db.commit()
    return get_retention_policy(db, tenant_id)
