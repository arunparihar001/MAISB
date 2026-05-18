from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM") or os.environ.get("RESEND_FROM_EMAIL") or "MAISB <hello@updates.maisb.app>"
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")
SALES_NOTIFY_EMAIL = os.environ.get("SALES_NOTIFY_EMAIL", "")
SECURITY_NOTIFY_EMAIL = os.environ.get("SECURITY_NOTIFY_EMAIL", "")
RESEND_NOTIFY_EMAILS = [x.strip() for x in os.environ.get("RESEND_NOTIFY_EMAILS", "").split(",") if x.strip()]
APP_DASHBOARD_URL = os.environ.get("APP_DASHBOARD_URL", "https://app.maisb.app")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.maisb.app")


def configured() -> bool:
    return bool(RESEND_API_KEY and RESEND_FROM)


def _recipients(items: Iterable[Optional[str]]) -> list[str]:
    return [x.strip() for x in items if x and x.strip()]


def _send_email(to: Iterable[Optional[str]], subject: str, html: str, text: Optional[str] = None) -> bool:
    recipients = _recipients(to)
    if not recipients or not configured():
        logger.info("Resend email skipped: configured=%s recipients=%s", configured(), bool(recipients))
        return False
    payload: dict[str, object] = {"from": RESEND_FROM, "to": recipients, "subject": subject, "html": html}
    if text:
        payload["text"] = text
    if RESEND_REPLY_TO:
        payload["reply_to"] = RESEND_REPLY_TO

    try:
        # Prefer SDK when available, but do not require it for runtime survival.
        try:
            import resend  # type: ignore
            resend.api_key = RESEND_API_KEY
            resend.Emails.send(payload)  # type: ignore[arg-type]
            return True
        except ImportError:
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8):
                return True
    except (Exception, urllib.error.URLError) as exc:
        logger.exception("Resend delivery failed: %s", exc)
        return False


def _layout(title: str, body: str) -> str:
    return f"""
    <div style='font-family:Inter,Arial,sans-serif;background:#f8fafc;padding:28px;color:#0f172a'>
      <div style='max-width:680px;margin:auto;background:white;border:1px solid #e2e8f0;border-radius:20px;padding:28px'>
        <h1>{title}</h1>
        {body}
        <hr style='border:0;border-top:1px solid #e2e8f0;margin:24px 0' />
        <p style='color:#64748b;font-size:13px'>MAISB Shield · <a href='{API_BASE_URL}/docs'>API Docs</a> · <a href='{APP_DASHBOARD_URL}'>Dashboard</a></p>
      </div>
    </div>
    """


def send_api_key_created_email(email: str, raw_api_key: str, api_key_masked: str) -> bool:
    html = _layout("Your MAISB API key is ready", f"<p>Your API key was created. Store it securely; it is shown once for onboarding.</p><pre style='background:#0f172a;color:#d1fae5;padding:14px;border-radius:10px'>{raw_api_key}</pre><p>Masked: <b>{api_key_masked}</b></p>")
    return _send_email([email], "Your MAISB API key", html)


def send_billing_request_email(email: str, plan: str, request_id: str, company: Optional[str] = None) -> bool:
    html = _layout("Billing request received", f"<p>Request: <b>{request_id}</b></p><p>Plan: {plan}<br/>Company: {company or 'N/A'}</p>")
    send_admin_notification("MAISB billing request", f"Request {request_id} for {email} / {plan}")
    return _send_email([email], "MAISB billing request received", html)


def send_certify_started_email(email: str, order_id: str, company: str) -> bool:
    html = _layout("MAISB Certify started", f"<p>Order: <b>{order_id}</b></p><p>Company: {company}</p>")
    send_admin_notification("MAISB Certify order started", f"Order {order_id} for {company} ({email})")
    return _send_email([email], "MAISB Certify order started", html)


def send_certify_report_ready_email(email: str, order_id: str, report_url: str, badge_url: str) -> bool:
    html = _layout("MAISB Certify report ready", f"<p>Order: <b>{order_id}</b></p><p><a href='{report_url}'>Report PDF</a> · <a href='{badge_url}'>Badge SVG</a></p>")
    return _send_email([email], "MAISB Certify report ready", html)


def send_admin_notification(subject: str, message: str) -> bool:
    recipients = [SALES_NOTIFY_EMAIL, SECURITY_NOTIFY_EMAIL, *RESEND_NOTIFY_EMAILS]
    return _send_email(recipients, subject, _layout(subject, f"<p>{message}</p>"))
