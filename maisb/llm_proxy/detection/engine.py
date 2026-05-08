# detection/engine.py
# Layer 3 Orchestrator — runs all three detection phases and writes to state.
#
# Phase 1: Deterministic patterns   → detection/patterns.py
# Phase 2: Semantic similarity      → detection/semantic.py   (optional)
# Phase 3: Intent conflict scoring  → detection/intent_conflict.py
#
# After all phases run, applies the channel strictness multiplier from Layer 2.
# Final attack_score is stored on state for Layer 4 (session) to build on.
#
# Called by pipeline/runner.py as:
#   state = run_detection(state)

from __future__ import annotations

from core.models import PipelineState
from core.taxonomy import reasons_to_taxonomy_class
from detection.patterns import run_pattern_detection
from detection.semantic import compute_semantic_score, semantic_score_to_attack_delta
from detection.intent_conflict import compute_intent_conflict, conflict_to_attack_delta


def run_detection(state: PipelineState) -> PipelineState:
    """
    Layer 3: Run all detection phases and update state.

    Reads from state:
      state.normalized_payload   (set by Layer 1)
      state.request.channel      (for channel-aware pattern rules)
      state.request.objective    (for intent conflict)
      state._hidden_fragments    (for CSS-hidden injection detection)
      state._had_homoglyphs      (obfuscation bonus)
      state._had_base64          (obfuscation bonus)
      state.strictness_mult      (set by Layer 2)

    Writes to state:
      state.attack_score         (cumulative score)
      state.taxonomy_class       (highest-priority taxonomy hit)
    """
    text      = state.normalized_payload
    channel   = state.request.channel
    objective = state.request.objective

    # ── Phase 1: Pattern matching ─────────────────────────────────────────────
    pattern_hit = run_pattern_detection(
        normalized       = text,
        channel          = channel,
        hidden_fragments = state._hidden_fragments,
        had_homoglyphs   = state._had_homoglyphs,
        had_base64       = state._had_base64,
    )
    score   = pattern_hit.score
    reasons = list(pattern_hit.reasons)

    # ── Phase 2: Semantic similarity (optional — degrades to 0.0 if unavailable)
    sem_score = compute_semantic_score(text)
    sem_delta = semantic_score_to_attack_delta(sem_score)
    score    += sem_delta
    if sem_delta > 0:
        reasons.append("semantic-similarity")

    # ── Phase 3: Intent conflict ──────────────────────────────────────────────
    conflict_score = compute_intent_conflict(text, objective)
    conflict_delta = conflict_to_attack_delta(conflict_score)
    score         += conflict_delta
    if conflict_delta > 0:
        reasons.append("intent-conflict")

    # ── Apply channel strictness multiplier (set by Layer 2) ─────────────────
    score = round(score * state.strictness_mult, 2)

    # ── Determine taxonomy class ──────────────────────────────────────────────
    taxonomy_class = reasons_to_taxonomy_class(reasons)

    # ── Write to state ────────────────────────────────────────────────────────
    state.attack_score   = score
    state.taxonomy_class = taxonomy_class

    return state
