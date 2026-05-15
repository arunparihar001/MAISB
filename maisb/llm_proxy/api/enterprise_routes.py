# maisb/llm_proxy/api/enterprise_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Enterprise Phase 1 API routes
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from maisb.core.database import get_db_session
from maisb.core.models.tenant import Tenant
from maisb.core.models.policy import Policy
from maisb.core.models.audit import AuditLog
from maisb.core.auth.key_manager import KeyManager
from maisb.core.auth.rbac import role_summary
from maisb.core.audit.logger import AuditLogger
from maisb.core.bootstrap import ensure_default_enterprise
from maisb.core.services.tenant_service import TenantService
from maisb.core.services.auth.api_keys import APIKeyService
from maisb.core.services.auth.key_rotation import KeyRotationService
from maisb.core.services.auth.permissions import all_scopes
from maisb.core.governance.retention_policy import get_retention_policy, update_retention_policy
from maisb.core.governance.privacy_modes import available_privacy_modes
from maisb.core.governance.data_lifecycle import DataLifecycleManager

ADMIN_KEY = os.environ.get("ADMIN_KEY", "change_me_in_production")
router = APIRouter(tags=["Enterprise"])


def require_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


class TenantCreateRequest(BaseModel):
    tenant_id: Optional[str] = None
    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class TenantConfigUpdateRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)


class KeyCreateRequest(BaseModel):
    tenant_id: str = "default"
    scopes: list[str] = Field(default_factory=lambda: ["scan"])
    expires_in_days: Optional[int] = None
    role: str = "viewer"
    monthly_limit: Optional[int] = None


class PolicyCreateRequest(BaseModel):
    tenant_id: str = "default"
    name: str = "Default Policy"
    description: Optional[str] = None
    rules: list[dict[str, Any]] = Field(default_factory=list)
    channel_rules: dict[str, Any] = Field(default_factory=dict)
    objective_restrictions: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class RetentionUpdateRequest(BaseModel):
    tenant_id: str = "default"
    retention_days: Optional[int] = None
    privacy_mode: Optional[str] = None


@router.get("/v1/enterprise/health")
def enterprise_health():
    with get_db_session() as db:
        ensure_default_enterprise(db)
        return {
            "status": "ok",
            "enterprise": True,
            "phase1_complete": True,
            "tenants": db.query(Tenant).count(),
            "policies": db.query(Policy).count(),
            "audit_logs": db.query(AuditLog).count(),
            "features": {
                "multi_tenant": True,
                "api_keys": True,
                "scopes": True,
                "usage_limits": True,
                "policy_engine": True,
                "audit_logging": True,
                "retention": True,
                "privacy_modes": True,
                "rbac": True,
            },
        }


@router.post("/v1/enterprise/tenants")
def create_tenant(body: TenantCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        try:
            tenant = TenantService.create_tenant(db, name=body.name, config=body.config, tenant_id=body.tenant_id)
            ensure_default_enterprise(db, tenant_id=tenant.tenant_id, tenant_name=tenant.name)
            return tenant.to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))


