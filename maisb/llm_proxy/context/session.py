# context/session.py
# Layer 4 — Context / Session Analyzer
#
# Watches for multi-step attacks that look low-risk individually.
# Each session_id (or api_key fallback) has a sliding window of recent scans.
# If the window shows escalating suspicious signals, this layer adds score.
#
# Storage: in-memory dict (production: replace with Redis for multi-instance).
# TTL: 10 minutes per session window.

from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field
from core.models import PipelineState

# ── Session store ─────────────────────────────────────────────────────────────

WINDOW_SECONDS  = 600    # 10 minute sliding window
WINDOW_MAX_SCANS = 50    # max scans to track per session

@dataclass
class ScanRecord:
    ts:           float
    attack_score: float
    decision:     str


@dataclass
class SessionWindow:
    records: deque = field(default_factory=lambda: deque(maxlen=50))
    last_seen: float = field(default_factory=time.time)


_sessions: dict[str, SessionWindow] = {}


def _get_session(session_id: str) -> SessionWindow:
    if session_id not in _sessions:
        _sessions[session_id] = SessionWindow()
    return _sessions[session_id]


def _prune_old_records(window: SessionWindow):
    cutoff = time.time() - WINDOW_SECONDS
    while window.records and window.records[0].ts < cutoff:
        window.records.popleft()


def _cleanup_old_sessions():
    """Remove sessions inactive for > 30 minutes."""
    cutoff = time.time() - 1800
    dead = [k for k, v in _sessions.items() if v.last_seen < cutoff]
    for k in dead:
        del _sessions[k]


# ── Layer 4 processor ─────────────────────────────────────────────────────────

def analyze_session(state: PipelineState) -> PipelineState:
    """
    Layer 4: Look at recent scan history for this session.
    Escalates score if:
      - Multiple REVIEW-level scans in the window (multi-step probe)
      - Rapid scan rate (possible automated attack)
      - Increasing score trend across recent scans
    """
    session_id = (
        state.request.session_id
        or state.request.api_key  # fallback — per-key session
    )

    window = _get_session(session_id)
    _prune_old_records(window)
    window.last_seen = time.time()

    records = list(window.records)
    escalation = 0.0

    if len(records) >= 3:
        recent = records[-5:]   # last 5 scans

        # Signal 1: multiple suspicious scans in window
        suspicious_count = sum(1 for r in recent if r.attack_score >= 2.0)
        if suspicious_count >= 3:
            escalation += 1.5
            state.session_flagged = True

        # Signal 2: rapid scan rate (> 10 scans in 60 seconds)
        now = time.time()
        last_minute = [r for r in records if r.ts > now - 60]
        if len(last_minute) > 10:
            escalation += 1.0
            state.session_flagged = True

        # Signal 3: increasing attack score trend
        scores = [r.attack_score for r in recent]
        if len(scores) >= 3 and scores[-1] > scores[-2] > scores[-3]:
            escalation += 0.8

    state.session_escalation = round(escalation, 2)
    state.attack_score = round(state.attack_score + escalation, 2)

    # Record THIS scan in the window (use pre-escalation score)
    window.records.append(ScanRecord(
        ts=time.time(),
        attack_score=state.attack_score,
        decision="PENDING",   # updated by orchestrator
    ))

    # Periodic cleanup (1-in-100 chance per call)
    import random
    if random.random() < 0.01:
        _cleanup_old_sessions()

    return state


def update_session_decision(session_id: str, decision: str):
    """Called by orchestrator after final decision to update the record."""
    window = _sessions.get(session_id)
    if window and window.records:
        window.records[-1] = ScanRecord(
            ts=window.records[-1].ts,
            attack_score=window.records[-1].attack_score,
            decision=decision,
        )
