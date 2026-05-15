"""FastAPI middleware for tenant context extraction."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Adds request.state.tenant_id for every request.

    Sources checked in order:
    1. X-Tenant-ID header
    2. X-MAISB-Tenant header
    3. tenant_id query parameter
    4. default fallback for local/dev endpoints
    """

    def __init__(self, app, required_for_prefixes: tuple[str, ...] = ("/v1/scan",)):
        super().__init__(app)
        self.required_for_prefixes = required_for_prefixes

    async def dispatch(self, request: Request, call_next):
        tenant_id = (
            request.headers.get("X-Tenant-ID")
            or request.headers.get("X-MAISB-Tenant")
            or request.query_params.get("tenant_id")
            or "default"
        )
        request.state.tenant_id = tenant_id

        if any(request.url.path.startswith(prefix) for prefix in self.required_for_prefixes):
            if not tenant_id:
                return JSONResponse(status_code=400, content={"detail": "Tenant ID required"})

        return await call_next(request)
