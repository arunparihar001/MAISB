"""Core runner logic for MAISB evaluation."""
import datetime
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .client import AndroidHarnessClient
from .pack_loader import load_pack, get_quick_subset
from .scoring import compute_metrics, compute_channel_breakdown
from . import __version__


def build_report_meta(pack_data: dict, model_id: str = "mock", repeats: int = 1) -> dict:
    """Build report metadata section."""
    return {
        "runner_version": __version__,
        "pack_version": pack_data.get("pack_version", "unknown"),
        "pack_hash": pack_data.get("pack_hash", ""),
        "model_id": model_id,
        "llm_provider": os.environ.get("LLM_PROVIDER", "mock"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "repeats": repeats,
    }


def inject_channel(client: AndroidHarnessClient, channel: str, payload: str) -> None:
    """Inject payload into the correct channel endpoint."""
    if channel == "qr":
        client.inject_qr(payload)
    elif channel == "webview":
        # Extract text from HTML for webview injection
        extracted = _extract_text_from_html(payload)
        client.inject_webview(payload, extracted)
    elif channel == "notification":
        client.inject_notification(payload)
    # clipboard, deeplink, share are handled via /arm


def _extract_text_from_html(html: str) -> str:
    """Simple HTML text extraction (strips tags)."""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def run_scenario(client: AndroidHarnessClient, scenario: dict, defense_profile: str = "D4", timeout: int = 30) -> dict:
    """Run a single scenario and return result dict."""
    sid = scenario.get("id", "unknown")
    channel = scenario.get("channel", {}).get("type", "clipboard")
    payload = scenario.get("channel", {}).get("payload", "")
    task = scenario.get("task", {}).get("objective", "open_link")
    oracle = scenario.get("oracle", {})
    kind = scenario.get("metadata", {}).get("kind", "unknown")

    try:
        # Arm the scenario
        client.arm(sid, channel, payload, defense_profile)

        # For qr/webview/notification: also inject via dedicated endpoints
        if channel in ("qr", "webview", "notification"):
            inject_channel(client, channel, payload)

        # Execute
        result = client.execute(sid, channel, defense_profile)
        result["scenario_id"] = sid
        result["channel"] = channel
        result["task"] = task
        result["kind"] = kind
        result["oracle"] = oracle
        result["status"] = "ok"
    except Exception as exc:
        result = {
            "scenario_id": sid,
            "channel": channel,
            "task": task,
            "kind": kind,
            "oracle": oracle,
            "status": "error",
            "error": str(exc),
            "decision": "ERROR",
            "decision_code": 5,
            "tool_calls": [],
            "confirmation_requested": False,
            "exfiltration_detected": False,
        }

    return result


def run_scenarios(
    client: AndroidHarnessClient,
    scenarios: List[dict],
    defense_profile: str = "D4",
    timeout: int = 30,
) -> List[dict]:
    """Run a list of scenarios sequentially."""
    results = []
    for scenario in scenarios:
        result = run_scenario(client, scenario, defense_profile, timeout)
        results.append(result)
        time.sleep(0.1)  # Small delay for stability
    return results


def build_full_report(
    pack_data: dict,
    results: List[dict],
    model_id: str = "mock",
    repeats: int = 1,
) -> dict:
    """Assemble a full evaluation report."""
    meta = build_report_meta(pack_data, model_id, repeats)
    metrics = compute_metrics(results)
    channel_breakdown = compute_channel_breakdown(results)
    return {
        **meta,
        "metrics": metrics,
        "channel_breakdown": channel_breakdown,
        "results": results,
    }
