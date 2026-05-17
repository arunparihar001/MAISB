import logging
import os
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "MAISB <noreply@maisb.app>")
RESEND_REPLY_TO = os.environ.get("RESEND_REPLY_TO", "")
SALES_NOTIFY_EMAIL = os.environ.get("SALES_NOTIFY_EMAIL", "")
SECURITY_NOTIFY_EMAIL = os.environ.get("SECURITY_NOTIFY_EMAIL", "")


def _send_email(to: Iterable[str], subject: str, html: str) -> bool:
    recipients = [x for x in to if x]
    if not recipients or not RESEND_API_KEY:
        return False
    try:
        import resend  # type: ignore

        resend.api_key = RESEND_API_KEY
        payload = {
            "from": RESEND_FROM,
            "to": recipients,
            "subject": subject,
            "html": html,
        }
        if RESEND_REPLY_TO:
            payload["reply_to"] = RESEND_REPLY_TO
        resend.Emails.send(payload)
        return True
    except Exception as exc:  # fail-safe by design
        logger.exception("Resend delivery failed: %s", exc)
        return False


def send_api_key_created_email(email: str, raw_api_key: str, api_key_masked: str) -> bool:
    return _send_email([email], "Your MAISB API key", f"<p>Your API key was created.</p><p><b>Key (shown once):</b> {raw_api_key}</p><p>Masked: {api_key_masked}</p>")


def send_billing_request_email(email: str, plan: str, request_id: str, company: Optional[str]) -> bool:
    return _send_email([email], "MAISB billing request received", f"<p>We received your billing request.</p><p>Request: {request_id}<br/>Plan: {plan}<br/>Company: {company or 'N/A'}</p>")


def send_certify_started_email(email: str, order_id: str, company: str) -> bool:
    return _send_email([email], "MAISB Certify started", f"<p>Your Certify order is created.</p><p>Order: {order_id}<br/>Company: {company}</p>")


def send_certify_report_ready_email(email: str, order_id: str, report_url: str, badge_url: str) -> bool:
    return _send_email([email], "MAISB Certify report ready", f"<p>Your Certify report is ready.</p><p>Order: {order_id}</p><p><a href='{report_url}'>Report PDF</a> · <a href='{badge_url}'>Badge SVG</a></p>")


def send_admin_notification(subject: str, message: str) -> bool:
    recipients = [SALES_NOTIFY_EMAIL, SECURITY_NOTIFY_EMAIL]
    return _send_email(recipients, subject, f"<p>{message}</p>")
