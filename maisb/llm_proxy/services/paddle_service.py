from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

PADDLE_ENV = os.environ.get("PADDLE_ENV", "sandbox")
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
PADDLE_PRO_PRICE_ID = os.environ.get("PADDLE_PRO_PRICE_ID") or os.environ.get("PADDLE_PRICE_ID_PRO", "")
PADDLE_CERTIFY_PRICE_ID = os.environ.get("PADDLE_CERTIFY_PRICE_ID") or os.environ.get("PADDLE_PRICE_ID_CERTIFY", "")
PADDLE_CHECKOUT_URL = os.environ.get("PADDLE_CHECKOUT_URL", "")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")


def price_id_for_plan(plan: str) -> str:
    if plan == "certify":
        return PADDLE_CERTIFY_PRICE_ID
    return PADDLE_PRO_PRICE_ID


def create_checkout_payload(email: str, plan: str, company: Optional[str] = None, success_url: Optional[str] = None, cancel_url: Optional[str] = None) -> dict[str, Any]:
    price_id = price_id_for_plan(plan)
    if not price_id and not PADDLE_CHECKOUT_URL:
        raise ValueError("Paddle is not configured: missing price ID or legacy checkout URL")
    base = {
        "provider": "paddle",
        "provisioning": "pending_webhook_confirmation",
        "environment": PADDLE_ENV,
        "plan": plan,
        "price_id": price_id,
        "customer": {"email": email, "company": company},
        "success_url": success_url or f"{APP_DASHBOARD_URL}/billing?checkout=success",
        "cancel_url": cancel_url or f"{APP_DASHBOARD_URL}/billing?checkout=cancelled",
        "message": "Access is upgraded only after trusted Paddle webhook confirmation.",
    }
    if PADDLE_CHECKOUT_URL:
        from urllib.parse import urlencode
        glue = "&" if "?" in PADDLE_CHECKOUT_URL else "?"
        base["checkout_url"] = f"{PADDLE_CHECKOUT_URL}{glue}{urlencode({'email': email, 'plan': plan, 'price_id': price_id, 'success_url': base['success_url'], 'cancel_url': base['cancel_url']})}"
    else:
        base["checkout_config"] = {"items": [{"priceId": price_id, "quantity": 1}], "customer": {"email": email}, "customData": {"plan": plan, "company": company or ""}}
    return base


def _parse_signature(header: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (header or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def verify_webhook_signature(raw_body: bytes, signature_header: Optional[str], tolerance_seconds: int = 300) -> bool:
    if not PADDLE_WEBHOOK_SECRET or not signature_header:
        return False
    parts = _parse_signature(signature_header)
    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False
    try:
        if abs(time.time() - int(ts)) > tolerance_seconds:
            return False
    except ValueError:
        return False
    signed = ts.encode("utf-8") + b":" + raw_body
    digest = hmac.new(PADDLE_WEBHOOK_SECRET.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, h1)


def parse_event(raw_body: bytes) -> dict[str, Any]:
    return json.loads(raw_body.decode("utf-8"))


def event_identity(payload: dict[str, Any]) -> dict[str, str]:
    return {"event_id": str(payload.get("event_id") or payload.get("id") or ""), "event_type": str(payload.get("event_type") or payload.get("type") or "unknown")}


def event_customer_email(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    customer = data.get("customer") or {}
    custom = data.get("custom_data") or {}
    return str(customer.get("email") or data.get("customer_email") or custom.get("email") or "")


def event_price_id(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    items = data.get("items") or []
    if items and isinstance(items, list):
        first = items[0] or {}
        price = first.get("price") or {}
        return str(price.get("id") or first.get("price_id") or "")
    price = data.get("price") or {}
    return str(price.get("id") or data.get("price_id") or "")


def event_customer_id(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    customer = data.get("customer") or {}
    return str(customer.get("id") or data.get("customer_id") or "")


def event_subscription_id(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    return str(data.get("subscription_id") or data.get("id") or "")


def plan_for_price(price_id: str) -> str:
    if price_id and price_id == PADDLE_CERTIFY_PRICE_ID:
        return "certify"
    return "pro"
