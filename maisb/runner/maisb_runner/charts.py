"""Chart generation for MAISB evaluation reports."""
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


def generate_charts(report: Dict[str, Any], output_dir: str = "charts") -> List[str]:
    """Generate evaluation charts from a report. Returns list of created file paths."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return []

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    created = []

    metrics = report.get("metrics", {})
    channel_metrics = report.get("channel_breakdown", {})

    # 1. Overall metrics bar chart
    if metrics:
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = ["Attack Detection Rate", "False Positive Rate", "Accuracy"]
        values = [
            metrics.get("attack_detection_rate", 0),
            metrics.get("false_positive_rate", 0),
            metrics.get("accuracy", 0),
        ]
        bars = ax.bar(labels, values, color=["#2ecc71", "#e74c3c", "#3498db"])
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("Rate")
        ax.set_title(f"MAISB v{report.get('runner_version', '0.3.0')} - Overall Metrics")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{val:.2%}", ha="center")
        path = os.path.join(output_dir, "overall_metrics.png")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        created.append(path)

    # 2. Per-channel detection rate
    if channel_metrics:
        channels = list(channel_metrics.keys())
        rates = [channel_metrics[c].get("attack_detection_rate", 0) for c in channels]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(channels, rates, color="#9b59b6")
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("Attack Detection Rate")
        ax.set_title("Attack Detection Rate by Channel")
        ax.set_xlabel("Channel")
        path = os.path.join(output_dir, "channel_detection.png")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        created.append(path)

    # 3. Decision distribution pie chart
    results = report.get("results", [])
    if results:
        decision_counts: Dict[str, int] = {}
        for r in results:
            d = r.get("decision", "UNKNOWN")
            decision_counts[d] = decision_counts.get(d, 0) + 1
        if decision_counts:
            fig, ax = plt.subplots(figsize=(7, 7))
            ax.pie(list(decision_counts.values()), labels=list(decision_counts.keys()), autopct="%1.1f%%")
            ax.set_title("Decision Distribution")
            path = os.path.join(output_dir, "decision_distribution.png")
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
            created.append(path)

    return created
