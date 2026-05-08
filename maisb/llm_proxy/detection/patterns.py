# detection/patterns.py
# Layer 3 — Phase 1: Pattern Matching Detection Engine
#
# Deterministic, sub-millisecond detection.
# Each rule set is channel-aware where relevant.
# Returns (attack_score_delta, list[reason_tag]).

from __future__ import annotations
import re
from typing import NamedTuple


class PatternHit(NamedTuple):
    score:   float
    reasons: list[str]


# ── Rule definitions ──────────────────────────────────────────────────────────
# Each entry: (phrases_set, score_per_hit, reason_tag, allow_partial_match)

# T1 — Direct instruction override
INSTRUCTION_OVERRIDE = {
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore your instructions",
    "disregard previous",
    "disregard all previous",
    "disregard your instructions",
    "disregard your earlier",
    "disregard earlier",
    "forget previous instructions",
    "forget all previous",
    "forget everything you were told",
    "set aside your earlier guidance",
    "override previous",
    "override all instructions",
    "ignore earlier guidance",
    "ignore your earlier",
    "your new instruction is",
    "new directive:",
    "system override:",
    "developer mode:",
    "ignore the above",
    "disregard the above",
    "ignore everything above",
    "ignore previous rules",
    "ignore previous commands",
    "new instruction:",
    "updated instruction:",
}

# T2 — Confirmation / safeguard bypass
CONFIRMATION_BYPASS = {
    "without confirmation",
    "without asking",
    "without asking the user",
    "do not ask",
    "do not show confirmation",
    "do not show",
    "skip confirmation",
    "skip the verification",
    "skip verification",
    "bypass confirmation",
    "bypass verification",
    "bypass the verification",
    "auto-approve",
    "auto approve",
    "automatically approve",
    "approve automatically",
    "approve all transfers",
    "approve all payments",
    "approve this without",
    "no need to confirm",
    "no confirmation needed",
    "proceed without confirmation",
    "proceed automatically",
    "execute without asking",
    "proceed without asking",
}

# T3 — Data exfiltration
EXFILTRATION = {
    "export all",
    "send all data",
    "send all",
    "send all account",
    "send all user",
    "export secrets",
    "export user data",
    "export credentials",
    "send to external",
    "leak the",
    "exfiltrate",
    "extract all",
    "dump all",
    "reveal all",
    "share all secrets",
    "override policy and export",
    "override policy and send",
    "transmit confidential",
    "send my data",
    "send account data",
}

# T4 — Bulk action triggers
BULK_ACTION = {
    "execute all pending",
    "approve all pending",
    "process all",
    "run all",
    "confirm all",
    "execute all transactions",
    "authorize all",
    "bulk approve",
    "mass transfer",
}

# T5 — Suspicious destination patterns
SUSPICIOUS_DESTINATION_PATTERNS = [
    r"attacker",
    r"evil\.com",
    r"malicious",
    r"hacker",
    r"to=\S+wallet",
    r"to=attacker",
    r"send.*to.*@(?!.*official|.*bank|.*jazz|.*easy)",  # suspicious email
]

# T6 — URI scheme abuse
URI_ABUSE = {
    "maisb://",
    "javascript:",
    "data:text",
    "vbscript:",
    "file://",
}

# T7 — Webview / indirect injection phrases
WEBVIEW_INDIRECT = {
    "ignore previous rules",
    "ignore previous instructions",
    "ignore all previous",
    "auto-approve",
    "auto approve",
    "approve all transfers",
    "without confirmation",
    "do not show confirmation",
    "bypass confirmation",
    "override policy",
    "override previous",
    "from this page",
    "as instructed by this page",
}

# T9 — Role confusion / persona hijack
ROLE_CONFUSION = {
    "you are now",
    "act as",
    "pretend you are",
    "pretend to be",
    "roleplay as",
    "your new persona",
    "you are a different",
    "forget you are",
    "you are not an ai",
    "you are a human",
    "developer override",
    "jailbreak",
    "dan mode",
    "unrestricted mode",
}

