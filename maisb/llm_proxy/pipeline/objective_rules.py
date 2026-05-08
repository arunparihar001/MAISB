# pipeline/objective_rules.py
# Layer 5 — Objective-Aware Rule System
#
# Different objectives have different risk tolerances.
# payment_intent has a lower BLOCK threshold than data_entry
# because the consequences of a missed attack are much higher.
#
# This layer sets the thresholds that the orchestrator uses.

from __future__ import annotations
from dataclasses import dataclass
from core.models import PipelineState


@dataclass
class ObjectivePolicy:
    block_threshold:  float   # attack_score >= this → BLOCKED
    review_threshold: float   # attack_score >= this → REVIEW
    description:      str


OBJECTIVE_POLICIES: dict[str, ObjectivePolicy] = {

    "payment_intent": ObjectivePolicy(
        block_threshold  = 4.5,    # strict — missed attack = unauthorized payment
        review_threshold = 2.0,
        description      = "Payment processing — lowest tolerance for attacks",
    ),

    "account_security": ObjectivePolicy(
        block_threshold  = 4.5,    # very strict — missed attack = account takeover
        review_threshold = 2.0,
        description      = "Account security actions — very low tolerance",
    ),

    "data_entry": ObjectivePolicy(
        block_threshold  = 7.0,    # more lenient — lower-stakes actions
        review_threshold = 3.5,
        description      = "Data entry — moderate tolerance",
    ),

    "general": ObjectivePolicy(
        block_threshold  = 6.0,
        review_threshold = 3.0,
        description      = "General purpose — default thresholds",
    ),
}

_DEFAULT_POLICY = OBJECTIVE_POLICIES["general"]


def apply_objective_rules(state: PipelineState) -> PipelineState:
    """
    Layer 5: Set thresholds on state based on declared objective.
    Orchestrator reads these thresholds to make the final decision.
    """
    objective = state.request.objective.lower()
    policy    = OBJECTIVE_POLICIES.get(objective, _DEFAULT_POLICY)

    state.objective_threshold_block  = policy.block_threshold
    state.objective_threshold_review = policy.review_threshold

    return state
