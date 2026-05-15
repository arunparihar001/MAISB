"""
Tenant model for multi-tenancy
"""
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from maisb.core.models import Base
from datetime import datetime

class Tenant(Base):
    """
    Represents a tenant in the multi-tenant system
    """
    __tablename__ = "tenants"
    
    tenant_id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Configuration and settings
    config = Column(JSON, default={}, nullable=True)
    metadata_retention_days = Column(Integer, default=90)
    max_api_keys = Column(Integer, default=10)
    features_enabled = Column(JSON, default={}, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Tenant {self.tenant_id}>"
    
    def to_dict(self):
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }
