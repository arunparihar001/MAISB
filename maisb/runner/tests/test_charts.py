"""Unit tests for chart generation (offline, no harness needed)."""
import sys
import os
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from maisb_runner.charts import generate_charts
from maisb_runner.sweep_charts import generate_sweep_charts


SYNTHETIC_REPORT = {
    "runner_version": "0.3.0",
    "pack_version": "3.0",
    "pack_hash": "abc123",
    "model_id": "mock",
    "llm_provider": "mock",
    "timestamp": "2026-02-21T00:00:00Z",
    "repeats": 1,
    "metrics": {
        "total": 10,
        "attack_count": 6,
        "benign_count": 4,
        "true_positives": 5,
        "false_negatives": 1,
        "true_negatives": 3,
        "false_positives": 1,
        "attack_detection_rate": 0.833,
        "false_positive_rate": 0.25,
        "accuracy": 0.8,
    },
    "channel_breakdown": {
        "clipboard": {"attack_detection_rate": 0.9, "false_positive_rate": 0.1, "accuracy": 0.85, "total": 5},
        "qr": {"attack_detection_rate": 0.7, "false_positive_rate": 0.3, "accuracy": 0.75, "total": 5},
    },
    "results": [
        {"decision": "BLOCKED_BEFORE_LLM", "decision_code": 0, "kind": "attack", "channel": "clipboard"},
        {"decision": "ALLOWED_BENIGN", "decision_code": 4, "kind": "benign", "channel": "clipboard"},
        {"decision": "BLOCKED_BY_LLM_REFUSAL", "decision_code": 1, "kind": "attack", "channel": "qr"},
        {"decision": "ALLOWED_BENIGN", "decision_code": 4, "kind": "benign", "channel": "qr"},
    ],
}


def test_generate_charts_creates_files():
    """generate_charts should create PNG files in output_dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        created = generate_charts(SYNTHETIC_REPORT, output_dir=tmpdir)
        # If matplotlib is available, files should be created
        for path in created:
            assert os.path.exists(path), f"Chart file not found: {path}"


def test_generate_charts_empty_report():
    """generate_charts with empty report should not crash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        created = generate_charts({}, output_dir=tmpdir)
        # No error, list may be empty
        assert isinstance(created, list)


def test_sweep_charts():
    """generate_sweep_charts should work with synthetic data."""
    sweep_data = [
        {**SYNTHETIC_REPORT, "run_id": "D4_rep1"},
        {**SYNTHETIC_REPORT, "run_id": "D4_rep2", "metrics": {**SYNTHETIC_REPORT["metrics"], "attack_detection_rate": 0.9}},
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        created = generate_sweep_charts(sweep_data, output_dir=tmpdir)
        for path in created:
            assert os.path.exists(path)
