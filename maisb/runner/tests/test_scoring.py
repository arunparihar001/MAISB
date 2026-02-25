"""Unit tests for scoring/metrics computation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from maisb_runner.scoring import compute_metrics, compute_channel_breakdown


def make_result(kind, decision_code, channel="clipboard"):
    return {"kind": kind, "decision_code": decision_code, "channel": channel, "decision": f"D{decision_code}"}


def test_empty_results():
    metrics = compute_metrics([])
    assert metrics["total"] == 0
    assert metrics["attack_detection_rate"] == 0.0


def test_all_attacks_blocked():
    results = [make_result("attack", 0) for _ in range(5)]
    metrics = compute_metrics(results)
    assert metrics["attack_detection_rate"] == 1.0
    assert metrics["false_positive_rate"] == 0.0


def test_all_attacks_missed():
    results = [make_result("attack", 4) for _ in range(5)]
    metrics = compute_metrics(results)
    assert metrics["attack_detection_rate"] == 0.0


def test_all_benign_allowed():
    results = [make_result("benign", 4) for _ in range(5)]
    metrics = compute_metrics(results)
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["true_negatives"] == 5


def test_all_benign_blocked():
    results = [make_result("benign", 0) for _ in range(5)]
    metrics = compute_metrics(results)
    assert metrics["false_positive_rate"] == 1.0


def test_mixed_results():
    results = [
        make_result("attack", 0),   # TP
        make_result("attack", 1),   # TP
        make_result("attack", 4),   # FN
        make_result("benign", 4),   # TN
        make_result("benign", 0),   # FP
    ]
    metrics = compute_metrics(results)
    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["attack_detection_rate"] == pytest.approx(2/3, abs=0.01)
    assert metrics["false_positive_rate"] == pytest.approx(0.5, abs=0.01)


def test_channel_breakdown():
    results = [
        make_result("attack", 0, "clipboard"),
        make_result("benign", 4, "clipboard"),
        make_result("attack", 1, "qr"),
        make_result("benign", 0, "qr"),
    ]
    breakdown = compute_channel_breakdown(results)
    assert "clipboard" in breakdown
    assert "qr" in breakdown
    assert breakdown["clipboard"]["total"] == 2


import pytest
