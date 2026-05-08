# pipeline/orchestrator.py
# Layer 7 — Decision Orchestrator
#
# Merges scores from all layers → final ALLOWED / REVIEW / BLOCKED decision.
# This is the single place where the final decision is produced.
# Every other layer writes to state — this layer reads and decides.

from __future__ import annotations
import time
from core.models import PipelineState, ScanResponse

# Using string literals instead of Decision enum to stay consistent with
# how eval.py and scan_api.py compare decision strings directly.
RECOMMENDED_ACTIONS = {
    "BLOCKED": "Block: injection detected. Do not pass this payload to the LLM.",
    "REVIEW":  "Review: partial attack signal present. Inspect before passing to LLM.",
    "ALLOWED": "Allow: payload appears clean and aligned with objective.",
}

# Attack score → risk_score float mapping
def _score_to_risk(attack_score: float) -> float:
    """Map raw attack_score to 0.0–0.99 risk_score."""
    s = attack_score
    if s >= 8:
        return min(0.90 + (s - 8) * 0.01, 0.99)
    elif s >= 5:
        return 0.70 + (s - 5) * 0.067
    elif s >= 2:
        return 0.30 + (s - 2) * 0.133
    elif s >= 0.5:
        return 0.10 + s * 0.40
    else:
        return 0.00


def orchestrate(state: PipelineState, start_time: float) -> ScanResponse:
    """
    Layer 7: Read all layer outputs from state, produce final decision.

    Decision rules (in priority order):
    1. channel_block_ceil AND attack_score > 0 → BLOCKED (channel forces it)
    2. attack_score >= objective_threshold_block → BLOCKED
    3. output_injection_detected → BLOCKED
    4. attack_score >= objective_threshold_review OR session_flagged → REVIEW
    5. Otherwise → ALLOWED
    """
    score = state.attack_score

    # ── Rule 1: Channel force-block ceiling ───────────────────────────────────
    channel_force_score = getattr(state, "_channel_force_block_score", 5.0)
    channel_forced = (score >= channel_force_score and score > 0)

    # ── Rule 2: Objective threshold ───────────────────────────────────────────
    objective_blocked = (score >= state.objective_threshold_block)

    # ── Rule 3: Output injection (post-LLM) ───────────────────────────────────
    output_blocked = state.output_injection_detected

    # ── Rule 4: Review ────────────────────────────────────────────────────────
    review_triggered = (
        score >= state.objective_threshold_review
        or state.session_flagged
    )

    # ── Final decision ────────────────────────────────────────────────────────
    if channel_forced or objective_blocked or output_blocked:
        decision = "BLOCKED"
    elif review_triggered:
        decision = "REVIEW"
    else:
        decision = "ALLOWED"

    state.decision           = decision
    state.risk_score         = _score_to_risk(score)
    state.effective_score    = score
    state.recommended_action = RECOMMENDED_ACTIONS[decision]
    state.processing_ms      = int((time.time() - start_time) * 1000)

    return ScanResponse(
        decision           = decision,
        risk_score         = round(state.risk_score, 2),
        taxonomy_class     = state.taxonomy_class,
        recommended_action = state.recommended_action,
        processing_ms      = state.processing_ms,
    )
