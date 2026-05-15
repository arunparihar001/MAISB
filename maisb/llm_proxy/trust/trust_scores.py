"""Dynamic channel trust scoring for Phase 2."""
from typing import Any, Dict, List

CHANNEL_TRUST_SCORES = {
    "internal_api": 0.93,
    "authenticated_user": 0.85,
    "api_response": 0.72,
    "file_upload": 0.40,
    "browser_plugin": 0.22,
    "clipboard": 0.15,
    "webview": 0.12,
    "qr": 0.10,
    "qr_code": 0.10,
    "push_notification": 0.08,
    "notification": 0.08,
    "nfc_tag": 0.08,
    "deep_link": 0.05,
    "share_intent": 0.05,
    "pdf_file": 0.35,
    "ocr_engine": 0.30,
    "agent": 0.45,
    "llm": 0.65,
    "unknown": 0.30,
}


class DynamicTrustScorer:
    """Calculate adaptive trust from channel and runtime context."""

    def calculate_trust(self, channel: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        channel = (channel or "unknown").lower()
        base = CHANNEL_TRUST_SCORES.get(channel, CHANNEL_TRUST_SCORES["unknown"])
        adjustments: List[Dict[str, Any]] = []
        if context.get("user_authenticated") is True:
            adjustments.append({"factor": "user_authenticated", "delta": 0.15})
        elif context.get("user_authenticated") is False:
            adjustments.append({"factor": "anonymous_or_unverified_user", "delta": -0.15})
        if isinstance(context.get("session_age_minutes"), (int, float)) and context["session_age_minutes"] > 60:
            adjustments.append({"factor": "stale_session", "delta": -0.10})
        if context.get("geo_consistent") is False:
            adjustments.append({"factor": "geographic_inconsistency", "delta": -0.20})
        if context.get("device_trusted") is True:
            adjustments.append({"factor": "trusted_device", "delta": 0.10})
        elif context.get("device_trusted") is False:
            adjustments.append({"factor": "untrusted_device", "delta": -0.10})
        trust_score = max(0.0, min(1.0, base + sum(item["delta"] for item in adjustments)))
        return {"channel": channel, "base_trust": round(base, 3), "adjustments": adjustments, "trust_score": round(trust_score, 3)}
