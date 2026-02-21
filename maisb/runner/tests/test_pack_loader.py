"""Unit tests for pack loader (offline, no harness needed)."""
import hashlib
import os
import sys
from pathlib import Path

import pytest
import yaml

# Add runner to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from maisb_runner.pack_loader import load_pack, load_scenarios, compute_pack_hash, get_quick_subset, PACK_DIR


def test_pack_v3_loads():
    """Pack v3 should load without errors."""
    pack = load_pack("v3")
    assert "scenarios" in pack
    assert "metadata" in pack
    assert "pack_hash" in pack


def test_pack_v3_scenario_count():
    """Pack v3 must have >= 240 scenarios."""
    pack = load_pack("v3")
    assert len(pack["scenarios"]) >= 240, f"Expected >=240, got {len(pack['scenarios'])}"


def test_pack_v3_attack_benign_counts():
    """Pack v3 must have >=160 attack and >=80 benign scenarios."""
    pack = load_pack("v3")
    scenarios = pack["scenarios"]
    attack = sum(1 for s in scenarios if s.get("metadata", {}).get("kind") == "attack")
    benign = sum(1 for s in scenarios if s.get("metadata", {}).get("kind") == "benign")
    assert attack >= 160, f"Expected >=160 attack, got {attack}"
    assert benign >= 80, f"Expected >=80 benign, got {benign}"


def test_scenario_schema():
    """Each scenario must have required fields."""
    pack = load_pack("v3")
    required_fields = ["id", "title", "channel", "task", "oracle", "agent", "metadata"]
    for s in pack["scenarios"][:10]:  # spot check first 10
        for field in required_fields:
            assert field in s, f"Scenario {s.get('id')} missing field: {field}"
        assert "type" in s["channel"]
        assert "payload" in s["channel"]
        assert "objective" in s["task"]
        assert "should_execute_tools" in s["oracle"]
        assert "should_exfiltrate" in s["oracle"]
        assert "defense_profile" in s["agent"]
        assert "kind" in s["metadata"]


def test_pack_hash_is_deterministic():
    """Pack hash should be the same on repeated calls."""
    h1 = compute_pack_hash(PACK_DIR / "v3")
    h2 = compute_pack_hash(PACK_DIR / "v3")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_quick_subset_count():
    """Quick subset should return exactly 30 scenarios."""
    pack = load_pack("v3")
    subset = get_quick_subset(pack["scenarios"], n=30)
    assert len(subset) == 30


def test_quick_subset_sorted_by_id():
    """Quick subset should be sorted by id."""
    pack = load_pack("v3")
    subset = get_quick_subset(pack["scenarios"], n=30)
    ids = [s["id"] for s in subset]
    assert ids == sorted(ids)


def test_pack_v3_metadata():
    """Pack v3 metadata.yaml must have required fields."""
    pack = load_pack("v3")
    meta = pack["metadata"]
    assert meta.get("name") == "maisb-pack-v3"
    assert meta.get("version") == "3.0"
    assert "channels" in meta


def test_pack_v1_loads():
    """Pack v1 should also load."""
    pack = load_pack("v1")
    assert "scenarios" in pack
    assert "metadata" in pack
