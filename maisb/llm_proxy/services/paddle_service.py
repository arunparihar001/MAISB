import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional

PADDLE_ENV = os.environ.get("PADDLE_ENV", "sandbox")
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
PADDLE_PRO_PRICE_ID = os.environ.get("PADDLE_PRO_PRICE_ID", "")
PADDLE_CERTIFY_PRICE_ID = os.environ.get("PADDLE_CERTIFY_PRICE_ID", "")
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")


def price_id_for_plan(plan: str) -> str:
    if plan == "certify":
        return PADDLE_CERTIFY_PRICE_ID
    return PADDLE_PRO_PRICE_ID


def create_checkout_payload(email: str, plan: str) -> Dict[str, Any]:
    price_id = price_id_for_plan(plan)
    return {
        "environment": PADDLE_ENV,
        "client_token_required": True,
        "price_id": price_id,
        "plan": plan,
        "customer": {"email": email},
        "success_url": f"{APP_DASHBOARD_URL}/billing?checkout=success",
        "cancel_url": f"{APP_DASHBOARD_URL}/billing?checkout=cancelled",
    }


def _parse_signature(signature_header: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for part in (signature_header or "").split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def verify_webhook_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not PADDLE_WEBHOOK_SECRET:
        return False
    parts = _parse_signature(signature_header or "")
    ts = parts.get("ts", "")
    h1 = parts.get("h1", "")
    if not ts or not h1:
        return False
    signed = f"{ts}:{raw_body.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(PADDLE_WEBHOOK_SECRET.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, h1)


def parse_event(raw_body: bytes) -> Dict[str, Any]:
    return json.loads(raw_body.decode("utf-8"))


def event_identity(payload: Dict[str, Any]) -> Dict[str, str]:
    event_id = str(payload.get("event_id") or payload.get("id") or "")
    event_type = str(payload.get("event_type") or payload.get("type") or "unknown")
    return {"event_id": event_id, "event_type": event_type}


def event_customer_email(payload: Dict[str, Any]) -> str:
    data = payload.get("data") or {}
    customer = data.get("customer") or {}
    custom_data = data.get("custom_data") or {}
    return str(customer.get("email") or custom_data.get("email") or "")


def event_price_id(payload: Dict[str, Any]) -> str:
    data = payload.get("data") or {}
    items = data.get("items") or []
    if items and isinstance(items, list):
        first = items[0] or {}
        price = first.get("price") or {}
        return str(price.get("id") or first.get("price_id") or "")
    return str((data.get("price") or {}).get("id") or "")


def plan_for_price(price_id: str) -> str:
    if price_id and price_id == PADDLE_CERTIFY_PRICE_ID:
        return "certify"
    return "pro"
