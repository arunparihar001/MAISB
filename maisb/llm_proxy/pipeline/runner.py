# pipeline/runner.py
# Full pipeline runner — connects all 7 layers in order.
#
# Usage:
#   from pipeline.runner import run_pipeline
#   response = run_pipeline(ScanRequest(...))

from __future__ import annotations
import time

from core.models import PipelineState, ScanRequest, ScanResponse
from core.normalizer import normalize
from channels.policy import apply_channel_policy
from detection.engine import run_detection
from context.session import analyze_session, update_session_decision
from pipeline.objective_rules import apply_objective_rules
from pipeline.orchestrator import orchestrate


def run_pipeline(request: ScanRequest) -> ScanResponse:
    """
    Execute the full 7-layer MAISB security pipeline.

    Layer 1 — Input normalization
    Layer 2 — Channel policy engine
    Layer 3 — Detection engine (patterns + semantic + intent)
    Layer 4 — Session context analyzer
    Layer 5 — Objective rule system
    Layer 6 — Output validator (called separately after LLM)
    Layer 7 — Decision orchestrator

    Returns ScanResponse ready to serialize to JSON.
    """
    start = time.time()

    # ── Initialise pipeline state ─────────────────────────────────────────────
    state = PipelineState(request=request)

    # ── Layer 1: Normalize ────────────────────────────────────────────────────
    norm_result = normalize(request.payload, request.channel)
    state.normalized_payload = norm_result.normalized
    # Store normalization metadata for detection engine
    state._hidden_fragments = norm_result.hidden_fragments
    state._had_homoglyphs   = norm_result.had_homoglyphs
    state._had_base64       = norm_result.had_base64

    # ── Layer 2: Channel policy ───────────────────────────────────────────────
    state = apply_channel_policy(state)

    # ── Layer 3: Detection ────────────────────────────────────────────────────
    state = run_detection(state)

    # ── Layer 4: Session context ──────────────────────────────────────────────
    state = analyze_session(state)

    # ── Layer 5: Objective thresholds ─────────────────────────────────────────
    state = apply_objective_rules(state)

    # ── Layer 6: Output validation ────────────────────────────────────────────
    # NOTE: Output validation runs separately after your LLM call.
    # See pipeline/output_validator.py → validate_output(llm_response, objective)
    # state.output_injection_detected is False by default.

    # ── Layer 7: Orchestrate final decision ───────────────────────────────────
    response = orchestrate(state, start)

    # Update session record with final decision
    session_id = request.session_id or request.api_key
    update_session_decision(session_id, response.decision)

    return response