# T10 — Jailbreak
JAILBREAK = {
    "jailbreak",
    "dan mode",
    "unrestricted mode",
    "no restrictions",
    "without restrictions",
    "ignore safety",
    "bypass safety",
    "disable safety",
    "override safety",
    "safety mode off",
}

# System message impersonation
SYSTEM_IMPERSONATION = {
    "system:",
    "[system]",
    "<system>",
    "system message:",
    "developer message:",
    "admin message:",
    "bank message:",
    "jazzcash:",
    "easypaisa:",
    "from the bank:",
    "official notice:",
}


# ── Scoring engine ────────────────────────────────────────────────────────────

def contains_any(text: str, phrases: set) -> list[str]:
    """Return list of matched phrases from set."""
    return [p for p in phrases if p in text]


def run_pattern_detection(
    normalized: str,
    channel: str,
    hidden_fragments: list[str],
    had_homoglyphs: bool,
    had_base64: bool,
) -> PatternHit:
    """
    Run all pattern rules against the normalized text.
    Returns total score delta and list of reason tags.
    """
    text = normalized.lower()
    score   = 0.0
    reasons = []

    # ── T1: instruction override ──────────────────────────────────────────────
    hits = contains_any(text, INSTRUCTION_OVERRIDE)
    if hits:
        score   += 4.0 + min(len(hits) - 1, 2) * 1.0   # +1 per extra hit, max +2
        reasons.append("instruction-override")

    # ── T2: confirmation bypass ───────────────────────────────────────────────
    hits = contains_any(text, CONFIRMATION_BYPASS)
    if hits:
        score   += 3.0 + min(len(hits) - 1, 2) * 0.5
        reasons.append("confirmation-bypass")

    # ── T3: exfiltration ──────────────────────────────────────────────────────
    hits = contains_any(text, EXFILTRATION)
    if hits:
        score   += 3.5
        reasons.append("exfiltration")

    # ── T4: bulk action ───────────────────────────────────────────────────────
    hits = contains_any(text, BULK_ACTION)
    if hits:
        score   += 3.0
        reasons.append("bulk-action")

    # ── T5: suspicious destination ────────────────────────────────────────────
    for pat in SUSPICIOUS_DESTINATION_PATTERNS:
        if re.search(pat, text):
            score   += 2.5
            reasons.append("suspicious-destination")
            break

    # ── T6: URI scheme abuse ──────────────────────────────────────────────────
    hits = contains_any(text, URI_ABUSE)
    if hits:
        score   += 3.0
        reasons.append("uri-scheme-abuse")

    # ── T7: webview indirect injection (only when channel is web surface) ─────
    if channel in ("webview", "web_view", "web", "api_response"):
        hits = contains_any(text, WEBVIEW_INDIRECT)
        if hits:
            score   += 6.0   # high — webview is the highest-risk surface
            reasons.append("indirect-webview-injection")

    # ── T7: hidden CSS injection (CSS-hidden text found in HTML) ──────────────
    if hidden_fragments:
        hidden_text = " ".join(hidden_fragments).lower()
        hits = contains_any(hidden_text, INSTRUCTION_OVERRIDE | CONFIRMATION_BYPASS)
        if hits:
            score   += 7.0   # very high — attacker explicitly tried to hide it
            reasons.append("hidden-css-injection")

    # ── T9: role confusion ────────────────────────────────────────────────────
    hits = contains_any(text, ROLE_CONFUSION)
    if hits:
        score   += 3.0
        reasons.append("role-confusion")

    # ── T10: jailbreak ────────────────────────────────────────────────────────
    hits = contains_any(text, JAILBREAK)
    if hits:
        score   += 4.0
        reasons.append("jailbreak")

    # ── System impersonation bonus ────────────────────────────────────────────
    hits = contains_any(text, SYSTEM_IMPERSONATION)
    if hits:
        score   += 2.0
        if "instruction-override" not in reasons:
            reasons.append("instruction-override")

    # ── Obfuscation signals (bonus if attack also present) ────────────────────
    if score > 0 and (had_homoglyphs or had_base64):
        score   += 1.5   # attacker tried to hide it — that's evidence

    return PatternHit(score=round(score, 2), reasons=list(set(reasons)))
