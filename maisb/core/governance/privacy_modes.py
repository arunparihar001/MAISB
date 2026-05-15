"""Privacy modes for payload previews and governance controls."""
from enum import Enum
import hashlib
import re


class PrivacyMode(str, Enum):
    FULL = "full"          # Store normal preview
    STANDARD = "standard"  # Store limited preview
    MINIMAL = "minimal"    # Store only hash and length
    STRICT = "strict"      # Store no payload preview


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)")


def sanitize_payload_preview(payload: str, mode: str = "standard", limit: int = 100) -> str:
    payload = payload or ""
    mode = (mode or PrivacyMode.STANDARD.value).lower()

    if mode == PrivacyMode.STRICT.value:
        return ""

    if mode == PrivacyMode.MINIMAL.value:
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"sha256:{digest};len:{len(payload)}"

    preview = payload[:limit]

    if mode == PrivacyMode.STANDARD.value:
        preview = EMAIL_RE.sub("[email-redacted]", preview)
        preview = PHONE_RE.sub("[phone-redacted]", preview)

    return preview


def available_privacy_modes() -> list[str]:
    return [m.value for m in PrivacyMode]
