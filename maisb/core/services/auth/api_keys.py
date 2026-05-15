"""High-level API key service."""
from sqlalchemy.orm import Session
from maisb.core.auth.key_manager import KeyManager
from maisb.core.audit.logger import AuditLogger


class APIKeyService:
    @staticmethod
    def generate(db: Session, tenant_id: str, scopes: list[str], role: str = "viewer", monthly_limit: int | None = None, expires_in_days: int | None = None):
        key_id, raw_key = KeyManager.create_key(
            db=db,
            tenant_id=tenant_id,
            scopes=scopes,
            role=role,
            monthly_limit=monthly_limit,
            expires_in_days=expires_in_days,
        )
        AuditLogger.log_key_generated(db, tenant_id, key_id)
        return key_id, raw_key

    @staticmethod
    def revoke(db: Session, tenant_id: str, key_id: str) -> bool:
        success = KeyManager.revoke_key(db, key_id, tenant_id)
        if success:
            AuditLogger.log_key_revoked(db, tenant_id, key_id)
        return success
