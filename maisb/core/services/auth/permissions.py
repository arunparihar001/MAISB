"""API scopes and permission helpers for MAISB Enterprise."""
from enum import Enum
from fastapi import HTTPException


class KeyScope(str, Enum):
    SCAN = "scan"
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    AUDIT_READ = "audit:read"
    KEY_MANAGE = "key:manage"
    TENANT_MANAGE = "tenant:manage"
    GOVERNANCE_READ = "governance:read"
    GOVERNANCE_WRITE = "governance:write"
    ALL = "*"


def normalize_scopes(scopes: list[str] | None) -> set[str]:
    return set(scopes or [])


def has_scope(scopes: list[str] | None, required_scope: str) -> bool:
    normalized = normalize_scopes(scopes)
    return KeyScope.ALL.value in normalized or required_scope in normalized


def require_scope_for_key(api_key, required_scope: str):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if not has_scope(api_key.scopes, required_scope):
        raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")
    return True


def all_scopes() -> list[str]:
    return [scope.value for scope in KeyScope]
