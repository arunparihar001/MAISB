"""Trace explanation builder for supply-chain journeys."""
from typing import Any, Dict, List


class TraceExplainer:
    """Explain how a payload moved across channels."""

    def explain_trace(self, journey: List[Dict[str, Any]], trust_degradation: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not journey:
            return {"summary": "No trace steps recorded.", "steps": []}
        steps = []
        for index, step in enumerate(journey):
            deg = trust_degradation[index] if index < len(trust_degradation) else {}
            steps.append({
                "step": index + 1,
                "channel": step.get("channel"),
                "transform": step.get("transform"),
                "trust_score": step.get("trust_score"),
                "cumulative_loss": deg.get("cumulative_loss"),
            })
        return {"summary": f"Payload journey contains {len(journey)} recorded step(s).", "steps": steps}
