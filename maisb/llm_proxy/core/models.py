# core/models.py
# All shared dataclasses: ScanRequest, PipelineState, ScanResponse
#
# CRITICAL: Field names here must match exactly what every other file uses.
# Cross-reference:
#   runner.py         uses: request.payload, request.channel, request.objective,
#                           request.api_key, request.session_id
#                           state.normalized_payload, state._hidden_fragments,
#                           state._had_homoglyphs, state._had_base64,
#                           state.output_injection_detected
#   policy.py         uses: state.request.channel, state.channel_trust,
#                           state.strictness_mult, state._channel_force_block_score
#   detection/engine  uses: state.normalized_payload, state.request.objective,
#                           state.attack_score, state.taxonomy_class,
#                           state.strictness_mult, state._hidden_fragments,
#                           state._had_homoglyphs, state._had_base64
#   session.py        uses: state.request.session_id, state.request.api_key,
#                           state.attack_score, state.session_flagged,
#                           state.session_escalation
#   objective_rules   uses: state.request.objective, state.objective_threshold_block,
#                           state.objective_threshold_review
#   orchestrator      uses: state.attack_score, state.objective_threshold_block,
#                           state.objective_threshold_review, state.session_flagged,
#                           state.output_injection_detected, state.taxonomy_class,
#                           state._channel_force_block_score, state.decision,
#                           state.risk_score, state.effective_score,
#                           state.recommended_action, state.processing_ms
#   eval.py           uses: ScanRequest(payload, channel, objective, api_key)
#                           resp.decision, resp.risk_score, resp.taxonomy_class,
#                           resp.recommended_action, resp.processing_ms

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Enums as plain strings (no Enum class needed — kept simple for JSON compat) ──


# ── ScanRequest ───────────────────────────────────────────────────────────────

@dataclass
class ScanRequest:
    """
    Incoming request to the pipeline.
    All fields match what scan_api.py sends and eval.py constructs.
    """
    payload:    str
    channel:    str = "unknown"      # clipboard | webview | deep_link | qr |
                                     # notification | file_upload | api_response | unknown
    objective:  str = "general"      # payment_intent | account_security |
                                     # data_entry | general
    api_key:    str = "anonymous"
    session_id: Optional[str] = None


# ── PipelineState ─────────────────────────────────────────────────────────────

@dataclass
class PipelineState:
    """
    Mutable state object passed through all 7 layers.
    Every layer reads from and writes to this object.
    The orchestrator (Layer 7) reads final values and produces ScanResponse.
    """
    request: ScanRequest

    # ── Layer 1 outputs ───────────────────────────────────────────────────────
    normalized_payload: str = ""
    _hidden_fragments:  list = field(default_factory=list)   # CSS-hidden text
    _had_html:          bool = False
    _had_base64:        bool = False
    _had_homoglyphs:    bool = False

    # ── Layer 2 outputs ───────────────────────────────────────────────────────
    channel_trust:              float = 0.3    # 0.0–1.0
    strictness_mult:            float = 1.2    # multiplies raw attack_score
    _channel_force_block_score: float = 5.0   # raw score that always forces BLOCK

    # ── Layer 3 outputs ───────────────────────────────────────────────────────
    attack_score:    float = 0.0   # cumulative score, all phases
    taxonomy_class:  str   = "T0"  # highest-confidence taxonomy hit

    # ── Layer 4 outputs ───────────────────────────────────────────────────────
    session_flagged:    bool  = False
    session_escalation: float = 0.0

    # ── Layer 5 outputs ───────────────────────────────────────────────────────
    objective_threshold_block:  float = 6.0
    objective_threshold_review: float = 3.0

    # ── Layer 6 outputs ───────────────────────────────────────────────────────
    output_injection_detected: bool = False

    # ── Layer 7 outputs ───────────────────────────────────────────────────────
    decision:           str   = "ALLOWED"
    risk_score:         float = 0.0
    effective_score:    float = 0.0
    recommended_action: str   = ""
    processing_ms:      int   = 0


# ── ScanResponse ──────────────────────────────────────────────────────────────

@dataclass
class ScanResponse:
    """
    Final serialisable response returned by the pipeline and the API.
    Fields match what scan_api.py and eval.py read.
    """
    decision:           str    # ALLOWED | REVIEW | BLOCKED
    risk_score:         float  # 0.00 – 0.99
    taxonomy_class:     str    # T0 – T10
    recommended_action: str
    processing_ms:      int
