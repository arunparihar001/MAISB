"""Trust degradation calculation for Phase 2 traces."""
from typing import Any, Dict, List

TRANSFORM_RISK = {
    "none": 0.00,
    "copy": 0.02,
    "minor_edit": 0.06,
    "format_conversion": 0.10,
    "ocr": 0.15,
    "context_inject": 0.25,
    "major_rewrite": 0.30,
    "unknown_transform": 0.18,
}


class TrustChainCalculator:
    """Calculate cumulative trust loss through the payload journey."""

    def calculate(self, journey: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        degradation = []
        cumulative = 0.0
        for index, step in enumerate(journey):
            trust_score = float(step.get("trust_score", 0.5))
            transform = step.get("transform", "unknown_transform")
            transform_risk = TRANSFORM_RISK.get(transform, TRANSFORM_RISK["unknown_transform"])
            channel_loss = max(0.0, 1.0 - trust_score)
            step_loss = min(1.0, (channel_loss * 0.35) + transform_risk)
            cumulative = min(1.0, cumulative + step_loss)
            degradation.append({
                "index": index,
                "channel": step.get("channel"),
                "transform": transform,
                "trust_score": round(trust_score, 3),
                "step_loss": round(step_loss, 3),
                "cumulative_loss": round(cumulative, 3),
            })
        return degradation
