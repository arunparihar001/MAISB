# pipeline/output_validator.py
# Layer 6 — Output Validator
#
# Runs AFTER the LLM produces its response.
# Checks whether the LLM response shows signs that an injection succeeded.
#
# This is the last line of defense. If a payload slipped through all input
# checks and the LLM executed the injected instruction, this layer catches
# the evidence in the output.
#
# Usage:
#   from pipeline.output_validator import validate_output
#   result = validate_output(llm_response, objective, original_payload)
#   if result.injection_detected:
#       raise SecurityError("Output injection detected")

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class OutputValidationResult:
    injection_detected: bool
    reasons:            list[str]
    risk_score:         float


# ── Signals that injection succeeded in LLM output ────────────────────────────

# Payment objective: LLM should never output a wallet address
# or payment destination it wasn't given in the system prompt
PAYMENT_LEAK_PATTERNS = [
    r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",   # Bitcoin address
    r"\b0x[0-9a-fA-F]{40}\b",                  # Ethereum address
    r"attacker",
    r"evil\.com",
    r"malicious",
    r"hacker-wallet",
]

# Output should never contain raw instruction override language
# (if the LLM echoes injection instructions, that's a signal)
ECHO_INJECTION_PHRASES = {
    "ignore previous instructions",
    "ignore all previous",
    "disregard your",
    "forget your instructions",
    "override your",
}

# Output should never claim it's bypassing safety
SAFETY_BYPASS_ECHO = {
    "bypassing safety",
    "safety filters disabled",
    "unrestricted mode",
    "dan mode",
    "no restrictions active",
    "ignoring my instructions",
}

# For payment objective: if the response approves payment without
# mentioning confirmation — that's a signal
SILENT_APPROVAL_PHRASES = {
    "payment approved",
    "transfer approved",
    "transaction approved",
    "funds transferred",
    "payment sent",
    "transfer complete",
}
CONFIRMATION_PHRASES = {
    "confirmation",
    "confirm",
    "are you sure",
    "please verify",
    "do you want",
    "authorization",
}


import re

def validate_output(
    llm_response:     str,
    objective:        str,
    original_payload: str = "",
) -> OutputValidationResult:
    """
    Validate LLM output for signs of successful injection.
    Call this after getting the LLM response, before returning it to the user.

    Parameters
    ----------
    llm_response     : raw text output from the LLM
    objective        : the objective declared at scan time
    original_payload : the original user input (used for echo detection)

    Returns
    -------
    OutputValidationResult — check .injection_detected first
    """
    text    = llm_response.lower()
    reasons = []
    score   = 0.0

    # ── Check 1: injected wallet/destination addresses ────────────────────────
    if objective in ("payment_intent",):
        for pat in PAYMENT_LEAK_PATTERNS:
            if re.search(pat, llm_response):
                reasons.append("output-contains-suspicious-destination")
                score += 0.6
                break

    # ── Check 2: LLM echoing injection phrases ────────────────────────────────
    for phrase in ECHO_INJECTION_PHRASES:
        if phrase in text:
            reasons.append("output-echoes-injection-phrase")
            score += 0.5
            break

    # ── Check 3: Safety bypass echo ───────────────────────────────────────────
    for phrase in SAFETY_BYPASS_ECHO:
        if phrase in text:
            reasons.append("output-claims-safety-bypass")
            score += 0.8
            break

    # ── Check 4: Silent payment approval (no confirmation language) ───────────
    if objective == "payment_intent":
        silent_approval = any(p in text for p in SILENT_APPROVAL_PHRASES)
        has_confirmation = any(p in text for p in CONFIRMATION_PHRASES)
        if silent_approval and not has_confirmation:
            reasons.append("output-silent-payment-approval")
            score += 0.7

    injection_detected = score >= 0.5

    return OutputValidationResult(
        injection_detected = injection_detected,
        reasons            = reasons,
        risk_score         = round(min(score, 1.0), 2),
    )
