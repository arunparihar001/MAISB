"""
Policy and rule models
"""
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, ForeignKey
from maisb.core.models import Base
from datetime import datetime

class Policy(Base):
    """
    Security policy for a tenant
    Defines rules, thresholds, and restrictions
    """
    __tablename__ = "policies"
    
    policy_id = Column(String(255), primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    version = Column(Integer, default=1)
    
    # Rules: List of condition->action mappings
    rules = Column(JSON, default=[], nullable=True)
    
    # Channel-specific thresholds
    # Example: {
    #   "clipboard": {"block_threshold": 0.8, "review_threshold": 0.5},
    #   "qr_code": {"block_threshold": 0.7, "review_threshold": 0.4}
    # }
    channel_rules = Column(JSON, default={}, nullable=True)
    
    # Objective restrictions
    # Example: {
    #   "payment_intent": {"blocked": True},
    #   "data_exfiltration": {"blocked": True}
    # }
    objective_restrictions = Column(JSON, default={}, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Policy {self.policy_id}>"
    
    def to_dict(self):
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "version": self.version,
            "rules": self.rules,
            "channel_rules": self.channel_rules,
            "objective_restrictions": self.objective_restrictions,
            "is_active": self.is_active
        }

class PolicyVersion(Base):
    """
    Version history of policies
    """
    __tablename__ = "policy_versions"
    
    version_id = Column(String(255), primary_key=True, index=True)
    policy_id = Column(String(255), ForeignKey("policies.policy_id"), nullable=False)
    version = Column(Integer, nullable=False)
    
    rules = Column(JSON, nullable=True)
    channel_rules = Column(JSON, nullable=True)
    objective_restrictions = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<PolicyVersion {self.policy_id} v{self.version}>"
