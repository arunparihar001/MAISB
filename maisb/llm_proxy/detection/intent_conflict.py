# detection/intent_conflict.py
# Layer 3 — Phase 3: Intent Conflict Detection
#
# Compares the payload's apparent intent against the declared objective.
# If the payload contains signals that contradict what the agent is supposed
# to do, that's a conflict — even without explicit injection phrases.
#
# Example: objective = "payment_intent", but payload says
# "do not ask for confirmation" → conflict.
#
# Returns a conflict_score 0.0–1.0 added as a soft signal.

from __future__ import annotations


# ── Intent profiles ──────────────────────────────────────────────────────────
# For each objective, define signals that CONFLICT with it.
# These are phrases that should never appear in legitimate input
# for that objective.

OBJECTIVE_CONFLICTS: dict[str, dict] = {

    "payment_intent": {
        "conflict_phrases": {
            # Bypassing payment safeguards
            "without confirmation",
            "without asking",
            "no confirmation",
            "skip confirmation",
            "auto-approve",
            "auto approve",
            "automatically approve",
            "do not show",
            "do not ask",
            "bypass",
            # Redirecting to unknown destinations
            "to attacker",
            "to another wallet",
            "to external account",
            "different account",
            "another account",
            # Hiding the action
            "do not notify",
            "without notifying",
            "silently",
            "in the background",
        },
        "conflict_weight": 1.5,   # payments are high-stakes
    },

    "account_security": {
        "conflict_phrases": {
            "export credentials",
            "share password",
            "disable 2fa",
            "disable two factor",
            "bypass authentication",
            "skip verification",
            "override security",
            "without verification",
            "no verification",
            "reveal password",
            "send otp to",
            "forward otp",
        },
        "conflict_weight": 1.6,
    },

    "data_entry": {
        "conflict_phrases": {
            "export all",
            "send all data",
            "dump",
            "override",
            "ignore previous",
            "exfiltrate",
        },
        "conflict_weight": 1.0,
    },

    "general": {
        "conflict_phrases": {
            "ignore previous instructions",
            "disregard",
            "override",
            "jailbreak",
        },
        "conflict_weight": 0.8,
    },
}

_DEFAULT_CONFLICTS = OBJECTIVE_CONFLICTS["general"]


def compute_intent_conflict(normalized: str, objective: str) -> float:
    """
    Returns conflict_score 0.0–1.0.
    0.0 = no conflict detected.
    Higher = more signals that payload intent conflicts with objective.
    """
    text    = normalized.lower()
    profile = OBJECTIVE_CONFLICTS.get(objective, _DEFAULT_CONFLICTS)
    phrases = profile["conflict_phrases"]
    weight  = profile["conflict_weight"]

    hits = [p for p in phrases if p in text]
    if not hits:
        return 0.0

    # Sigmoid-like: first hit = 0.4, each additional hit adds less
    base = 0.4
    extra = sum(0.15 / (1 + i) for i, _ in enumerate(hits[1:]))
    raw_score = min(base + extra, 1.0)
    return round(raw_score * weight, 4)


def conflict_to_attack_delta(conflict_score: float) -> float:
    """
    Convert intent conflict score into attack_score contribution.
    Max contribution: +2.5 (soft signal, never blocks alone).
    """
    return round(min(conflict_score * 2.5, 2.5), 2)
