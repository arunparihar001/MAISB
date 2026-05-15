"""
MAISB Enterprise bootstrap helpers.

Creates default tenant/policy and runs safe Phase 1 migrations.
"""
from uuid import uuid4
from sqlalchemy.orm import Session

from maisb.core.migrations import run_phase1_migrations
from maisb.core.models.tenant import Tenant
from maisb.core.models.policy import Policy


def ensure_default_enterprise(
    db: Session,
    tenant_id: str = "default",
    tenant_name: str = "Default Tenant"
) -> Tenant:
    """Ensure a tenant and a default policy exist."""
    run_phase1_migrations()

    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

    if not tenant:
        tenant = Tenant(
            tenant_id=tenant_id,
            name=tenant_name,
            config={"privacy_mode": "standard", "created_by": "enterprise_bootstrap"},
            features_enabled={
                "policy_engine": True,
                "audit_logging": True,
                "api_keys": True,
                "rbac": True,
                "retention": True,
            },
            metadata_retention_days=90,
            max_api_keys=10,
            is_active=True,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    active_policy = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.is_active == True
    ).first()

    if not active_policy:
        policy = Policy(
            policy_id=f"policy_{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            name="Default Enterprise Policy",
            description="Default policy created automatically for Phase 1 enterprise integration.",
            version=1,
            rules=[],
            channel_rules={
                "clipboard": {"block_threshold": 0.80, "review_threshold": 0.50},
                "webview": {"block_threshold": 0.75, "review_threshold": 0.45},
                "qr": {"block_threshold": 0.70, "review_threshold": 0.40},
                "deep_link": {"block_threshold": 0.70, "review_threshold": 0.40},
                "notification": {"block_threshold": 0.75, "review_threshold": 0.45},
                "file_upload": {"block_threshold": 0.80, "review_threshold": 0.50},
                "api_response": {"block_threshold": 0.85, "review_threshold": 0.55},
                "unknown": {"block_threshold": 0.80, "review_threshold": 0.50},
            },
            objective_restrictions={},
            is_active=True,
        )
        db.add(policy)
        db.commit()

    return tenant
