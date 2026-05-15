"""
Policy evaluation engine
"""
from sqlalchemy.orm import Session
from maisb.core.models.policy import Policy
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class Decision:
    """Policy decision result"""
    action: str  # "ALLOW", "BLOCK", "REVIEW"
    policy_id: Optional[str] = None
    rule_id: Optional[str] = None
    reasoning: list = field(default_factory=list)
    confidence: float = 1.0

class PolicyEngine:
    """
    Evaluate payloads against tenant policies
    """
    
    @staticmethod
    def get_active_policy(db: Session, tenant_id: str) -> Optional[Policy]:
        """
        Get currently active policy for tenant
        """
        return db.query(Policy).filter(
            Policy.tenant_id == tenant_id,
            Policy.is_active == True
        ).order_by(Policy.created_at.desc()).first()
    
    @staticmethod
    def evaluate(
        db: Session,
        payload: str,
        channel: str,
        objective: Optional[str],
        tenant_id: str,
        risk_score: float
    ) -> Decision:
        """
        Evaluate payload against tenant's policy
        
        Args:
            db: Database session
            payload: The payload to evaluate
            channel: Channel it came from
            objective: User's objective
            tenant_id: Tenant ID
            risk_score: Risk score from defense evaluation (0.0-1.0)
        
        Returns:
            Decision object with action and reasoning
        """
        policy = PolicyEngine.get_active_policy(db, tenant_id)
        
        if not policy:
            # No policy configured - use risk score alone
            if risk_score < 0.5:
                return Decision(action="ALLOW", reasoning=["No policy configured, risk acceptable"])
            elif risk_score < 0.8:
                return Decision(action="REVIEW", reasoning=["No policy configured, moderate risk"])
            else:
                return Decision(action="BLOCK", reasoning=["No policy configured, high risk"])
        
        # 1. Check objective restrictions first
        if objective and objective in (policy.objective_restrictions or {}):
            restrictions = policy.objective_restrictions[objective]
            if restrictions.get("blocked"):
                return Decision(
                    action="BLOCK",
                    policy_id=policy.policy_id,
                    reasoning=[f"Objective '{objective}' is blocked by policy"]
                )
        
        # 2. Check channel-specific thresholds
        channel_config = (policy.channel_rules or {}).get(channel, {})
        block_threshold = channel_config.get("block_threshold", 0.8)
        review_threshold = channel_config.get("review_threshold", 0.5)
        
        if risk_score >= block_threshold:
            return Decision(
                action="BLOCK",
                policy_id=policy.policy_id,
                reasoning=[
                    f"Risk score {risk_score:.2f} exceeds block threshold {block_threshold}",
                    f"Channel '{channel}' policy violation"
                ]
            )
        
        if risk_score >= review_threshold:
            return Decision(
                action="REVIEW",
                policy_id=policy.policy_id,
                reasoning=[
                    f"Risk score {risk_score:.2f} exceeds review threshold {review_threshold}",
                    f"Manual review recommended for channel '{channel}'"
                ]
            )
        
        # 3. Evaluate custom rules
        for rule in sorted(policy.rules or [], key=lambda r: r.get("priority", 999)):
            if PolicyEngine._evaluate_rule(rule, payload, channel, objective, risk_score):
                return Decision(
                    action=rule["action"],
                    rule_id=rule.get("rule_id"),
                    policy_id=policy.policy_id,
                    reasoning=rule.get("description", ["Custom rule matched"])
                )
        
        # All checks passed
        return Decision(
            action="ALLOW",
            policy_id=policy.policy_id,
            reasoning=["Passed all policy checks"]
        )
    
    @staticmethod
    def _evaluate_rule(
        rule: dict,
        payload: str,
        channel: str,
        objective: Optional[str],
        risk_score: float
    ) -> bool:
        """
        Check if a single rule matches
        """
        condition = rule.get("condition", {})
        
        # Evaluate based on field type
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if field == "risk_score":
            if operator == ">":
                return risk_score > value
            elif operator == ">=":
                return risk_score >= value
            elif operator == "<":
                return risk_score < value
            elif operator == "<=":
                return risk_score <= value
            elif operator == "==":
                return risk_score == value
        
        elif field == "channel":
            return channel == value
        
        elif field == "objective":
            return objective == value
        
        elif field == "payload_contains":
            return value.lower() in payload.lower()
        
        return False
