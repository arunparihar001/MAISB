import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services.billing_store import get_billing_status, init_billing_store, store_webhook_event, upsert_subscription
from services.paddle_service import (
    create_checkout_payload,
    event_customer_email,
    event_identity,
    event_price_id,
    parse_event,
    plan_for_price,
    verify_webhook_signature,
)

router = APIRouter(tags=["Paddle Billing"])
init_billing_store()


class CheckoutRequest(BaseModel):
    email: str
    plan: str = Field("pro", pattern="^(pro|certify)$")


@router.post("/v1/billing/paddle/checkout-session")
def paddle_checkout_session(body: CheckoutRequest) -> Dict[str, Any]:
    return {
        "checkout_id": f"chk_{secrets.token_hex(6)}",
        "provisioning": "pending_webhook_confirmation",
        "checkout": create_checkout_payload(body.email, body.plan),
    }


@router.post("/v1/billing/paddle/webhook")
async def paddle_webhook(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    signature = request.headers.get("Paddle-Signature")
    if not verify_webhook_signature(raw, signature):
        raise HTTPException(status_code=401, detail="Invalid Paddle signature")

    payload = parse_event(raw)
    identity = event_identity(payload)
    if not identity["event_id"]:
        raise HTTPException(status_code=400, detail="Missing Paddle event id")

    inserted = store_webhook_event(identity["event_id"], identity["event_type"], payload)
    if not inserted:
        return {"ok": True, "duplicate": True, "event_id": identity["event_id"]}

    email = event_customer_email(payload)
    price_id = event_price_id(payload)
    plan = plan_for_price(price_id)

    if email and identity["event_type"] in {"transaction.completed", "subscription.created", "subscription.updated"}:
        data = payload.get("data") or {}
        upsert_subscription(
            email=email,
            plan=plan,
            status="active",
            customer_id=str((data.get("customer") or {}).get("id") or ""),
            subscription_id=str(data.get("id") or identity["event_id"]),
            price_id=price_id,
        )

    return {"ok": True, "event_id": identity["event_id"], "processed": True}


@router.get("/v1/billing/paddle/status")
def paddle_status(email: Optional[str] = Query(None), api_key: Optional[str] = Query(None)) -> Dict[str, Any]:
    return get_billing_status(email=email, api_key=api_key)
