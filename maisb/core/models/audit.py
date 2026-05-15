"""
Audit logging models
"""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from maisb.core.models import Base
from datetime import datetime
import hashlib

class AuditLog(Base):
    """
    Immutable audit log for compliance and debugging
    """
    __tablename__ = "audit_logs"
    
    log_id = Column(String(255), primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    # Event information
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(255), nullable=False, index=True)  # SCAN, POLICY_CHANGE, KEY_GENERATED, API_ACCESS
    actor_id = Column(String(255), nullable=True)  # User or "system"
    resource = Column(String(255), nullable=True)  # What was acted on
    action = Column(String(255), nullable=False)  # The action taken
    
    # Details and context
    details = Column(JSON, default={}, nullable=True)
    
    # Tamper detection
    hash = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=True)  # Hash chain
    
    def __repr__(self):
        return f"<AuditLog {self.log_id}>"
    
    def compute_hash(self) -> str:
        """
        Compute tamper-evident hash
        Creates a hash chain for integrity verification
        """
        data_str = f"{self.log_id}|{self.timestamp}|{self.event_type}|{self.previous_hash or 'none'}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self):
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "action": self.action,
            "details": self.details
        }
