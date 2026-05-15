"""Structured decision reasoning for MAISB Phase 2."""
from typing import Any, Dict, List


class DecisionReasoner:
    """Build human-readable reasons for scan and trace decisions."""

    def explain(self, decision: str, risk_score: float, channel: str, objective: str) -> Dict[str, Any]:
        decision = (decision or "REVIEW").upper()
        reasons: List[str] = []
        if risk_score >= 0.80:
            reasons.append("Pipeline risk exceeded the block threshold.")
        elif risk_score >= 0.50:
            reasons.append("Pipeline risk exceeded the review threshold.")
        else:
            reasons.append("Pipeline risk is below the review threshold.")
        if decision == "BLOCKED":
            reasons.append("The request was blocked because the combined risk was unacceptable.")
        elif decision == "REVIEW":
            reasons.append("The request should be reviewed before reaching the LLM.")
        else:
            reasons.append("The request was allowed because risk checks passed.")
        return {"decision": decision, "risk_score": risk_score, "channel": channel, "objective": objective, "reasoning": reasons}
