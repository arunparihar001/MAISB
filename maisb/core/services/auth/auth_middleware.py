"""Authentication middleware helpers for enterprise API keys."""
from dataclasses import dataclass
from datetime import datetime
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from maisb.core.auth.key_manager import KeyManager
from maisb.core.auth.rbac import require_permission_for_key
from maisb.core.services.auth.permissions import require_scope_for_key
from maisb.core.services.tenant_service import TenantService


@dataclass
class EnterpriseAuthContext:
    tenant_id: str
    key_id: str
    role: str
    scopes: list[str]
    usage_count: int
    monthly_limit: int | None


def extract_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def authenticate_api_key(
    db: Session,
    raw_key: str,
    tenant_id: str | None = None,
    required_scope: str | None = None,
    required_permission: str | None = None,
    consume_usage: bool = False,
) -> EnterpriseAuthContext:
    api_key = KeyManager.verify_key(db, raw_key, tenant_id=tenant_id)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or expired enterprise API key")

    tenant_id = tenant_id or api_key.tenant_id
    TenantService.require_tenant(db, tenant_id)

    if required_scope:
        require_scope_for_key(api_key, required_scope)

    if required_permission:
        require_permission_for_key(api_key, required_permission)

    api_key.reset_usage_if_needed()
    if consume_usage:
        if not api_key.can_use():
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "enterprise_quota_exceeded",
                    "message": "Enterprise API key monthly usage limit reached.",
                    "monthly_limit": api_key.monthly_limit,
                    "usage_count": api_key.usage_count,
                    "usage_reset_at": api_key.usage_reset_at.isoformat() if api_key.usage_reset_at else None,
                },
            )
        api_key.record_use()
        db.commit()

    return EnterpriseAuthContext(
        tenant_id=api_key.tenant_id,
        key_id=api_key.key_id,
        role=api_key.role,
        scopes=api_key.scopes or [],
        usage_count=api_key.usage_count or 0,
        monthly_limit=api_key.monthly_limit,
    )


def authenticate_request(
    db: Session,
    request: Request,
    required_scope: str | None = None,
    required_permission: str | None = None,
    consume_usage: bool = False,
) -> EnterpriseAuthContext:
    raw_key = extract_bearer_token(request) or request.headers.get("X-API-Key")
    if not raw_key:
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token or X-API-Key header")

    tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("X-Tenant-ID")
    return authenticate_api_key(
        db=db,
        raw_key=raw_key,
        tenant_id=tenant_id,
        required_scope=required_scope,
        required_permission=required_permission,
        consume_usage=consume_usage,
    )
