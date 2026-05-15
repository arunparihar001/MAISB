"""
API Key and authentication models

Phase 1 complete version:
- key hashing
- expiration
- revocation
- scopes
- role binding
- usage limits
"""
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Integer
from maisb.core.models import Base
from datetime import datetime, timedelta
import secrets
import hashlib


class APIKey(Base):
    """
    API Key for authentication and authorization.

    Raw keys are never stored. Only SHA-256 hashes are stored.
    """
    __tablename__ = "api_keys"

    key_id = Column(String(255), primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False, index=True)

    # Store SHA-256 hash of key, never raw key
    key_hash = Column(String(64), nullable=False, unique=True)

    # Authorization metadata
    scopes = Column(JSON, default=["scan"], nullable=True)
    role = Column(String(50), default="viewer", nullable=False)

    # Usage limits
    monthly_limit = Column(Integer, nullable=True)  # None = unlimited
    usage_count = Column(Integer, default=0, nullable=False)
    usage_reset_at = Column(DateTime, nullable=True)

    # Lifecycle metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<APIKey {self.key_id}>"

    @classmethod
    def generate_key(
        cls,
        tenant_id: str,
        scopes: list = None,
        role: str = "viewer",
        monthly_limit: int | None = None,
    ):
        """
        Generate a new API key.

        Returns:
            Tuple of (APIKey object, raw_key_string)
            The raw key should only be returned to user once.
        """
        raw_key = f"maisb_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = cls(
            key_id=f"key_{secrets.token_hex(8)}",
            tenant_id=tenant_id,
            key_hash=key_hash,
            scopes=scopes or ["scan"],
            role=role or "viewer",
            monthly_limit=monthly_limit,
            usage_count=0,
            usage_reset_at=datetime.utcnow() + timedelta(days=30),
        )

        return api_key, raw_key

    def verify_key(self, raw_key: str) -> bool:
        """Verify that a raw key matches this key's hash."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return key_hash == self.key_hash

    def is_valid(self) -> bool:
        """Check if key is currently valid."""
        if not self.is_active:
            return False
        if self.revoked_at:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def has_scope(self, scope: str) -> bool:
        scopes = self.scopes or []
        return "*" in scopes or scope in scopes

    def reset_usage_if_needed(self):
        now = datetime.utcnow()
        if not self.usage_reset_at or now >= self.usage_reset_at:
            self.usage_count = 0
            self.usage_reset_at = now + timedelta(days=30)

    def can_use(self) -> bool:
        self.reset_usage_if_needed()
        if self.monthly_limit is None:
            return True
        return (self.usage_count or 0) < self.monthly_limit

    def record_use(self):
        self.reset_usage_if_needed()
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used = datetime.utcnow()

    def to_dict(self, include_secret=False):
        """Convert to dictionary. Never includes raw secret."""
        return {
            "key_id": self.key_id,
            "tenant_id": self.tenant_id,
            "scopes": self.scopes,
            "role": self.role,
            "monthly_limit": self.monthly_limit,
            "usage_count": self.usage_count,
            "usage_reset_at": self.usage_reset_at.isoformat() if self.usage_reset_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_active": self.is_active,
        }
