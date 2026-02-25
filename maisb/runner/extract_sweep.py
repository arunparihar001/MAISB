import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


def normalize_profiles(data):
    """
    Returns dict: defense_profile -> metrics dict
    Supports:
    - dict with metrics_by_profile (dict)
    - dict with profiles (dict or list)
    - list of profile objects
    """
    if isinstance(data, dict):
        if isinstance(data.get("metrics_by_profile"), dict):
            return data["metrics_by_profile"]
        profs = data.get("profiles")
        if isinstance(profs, dict):
            return profs
        if isinstance(profs, list):
            out = {}
            for item in profs:
                if not isinstance(item, dict):
                    continue
                key = item.get("defense") or item.get("profile") or item.get("defense_profile") or item.get("name")
                metrics = item.get("metrics") or item
                if key:
                    out[str(key)] = metrics
            return out
        # fallback: maybe it's already keyed somewhere else
        return {}

    if isinstance(data, list):
        out = {}
        for item in data:
            if not isinstance(item, dict):
                continue
            key = item.get("defense") or item.get("profile") or item.get("defense_profile") or item.get("name")
            metrics = item.get("metrics") or item
            if key:
                out[str(key)] = metrics
        return out

    return {}


def pick(m, *keys, default=0.0):
    for k in keys:
        if k in m:
            return m[k]
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Path to report_sweep.json")
    ap.add_argument("--csv", default="reports_sweep/sweep_metrics.csv", help="CSV output path")
    ap.add_argument("--plotdir", default="charts_sweep", help="Directory for plots")
    args = ap.parse_args()

    data = json.loads(Path(args.infile).read_text(encoding="utf-8"))
    profiles = normalize_profiles(data)

    if not profiles:
        raise SystemExit("Could not find profile metrics in this sweep file.")

    # sort profiles D0..D5
    order = sorted(profiles.keys(), key=lambda x: int(x.replace("D", "")) if x.startswith("D") else x)

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["defense", "attack_detection_rate", "false_positive_rate", "accuracy", "attack_count", "benign_count"])
        for p in order:
            m = profiles[p]
            dr = float(pick(m, "attack_detection_rate", "detection_rate", default=0.0))
            fpr = float(pick(m, "false_positive_rate", default=0.0))
            acc = float(pick(m, "accuracy", default=0.0))
            att = int(pick(m, "attack_count", default=0))
            ben = int(pick(m, "benign_count", default=0))
            w.writerow([p, dr, fpr, acc, att, ben])

    print("Wrote CSV:", csv_path)

    # Plots
    plot_dir = Path(args.plotdir)
    plot_dir.mkdir(parents=True, exist_ok=True)

    drs, fprs, accs = [], [], []
    for p in order:
        m = profiles[p]
        drs.append(float(pick(m, "attack_detection_rate", "detection_rate", default=0.0)))
        fprs.append(float(pick(m, "false_positive_rate", default=0.0)))
        accs.append(float(pick(m, "accuracy", default=0.0)))

    def save_bar(vals, title, ylabel, filename):
        plt.figure()
        plt.title(title)
        plt.xlabel("Defense")
        plt.ylabel(ylabel)
        plt.bar(order, vals)
        out = plot_dir / filename
        plt.tight_layout()
        plt.savefig(out, dpi=200)
        plt.close()
        print("Saved plot:", out)

    save_bar(drs, "Attack Detection Rate vs Defense", "Detection rate", "detection_vs_defense.png")
    save_bar(fprs, "False Positive Rate vs Defense", "False positive rate", "fpr_vs_defense.png")
    save_bar(accs, "Accuracy vs Defense", "Accuracy", "accuracy_vs_defense.png")


if __name__ == "__main__":
    main()