@router.get("/v1/enterprise/tenants")
def list_tenants(admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        tenants = TenantService.list_tenants(db)
        return {"tenants": [t.to_dict() for t in tenants]}


@router.patch("/v1/enterprise/tenants/{tenant_id}/config")
def update_tenant_config(tenant_id: str, body: TenantConfigUpdateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        try:
            tenant = TenantService.update_config(db, tenant_id, body.config)
            return tenant.to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/v1/auth/generate-key")
def generate_key(body: KeyCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=body.tenant_id)
        key_id, raw_key = APIKeyService.generate(
            db=db,
            tenant_id=body.tenant_id,
            scopes=body.scopes,
            role=body.role,
            monthly_limit=body.monthly_limit,
            expires_in_days=body.expires_in_days,
        )
    return {
        "key_id": key_id,
        "raw_key": raw_key,
        "tenant_id": body.tenant_id,
        "scopes": body.scopes,
        "role": body.role,
        "monthly_limit": body.monthly_limit,
        "expires_in_days": body.expires_in_days,
        "warning": "Copy raw_key now. It will not be shown again.",
    }


@router.get("/v1/auth/keys")
def list_enterprise_keys(tenant_id: str = Query("default"), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=tenant_id)
        keys = KeyManager.list_keys(db, tenant_id)
        return {"tenant_id": tenant_id, "keys": [k.to_dict() for k in keys]}


@router.post("/v1/auth/revoke-key/{key_id}")
def revoke_key(key_id: str, tenant_id: str = Query("default"), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        success = APIKeyService.revoke(db, tenant_id, key_id)
    return {"success": success, "key_id": key_id, "tenant_id": tenant_id}


@router.post("/v1/auth/rotate-key/{key_id}")
def rotate_key(key_id: str, tenant_id: str = Query("default"), expires_in_days: Optional[int] = Query(None), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=tenant_id)
        new_key_id, raw_key = KeyRotationService.rotate(db, tenant_id, key_id, expires_in_days)
    return {
        "old_key_id": key_id,
        "new_key_id": new_key_id,
        "raw_key": raw_key,
        "tenant_id": tenant_id,
        "warning": "Copy raw_key now. It will not be shown again.",
    }


@router.get("/v1/auth/scopes")
def get_scopes(admin_key: str = Query(...)):
    require_admin(admin_key)
    return {"scopes": all_scopes(), "roles": role_summary()}


@router.post("/v1/policies")
def create_policy(body: PolicyCreateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=body.tenant_id)
        if body.is_active:
            db.query(Policy).filter(Policy.tenant_id == body.tenant_id, Policy.is_active == True).update({"is_active": False})
        policy = Policy(
            policy_id=f"policy_{uuid4().hex[:12]}",
            tenant_id=body.tenant_id,
            name=body.name,
            description=body.description,
            version=1,
            rules=body.rules,
            channel_rules=body.channel_rules,
            objective_restrictions=body.objective_restrictions,
            is_active=body.is_active,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        AuditLogger.log_policy_change(db, body.tenant_id, policy.policy_id, {"action": "create", "name": body.name})
        return policy.to_dict()


@router.get("/v1/policies/active")
def get_active_policy(tenant_id: str = Query("default"), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=tenant_id)
        policy = db.query(Policy).filter(Policy.tenant_id == tenant_id, Policy.is_active == True).order_by(Policy.created_at.desc()).first()
        return {"tenant_id": tenant_id, "policy": policy.to_dict() if policy else None}


@router.get("/v1/audit/logs")
def get_audit_logs(tenant_id: str = Query("default"), limit: int = Query(50, ge=1, le=500), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        ensure_default_enterprise(db, tenant_id=tenant_id)
        logs = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return {"tenant_id": tenant_id, "logs": [log.to_dict() for log in logs]}


@router.get("/v1/governance/privacy-modes")
def privacy_modes(admin_key: str = Query(...)):
    require_admin(admin_key)
    return {"privacy_modes": available_privacy_modes()}


@router.get("/v1/governance/retention")
def read_retention(tenant_id: str = Query("default"), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        policy = get_retention_policy(db, tenant_id)
        return policy.__dict__ | {"delete_before": policy.delete_before.isoformat()}


@router.patch("/v1/governance/retention")
def update_retention(body: RetentionUpdateRequest, admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        try:
            policy = update_retention_policy(db, body.tenant_id, body.retention_days, body.privacy_mode)
            return policy.__dict__ | {"delete_before": policy.delete_before.isoformat()}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.post("/v1/governance/lifecycle/purge")
def purge_lifecycle(tenant_id: str = Query("default"), dry_run: bool = Query(True), admin_key: str = Query(...)):
    require_admin(admin_key)
    with get_db_session() as db:
        return DataLifecycleManager.purge_expired_audit_logs(db, tenant_id, dry_run=dry_run)
