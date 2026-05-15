"""Data lifecycle operations for retention enforcement."""
from sqlalchemy.orm import Session

from maisb.core.models.audit import AuditLog
from maisb.core.governance.retention_policy import get_retention_policy


class DataLifecycleManager:
    @staticmethod
    def purge_expired_audit_logs(db: Session, tenant_id: str, dry_run: bool = True) -> dict:
        policy = get_retention_policy(db, tenant_id)
        query = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.timestamp < policy.delete_before,
        )
        count = query.count()

        if not dry_run and count:
            query.delete(synchronize_session=False)
            db.commit()

        return {
            "tenant_id": tenant_id,
            "retention_days": policy.retention_days,
            "delete_before": policy.delete_before.isoformat(),
            "expired_audit_logs": count,
            "dry_run": dry_run,
            "deleted": 0 if dry_run else count,
        }
