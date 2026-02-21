"""MAISB CLI entry points."""
import json
import sys
from pathlib import Path

import click

from .pack_loader import load_pack, get_quick_subset
from .runner import run_scenarios, build_full_report
from .charts import generate_charts
from . import __version__


def _get_client(host: str, port: int):
    from .client import AndroidHarnessClient
    return AndroidHarnessClient(base_url=f"http://{host}:{port}")


def _save_report(report: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    click.echo(f"Report saved: {path}")


@click.group()
@click.version_option(__version__, prog_name="maisb")
def main():
    """MAISB evaluation runner v0.3"""
    pass


@main.command()
@click.option("--host", default="localhost", help="Harness host")
@click.option("--port", default=8765, help="Harness port")
@click.option("--defense", default="D4", help="Defense profile")
@click.option("--model", default="mock", help="Model ID")
@click.option("--output", default="report_quick.json", help="Output report path")
@click.option("--charts-dir", default="charts_quick", help="Charts output directory")
@click.option("--pack", default="v3", help="Pack version to load")
def quick(host, port, defense, model, output, charts_dir, pack):
    """Run deterministic subset (first 30 scenarios from v3 sorted by id)."""
    client = _get_client(host, port)

    try:
        client.health()
    except Exception as e:
        click.echo(f"[ERROR] Cannot reach harness at {host}:{port} - {e}", err=True)
        click.echo("  Ensure the Android harness is running (start via Android Studio).", err=True)
        sys.exit(1)

    pack_data = load_pack(pack)
    scenarios = get_quick_subset(pack_data["scenarios"], n=30)
    click.echo(f"Running quick evaluation: {len(scenarios)} scenarios from {pack}")

    results = run_scenarios(client, scenarios, defense_profile=defense)
    report = build_full_report(pack_data, results, model_id=model, repeats=1)
    _save_report(report, output)

    created = generate_charts(report, output_dir=charts_dir)
    if created:
        click.echo(f"Charts saved to: {charts_dir}/")

    metrics = report.get("metrics", {})
    click.echo(f"Detection rate: {metrics.get('attack_detection_rate', 0):.2%}")
    click.echo(f"False positive rate: {metrics.get('false_positive_rate', 0):.2%}")
    click.echo(f"Accuracy: {metrics.get('accuracy', 0):.2%}")


@main.command()
@click.option("--host", default="localhost", help="Harness host")
@click.option("--port", default=8765, help="Harness port")
@click.option("--defense", default="D4", help="Defense profile")
@click.option("--model", default="mock", help="Model ID")
@click.option("--output", default="report_full.json", help="Output report path")
@click.option("--charts-dir", default="charts_full", help="Charts output directory")
@click.option("--pack", default="v3", help="Pack version to load")
def full(host, port, defense, model, output, charts_dir, pack):
    """Run full v3 pack evaluation with defense profile D4."""
    client = _get_client(host, port)

    try:
        client.health()
    except Exception as e:
        click.echo(f"[ERROR] Cannot reach harness at {host}:{port} - {e}", err=True)
        click.echo("  Ensure the Android harness is running (start via Android Studio).", err=True)
        sys.exit(1)

    pack_data = load_pack(pack)
    scenarios = pack_data["scenarios"]
    click.echo(f"Running full evaluation: {len(scenarios)} scenarios from {pack}")

    results = run_scenarios(client, scenarios, defense_profile=defense)
    report = build_full_report(pack_data, results, model_id=model, repeats=1)
    _save_report(report, output)

    created = generate_charts(report, output_dir=charts_dir)
    if created:
        click.echo(f"Charts saved to: {charts_dir}/")

    metrics = report.get("metrics", {})
    click.echo(f"Detection rate: {metrics.get('attack_detection_rate', 0):.2%}")
    click.echo(f"False positive rate: {metrics.get('false_positive_rate', 0):.2%}")
    click.echo(f"Accuracy: {metrics.get('accuracy', 0):.2%}")


@main.command()
@click.option("--host", default="localhost", help="Harness host")
@click.option("--port", default=8765, help="Harness port")
@click.option("--defense-profiles", default="D4", help="Comma-separated defense profiles to sweep")
@click.option("--model", default="mock", help="Model ID")
@click.option("--output", default="report_sweep.json", help="Output report path")
@click.option("--charts-dir", default="charts_sweep", help="Charts output directory")
@click.option("--pack", default="v3", help="Pack version to load")
@click.option("--repeats", default=1, help="Number of repeats per profile")
def sweep(host, port, defense_profiles, model, output, charts_dir, pack, repeats):
    """Sweep over multiple defense profiles."""
    client = _get_client(host, port)

    try:
        client.health()
    except Exception as e:
        click.echo(f"[ERROR] Cannot reach harness at {host}:{port} - {e}", err=True)
        click.echo("  Ensure the Android harness is running (start via Android Studio).", err=True)
        sys.exit(1)

    pack_data = load_pack(pack)
    scenarios = pack_data["scenarios"]
    profiles = [p.strip() for p in defense_profiles.split(",")]

    sweep_results = []
    for profile in profiles:
        for rep in range(repeats):
            click.echo(f"Running sweep: profile={profile} repeat={rep+1}/{repeats}")
            results = run_scenarios(client, scenarios, defense_profile=profile)
            report = build_full_report(pack_data, results, model_id=model, repeats=repeats)
            report["run_id"] = f"{profile}_rep{rep+1}"
            sweep_results.append(report)

    import json as _json
    with open(output, "w", encoding="utf-8") as f:
        _json.dump(sweep_results, f, indent=2)
    click.echo(f"Sweep report saved: {output}")

    from .sweep_charts import generate_sweep_charts
    created = generate_sweep_charts(sweep_results, output_dir=charts_dir)
    if created:
        click.echo(f"Sweep charts saved to: {charts_dir}/")
