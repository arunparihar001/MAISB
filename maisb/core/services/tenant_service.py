"""Tenant service for Phase 1 enterprise multi-tenancy."""
from uuid import uuid4
from sqlalchemy.orm import Session
from maisb.core.models.tenant import Tenant


class TenantService:
    @staticmethod
    def create_tenant(db: Session, name: str, config: dict | None = None, tenant_id: str | None = None) -> Tenant:
        tenant_id = tenant_id or f"tenant_{uuid4().hex[:10]}"
        existing = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if existing:
            raise ValueError("Tenant already exists")
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            config=config or {},
            features_enabled={"policy_engine": True, "audit_logging": True, "api_keys": True},
            is_active=True,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def get_tenant(db: Session, tenant_id: str) -> Tenant | None:
        return db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

    @staticmethod
    def require_tenant(db: Session, tenant_id: str) -> Tenant:
        tenant = TenantService.get_tenant(db, tenant_id)
        if not tenant or not tenant.is_active:
            raise ValueError("Invalid or inactive tenant")
        return tenant

    @staticmethod
    def list_tenants(db: Session) -> list[Tenant]:
        return db.query(Tenant).order_by(Tenant.created_at.desc()).all()

    @staticmethod
    def update_config(db: Session, tenant_id: str, config: dict) -> Tenant:
        tenant = TenantService.require_tenant(db, tenant_id)
        current = tenant.config or {}
        current.update(config or {})
        tenant.config = current
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def validate_tenant_access(db: Session, tenant_id: str, api_key) -> bool:
        tenant = TenantService.get_tenant(db, tenant_id)
        if not tenant or not tenant.is_active:
            return False
        return api_key is not None and api_key.tenant_id == tenant_id and api_key.is_valid()
