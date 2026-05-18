from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services.billing_store import get_billing_status, init_billing_store, store_webhook_event, upsert_subscription
from services.paddle_service import (
    create_checkout_payload,
    event_customer_email,
    event_customer_id,
    event_identity,
    event_price_id,
    event_subscription_id,
    parse_event,
    plan_for_price,
    verify_webhook_signature,
)

router = APIRouter(tags=["Paddle Billing"])
init_billing_store()


class CheckoutSessionRequest(BaseModel):
    email: str
    company: Optional[str] = None
    plan: str = Field("pro", pattern="^(pro|certify)$")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.post("/v1/billing/paddle/checkout-session")
def paddle_checkout_session(body: CheckoutSessionRequest) -> Dict[str, Any]:
    try:
        checkout = create_checkout_payload(body.email, body.plan, body.company, body.success_url, body.cancel_url)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return checkout


# Backward-compatible alias for earlier frontend attempts.
@router.post("/v1/billing/paddle/checkout-link")
def paddle_checkout_link(body: CheckoutSessionRequest) -> Dict[str, Any]:
    return paddle_checkout_session(body)


@router.post("/v1/billing/paddle/webhook")
async def paddle_webhook(request: Request, paddle_signature: str = Header(default="")) -> Dict[str, Any]:
    raw = await request.body()
    if not verify_webhook_signature(raw, paddle_signature):
        raise HTTPException(status_code=401, detail="Invalid Paddle webhook signature")
    payload = parse_event(raw)
    identity = event_identity(payload)
    event_id = identity["event_id"]
    event_type = identity["event_type"]
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing Paddle event id")
    inserted = store_webhook_event(event_id, event_type, payload)
    if not inserted:
        return {"ok": True, "duplicate": True, "event_id": event_id}

    email = event_customer_email(payload)
    price_id = event_price_id(payload)
    plan = plan_for_price(price_id)
    customer_id = event_customer_id(payload)
    subscription_id = event_subscription_id(payload)

    if email and event_type in {"transaction.completed", "subscription.created", "subscription.updated", "subscription.resumed"}:
        upsert_subscription(email=email, plan=plan, status="active", customer_id=customer_id, subscription_id=subscription_id, price_id=price_id)
    elif email and event_type in {"subscription.canceled", "subscription.paused"}:
        upsert_subscription(email=email, plan=plan, status="inactive", customer_id=customer_id, subscription_id=subscription_id, price_id=price_id)

    return {"ok": True, "event_id": event_id, "event_type": event_type, "processed": True}


@router.get("/v1/billing/paddle/status")
def paddle_status(email: Optional[str] = Query(default=None), api_key: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    return get_billing_status(email=email, api_key=api_key)
