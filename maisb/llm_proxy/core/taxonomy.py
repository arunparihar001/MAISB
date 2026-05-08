# core/taxonomy.py
# T0–T12 threat taxonomy definitions.
# Maps reason tags (produced by detection/patterns.py) to taxonomy class strings.
#
# The taxonomy_class stored on PipelineState is the HIGHEST-severity class
# hit during detection. The orchestrator stores it in ScanResponse.taxonomy_class.
#
# Reason tags come from detection/patterns.py as short kebab-case strings like:
#   "instruction-override", "confirmation-bypass", "jailbreak", etc.
# These map to T-codes which are returned in the API response.

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomyEntry:
    code:        str   # "T1"
    name:        str   # human-readable
    description: str
    severity:    int   # 1 (low) – 5 (critical)


# ── Taxonomy table ────────────────────────────────────────────────────────────

TAXONOMY: dict[str, TaxonomyEntry] = {
    "T0": TaxonomyEntry(
        code="T0", name="Benign",
        description="No threat detected.",
        severity=0,
    ),
    "T1": TaxonomyEntry(
        code="T1", name="Direct Instruction Override",
        description="Explicit attempt to override or reset system instructions.",
        severity=5,
    ),
    "T2": TaxonomyEntry(
        code="T2", name="Confirmation / Safeguard Bypass",
        description="Attempt to skip confirmation steps or safety checks.",
        severity=4,
    ),
    "T3": TaxonomyEntry(
        code="T3", name="Data Exfiltration",
        description="Attempt to extract credentials, secrets, or user data.",
        severity=5,
    ),
    "T4": TaxonomyEntry(
        code="T4", name="Bulk Action Trigger",
        description="Attempt to execute mass operations without per-item approval.",
        severity=4,
    ),
    "T5": TaxonomyEntry(
        code="T5", name="Suspicious Destination",
        description="Payment or data sent to an unknown or attacker-controlled destination.",
        severity=4,
    ),
    "T6": TaxonomyEntry(
        code="T6", name="URI / Scheme Abuse",
        description="Malicious URI scheme or protocol abuse.",
        severity=3,
    ),
    "T7": TaxonomyEntry(
        code="T7", name="Indirect / Hidden Injection",
        description="Injection via webview, hidden HTML, or tool API response.",
        severity=5,
    ),
    "T8": TaxonomyEntry(
        code="T8", name="Multi-Vector Combined Attack",
        description="Multiple attack signals combined in one payload.",
        severity=5,
    ),
    "T9": TaxonomyEntry(
        code="T9", name="Role Confusion / Persona Hijack",
        description="Attempt to assign the AI a new unrestricted persona.",
        severity=4,
    ),
    "T10": TaxonomyEntry(
        code="T10", name="Jailbreak",
        description="Explicit jailbreak attempt (DAN mode, unrestricted mode, etc.).",
        severity=5,
    ),
}


# ── Reason tag → taxonomy code ────────────────────────────────────────────────
# These reason tags are the exact strings produced by detection/patterns.py.
# Order matters: higher entries take priority when multiple tags hit.

_REASON_TAG_TO_CODE: list[tuple[str, str]] = [
    # T10 first — jailbreak is always highest display priority
    ("jailbreak",                   "T10"),
    # T7 — hidden/indirect injection
    ("hidden-css-injection",        "T7"),
    ("indirect-webview-injection",  "T7"),
    # T1 — direct override
    ("instruction-override",        "T1"),
    # T2 — confirmation bypass
    ("confirmation-bypass",         "T2"),
    # T3 — exfiltration
    ("exfiltration",                "T3"),
    # T4 — bulk action
    ("bulk-action",                 "T4"),
    # T5 — suspicious destination
    ("suspicious-destination",      "T5"),
    # T6 — URI abuse
    ("uri-scheme-abuse",            "T6"),
    # T9 — role confusion
    ("role-confusion",              "T9"),
    # Session-level
    ("session-escalation",          "T8"),
    # Intent conflict (adds to score but doesn't set class alone)
    ("intent-conflict",             "T1"),
]

# Priority order for determining the single taxonomy_class to report
# Higher index = lower priority (T10 > T7 > T1 > T2 > ...)
_CODE_PRIORITY: list[str] = ["T10", "T7", "T1", "T3", "T2", "T8", "T4", "T5", "T6", "T9", "T0"]


def reasons_to_taxonomy_class(reasons: list[str]) -> str:
    """
    Given a list of reason tags from the detection engine,
    return the single highest-priority taxonomy class string.
    """
    if not reasons:
        return "T0"

    hit_codes: set[str] = set()
    for reason in reasons:
        for tag, code in _REASON_TAG_TO_CODE:
            if tag in reason:
                hit_codes.add(code)

    if not hit_codes:
        return "T0"

    # Return the highest-priority code
    for code in _CODE_PRIORITY:
        if code in hit_codes:
            return code

    return sorted(hit_codes)[0]


def get_taxonomy(code: str) -> TaxonomyEntry:
    return TAXONOMY.get(code, TAXONOMY["T0"])
