"""Role-Based Access Control for MAISB Enterprise Phase 1."""
from enum import Enum
from fastapi import HTTPException


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class Permission(str, Enum):
    TENANT_MANAGE = "tenant:manage"
    KEY_MANAGE = "key:manage"
    SCAN = "scan"
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    AUDIT_READ = "audit:read"
    GOVERNANCE_READ = "governance:read"
    GOVERNANCE_WRITE = "governance:write"


ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.TENANT_MANAGE,
        Permission.KEY_MANAGE,
        Permission.SCAN,
        Permission.POLICY_READ,
        Permission.POLICY_WRITE,
        Permission.AUDIT_READ,
        Permission.GOVERNANCE_READ,
        Permission.GOVERNANCE_WRITE,
    },
    Role.ANALYST: {
        Permission.SCAN,
        Permission.POLICY_READ,
        Permission.AUDIT_READ,
        Permission.GOVERNANCE_READ,
    },
    Role.VIEWER: {
        Permission.POLICY_READ,
        Permission.GOVERNANCE_READ,
    },
    Role.AUDITOR: {
        Permission.AUDIT_READ,
        Permission.POLICY_READ,
        Permission.GOVERNANCE_READ,
    },
}


def normalize_role(role: str | None) -> Role:
    try:
        return Role((role or "viewer").lower())
    except ValueError:
        return Role.VIEWER


def has_permission(role: str | Role, permission: str | Permission) -> bool:
    role = normalize_role(role if isinstance(role, str) else role.value)
    permission = Permission(permission) if isinstance(permission, str) else permission
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission_for_key(api_key, permission: str | Permission):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if not has_permission(api_key.role, permission):
        raise HTTPException(status_code=403, detail=f"Role '{api_key.role}' lacks permission '{permission}'")
    return True


def role_summary():
    return {role.value: [p.value for p in perms] for role, perms in ROLE_PERMISSIONS.items()}
