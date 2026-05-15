"""Risk factor explanations for MAISB Phase 2."""
from typing import Any, Dict


class RiskExplainer:
    """Describe risk score components in clear terms."""

    def explain_risk(self, risk_factors: Dict[str, Any]) -> Dict[str, Any]:
        pipeline_risk = float(risk_factors.get("pipeline_risk", 0.0))
        trust_degradation = float(risk_factors.get("trust_degradation", 0.0))
        return {
            "pipeline_risk": pipeline_risk,
            "trust_degradation": trust_degradation,
            "risk_level": self.level(max(pipeline_risk, trust_degradation)),
            "summary": "Risk combines prompt/policy risk with cross-channel trust degradation.",
        }

    def level(self, value: float) -> str:
        if value >= 0.80:
            return "critical"
        if value >= 0.50:
            return "high"
        if value >= 0.25:
            return "medium"
        return "low"
