"""
Phase 2 Cross-Channel Trace Engine.
This modular version mirrors the deployed self-contained API implementation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import secrets


def utcnow() -> str:
    return datetime.utcnow().isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def generate_trace_id() -> str:
    return f"trace_{secrets.token_hex(8)}"


@dataclass
class TraceStep:
    channel: str
    timestamp: str
    payload_hash: str
    transform: str = "none"
    trust_score: float = 0.5
    risk_score: float = 0.0
    decision: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelTraceRecord:
    trace_id: str
    tenant_id: str
    source_channel: str
    source_hash: str
    journey: List[TraceStep] = field(default_factory=list)
    trust_degradation: List[Dict[str, Any]] = field(default_factory=list)
    final_risk_score: float = 0.0
    detection_layer: Optional[str] = None


class TraceEngine:
    """Build trace records for payload movement across channels."""

    def start_trace(self, tenant_id: str, payload: str, channel: str, trust_score: float = 0.5, risk_score: float = 0.0, decision: Optional[str] = None) -> ChannelTraceRecord:
        payload_hash = sha256_text(payload)
        step = TraceStep(
            channel=channel,
            timestamp=utcnow(),
            payload_hash=payload_hash,
            transform="none",
            trust_score=trust_score,
            risk_score=risk_score,
            decision=decision,
        )
        return ChannelTraceRecord(
            trace_id=generate_trace_id(),
            tenant_id=tenant_id,
            source_channel=channel,
            source_hash=payload_hash,
            journey=[step],
            final_risk_score=risk_score,
            detection_layer=channel if decision == "BLOCKED" else None,
        )

    def extend_trace(self, trace: ChannelTraceRecord, payload: str, channel: str, transform: str, trust_score: float, risk_score: float, decision: Optional[str] = None) -> ChannelTraceRecord:
        step = TraceStep(
            channel=channel,
            timestamp=utcnow(),
            payload_hash=sha256_text(payload),
            transform=transform,
            trust_score=trust_score,
            risk_score=risk_score,
            decision=decision,
        )
        trace.journey.append(step)
        trace.final_risk_score = max(trace.final_risk_score, risk_score)
        if decision == "BLOCKED":
            trace.detection_layer = channel
        return trace
