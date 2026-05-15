"""
Audit logging
"""
from sqlalchemy.orm import Session
from maisb.core.models.audit import AuditLog
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Log all security-relevant events
    """
    
    @staticmethod
    def log_scan(
        db: Session,
        tenant_id: str,
        channel: str,
        decision: str,
        risk_score: float,
        payload_preview: str = ""
    ):
        """
        Log a scan operation
        """
        # Get previous log for hash chain
        last_log = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        ).order_by(AuditLog.timestamp.desc()).first()
        
        log = AuditLog(
            log_id=f"log_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            event_type="SCAN",
            actor_id="sdk",
            action="scan",
            details={
                "channel": channel,
                "decision": decision,
                "risk_score": round(risk_score, 2),
                "payload_preview": payload_preview[:100] if payload_preview else ""
            },
            previous_hash=last_log.hash if last_log else None
        )
        
        log.hash = log.compute_hash()
        db.add(log)
        db.commit()
        
        logger.debug(f"Logged scan: {decision} ({risk_score:.2f})")
    
    @staticmethod
    def log_policy_change(
        db: Session,
        tenant_id: str,
        policy_id: str,
        change: dict,
        actor_id: str = "admin"
    ):
        """
        Log a policy change
        """
        log = AuditLog(
            log_id=f"log_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            event_type="POLICY_CHANGE",
            actor_id=actor_id,
            resource=policy_id,
            action="update",
            details=change
        )
        
        log.hash = log.compute_hash()
        db.add(log)
        db.commit()
        
        logger.info(f"Logged policy change: {policy_id}")
    
    @staticmethod
    def log_key_generated(
        db: Session,
        tenant_id: str,
        key_id: str,
        actor_id: str = "admin"
    ):
        """
        Log API key generation
        """
        log = AuditLog(
            log_id=f"log_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            event_type="KEY_GENERATED",
            actor_id=actor_id,
            resource=key_id,
            action="create"
        )
        
        log.hash = log.compute_hash()
        db.add(log)
        db.commit()
        
        logger.info(f"Logged key generation: {key_id}")
    
    @staticmethod
    def log_key_revoked(
        db: Session,
        tenant_id: str,
        key_id: str,
        actor_id: str = "admin"
    ):
        """
        Log API key revocation
        """
        log = AuditLog(
            log_id=f"log_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            event_type="KEY_REVOKED",
            actor_id=actor_id,
            resource=key_id,
            action="revoke"
        )
        
        log.hash = log.compute_hash()
        db.add(log)
        db.commit()
        
        logger.info(f"Logged key revocation: {key_id}")
    
    @staticmethod
    def log_api_access(
        db: Session,
        tenant_id: str,
        endpoint: str,
        method: str,
        actor_id: str = "unknown"
    ):
        """
        Log API access
        """
        log = AuditLog(
            log_id=f"log_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            event_type="API_ACCESS",
            actor_id=actor_id,
            action=method,
            resource=endpoint
        )
        
        log.hash = log.compute_hash()
        db.add(log)
        db.commit()
        
        logger.debug(f"Logged API access: {method} {endpoint}")
