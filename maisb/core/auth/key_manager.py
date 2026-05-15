"""
API Key management

Phase 1 complete version:
- generation
- expiration
- revocation
- rotation
- scope storage
- role storage
- monthly usage limit storage
"""
from sqlalchemy.orm import Session
from maisb.core.models.auth import APIKey
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import logging

logger = logging.getLogger(__name__)


class KeyManager:
    """Manage API keys for tenants."""

    @staticmethod
    def create_key(
        db: Session,
        tenant_id: str,
        scopes: list = None,
        expires_in_days: int = None,
        role: str = "viewer",
        monthly_limit: int | None = None,
    ) -> tuple:
        """
        Create new API key for tenant.

        Returns:
            Tuple of (key_id, raw_key). Raw key should be returned once only.
        """
        api_key, raw_key = APIKey.generate_key(
            tenant_id=tenant_id,
            scopes=scopes or ["scan"],
            role=role,
            monthly_limit=monthly_limit,
        )

        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        db.add(api_key)
        db.commit()

        logger.info(f"Created API key {api_key.key_id} for tenant {tenant_id}")
        return api_key.key_id, raw_key

    @staticmethod
    def find_by_raw_key(db: Session, raw_key: str):
        if not raw_key:
            return None
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    @staticmethod
    def verify_key(db: Session, raw_key: str, tenant_id: str = None):
        """Verify an API key is valid. Optionally enforce tenant_id."""
        api_key = KeyManager.find_by_raw_key(db, raw_key)
        if not api_key:
            return None
        if tenant_id and api_key.tenant_id != tenant_id:
            return None
        if not api_key.is_valid():
            return None
        api_key.last_used = datetime.utcnow()
        db.commit()
        return api_key

    @staticmethod
    def revoke_key(db: Session, key_id: str, tenant_id: str) -> bool:
        api_key = db.query(APIKey).filter(
            APIKey.key_id == key_id,
            APIKey.tenant_id == tenant_id
        ).first()
        if api_key:
            api_key.revoked_at = datetime.utcnow()
            api_key.is_active = False
            db.commit()
            logger.info(f"Revoked API key {key_id} for tenant {tenant_id}")
            return True
        return False

    @staticmethod
    def rotate_key(
        db: Session,
        key_id: str,
        tenant_id: str,
        expires_in_days: int = None
    ) -> tuple:
        old_key = KeyManager.get_key(db, key_id, tenant_id)
        if old_key:
            scopes = old_key.scopes or ["scan"]
            role = old_key.role or "viewer"
            monthly_limit = old_key.monthly_limit
        else:
            scopes = ["scan"]
            role = "viewer"
            monthly_limit = None

        KeyManager.revoke_key(db, key_id, tenant_id)
        return KeyManager.create_key(
            db=db,
            tenant_id=tenant_id,
            scopes=scopes,
            role=role,
            monthly_limit=monthly_limit,
            expires_in_days=expires_in_days,
        )

    @staticmethod
    def list_keys(db: Session, tenant_id: str) -> list:
        return db.query(APIKey).filter(APIKey.tenant_id == tenant_id).all()

    @staticmethod
    def get_key(db: Session, key_id: str, tenant_id: str):
        return db.query(APIKey).filter(
            APIKey.key_id == key_id,
            APIKey.tenant_id == tenant_id
        ).first()
