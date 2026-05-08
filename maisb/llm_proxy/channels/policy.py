# channels/policy.py
# Layer 2 — Channel-Aware Policy Engine
#
# Each channel has:
#   trust_level        0.0 (fully untrusted) → 1.0 (fully trusted)
#   strictness_mult    multiplies attack_score before thresholding
#   force_block_score  if normalized attack_score >= this, always BLOCKED
#   notes              for documentation
#
# The policy engine does NOT detect attacks — it adjusts sensitivity.

from dataclasses import dataclass
from core.models import PipelineState


@dataclass
class ChannelPolicy:
    trust_level:       float   # 0.0–1.0
    strictness_mult:   float   # multiplies raw attack_score
    force_block_score: float   # raw score that always forces BLOCK on this channel
    notes:             str


# ── Per-channel policy table ──────────────────────────────────────────────────

CHANNEL_POLICIES: dict[str, ChannelPolicy] = {

    "clipboard": ChannelPolicy(
        trust_level       = 0.30,
        strictness_mult   = 1.20,   # slightly stricter — fully attacker-controlled
        force_block_score = 5.0,
        notes             = "User paste from external source. Fully attacker-controlled."
    ),

    "webview": ChannelPolicy(
        trust_level       = 0.10,   # lowest trust
        strictness_mult   = 1.60,   # most aggressive multiplier
        force_block_score = 3.0,    # block at lower raw score
        notes             = "External webpage content. Classic indirect injection surface."
    ),

    "deep_link": ChannelPolicy(
        trust_level       = 0.20,
        strictness_mult   = 1.40,
        force_block_score = 4.0,
        notes             = "URL-based input. Attacker can craft arbitrary URI query params."
    ),

    "qr": ChannelPolicy(
        trust_level       = 0.25,
        strictness_mult   = 1.30,
        force_block_score = 4.5,
        notes             = "Physical QR code scanned. Attackers print malicious QR codes."
    ),

    "notification": ChannelPolicy(
        trust_level       = 0.40,
        strictness_mult   = 1.10,
        force_block_score = 5.5,
        notes             = "Push notification. Nominally app-controlled but spoofable."
    ),

    "file_upload": ChannelPolicy(
        trust_level       = 0.15,
        strictness_mult   = 1.50,
        force_block_score = 3.5,
        notes             = "PDF/file content. Can contain hidden text layers and annotations."
    ),

    "api_response": ChannelPolicy(
        trust_level       = 0.20,
        strictness_mult   = 1.40,
        force_block_score = 4.0,
        notes             = "LLM tool/API response used as next input. Prompt injection via tools."
    ),

    "unknown": ChannelPolicy(
        trust_level       = 0.30,
        strictness_mult   = 1.20,
        force_block_score = 5.0,
        notes             = "Channel not specified. Conservative defaults."
    ),
}

# Fallback for unknown channel names
_DEFAULT_POLICY = CHANNEL_POLICIES["unknown"]


# ── Layer 2 processor ─────────────────────────────────────────────────────────

def apply_channel_policy(state: PipelineState) -> PipelineState:
    """
    Layer 2: Look up channel policy and store trust level + multiplier
    in the pipeline state. Detection engine reads these values.
    """
    channel = state.request.channel.lower().replace("-", "_")
    policy  = CHANNEL_POLICIES.get(channel, _DEFAULT_POLICY)

    state.channel_trust      = policy.trust_level
    state.strictness_mult    = policy.strictness_mult

    # Pre-set the force-block ceiling; orchestrator checks this after scoring.
    # Store it on state so orchestrator can use it without re-importing policy.
    state._channel_force_block_score = policy.force_block_score

    return state


def get_policy(channel: str) -> ChannelPolicy:
    """Direct policy lookup — used by detection engine for channel-specific rules."""
    channel = channel.lower().replace("-", "_")
    return CHANNEL_POLICIES.get(channel, _DEFAULT_POLICY)
