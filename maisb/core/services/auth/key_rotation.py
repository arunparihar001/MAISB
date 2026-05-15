"""API key rotation service."""
from sqlalchemy.orm import Session
from maisb.core.auth.key_manager import KeyManager
from maisb.core.audit.logger import AuditLogger


class KeyRotationService:
    @staticmethod
    def rotate(db: Session, tenant_id: str, key_id: str, expires_in_days: int | None = None):
        new_key_id, raw_key = KeyManager.rotate_key(
            db=db,
            key_id=key_id,
            tenant_id=tenant_id,
            expires_in_days=expires_in_days,
        )
        AuditLogger.log_key_revoked(db, tenant_id, key_id)
        AuditLogger.log_key_generated(db, tenant_id, new_key_id)
        return new_key_id, raw_key
