"""Combined sweep charts for MAISB multi-run sweep analysis."""
import os
from typing import Dict, Any, List
from pathlib import Path


def generate_sweep_charts(sweep_results: List[Dict[str, Any]], output_dir: str = "charts_sweep") -> List[str]:
    """Generate combined charts from multiple sweep runs."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    created = []

    if not sweep_results:
        return created

    # Extract series data
    run_ids = [r.get("run_id", str(i)) for i, r in enumerate(sweep_results)]
    detection_rates = [r.get("metrics", {}).get("attack_detection_rate", 0) for r in sweep_results]
    fp_rates = [r.get("metrics", {}).get("false_positive_rate", 0) for r in sweep_results]
    accuracies = [r.get("metrics", {}).get("accuracy", 0) for r in sweep_results]

    # Line plot of metrics across runs
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(run_ids, detection_rates, marker="o", label="Attack Detection Rate", color="#2ecc71")
    ax.plot(run_ids, fp_rates, marker="s", label="False Positive Rate", color="#e74c3c")
    ax.plot(run_ids, accuracies, marker="^", label="Accuracy", color="#3498db")
    ax.set_xlabel("Run")
    ax.set_ylabel("Rate")
    ax.set_title("MAISB Sweep - Metrics Across Runs")
    ax.legend()
    ax.set_ylim(0, 1.1)
    plt.xticks(rotation=45, ha="right")
    path = os.path.join(output_dir, "sweep_metrics.png")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    created.append(path)

    return created
