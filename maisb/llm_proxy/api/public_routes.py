# maisb/llm_proxy/api/public_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# MAISB Public Info Routes
#
# These endpoints return lightweight JSON with canonical URLs for:
#   GET /terms   — terms of service
#   GET /privacy — privacy policy
#   GET /refund  — refund policy
#
# These complement the frontend pages at the same paths on app.maisb.app.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://maisb.app")

router = APIRouter(tags=["Public"])


@router.get("/terms")
def terms() -> Dict[str, Any]:
    return {
        "page": "terms",
        "url": f"{PUBLIC_BASE_URL}/terms",
        "summary": "MAISB Shield Terms of Service govern use of the API and SDKs.",
    }


@router.get("/privacy")
def privacy() -> Dict[str, Any]:
    return {
        "page": "privacy",
        "url": f"{PUBLIC_BASE_URL}/privacy",
        "summary": "MAISB Shield Privacy Policy describes how scan data and account data is handled.",
    }


@router.get("/refund")
def refund() -> Dict[str, Any]:
    return {
        "page": "refund",
        "url": f"{PUBLIC_BASE_URL}/refund",
        "summary": "MAISB Shield Refund Policy. For billing queries contact sales@maisb.app.",
    }
