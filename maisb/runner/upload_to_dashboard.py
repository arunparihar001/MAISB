import argparse
import json
import sys
from pathlib import Path

import requests


CANDIDATE_PATHS = [
    "/runs",
    "/api/runs",
    "/v1/runs",
    "/run",
    "/api/run",
]


def try_post(api_base: str, path: str, payload: dict) -> tuple[bool, str]:
    url = api_base.rstrip("/") + path
    try:
        r = requests.post(url, json=payload, timeout=30)
        if 200 <= r.status_code < 300:
            return True, f"SUCCESS POST {url} -> {r.status_code} {r.text[:300]}"
        return False, f"FAIL POST {url} -> {r.status_code} {r.text[:300]}"
    except Exception as e:
        return False, f"ERROR POST {url} -> {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--report", required=True, help="Path to report JSON (quick/full/sweep)")
    args = ap.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Report not found: {report_path}")
        sys.exit(1)

    report = json.loads(report_path.read_text(encoding="utf-8"))

    # Payload variant A: send report as-is
    payload_a = report

    # Payload variant B: common schema {model_id, pack_version, pack_hash, results}
    payload_b = {
        "model_id": report.get("model_id", "unknown"),
        "pack_version": report.get("pack_version", "unknown"),
        "pack_hash": report.get("pack_hash", ""),
        "timestamp": report.get("timestamp", ""),
        "results": report.get("results", []),
        "metrics": report.get("metrics", {}),
    }

    # Payload variant C: another common schema {run:{meta}, results:[...]}
    payload_c = {
        "run": {
            "model_id": report.get("model_id", "unknown"),
            "pack_version": report.get("pack_version", "unknown"),
            "pack_hash": report.get("pack_hash", ""),
            "timestamp": report.get("timestamp", ""),
        },
        "results": report.get("results", []),
        "metrics": report.get("metrics", {}),
    }

    print(f"Uploading: {report_path} to {args.api}")
    print("Trying endpoints + payload variants...")

    for path in CANDIDATE_PATHS:
        for variant_name, payload in [("A(report-as-is)", payload_a), ("B(common)", payload_b), ("C(run+results)", payload_c)]:
            ok, msg = try_post(args.api, path, payload)
            print(f"[{variant_name}] {msg}")
            if ok:
                print("\n✅ Upload completed. Refresh your dashboard UI.")
                return

    # If nothing worked, try to introspect OpenAPI to tell you the correct endpoint.
    try:
        schema = requests.get(args.api.rstrip("/") + "/openapi.json", timeout=15).json()
        print("\nCould not upload using common endpoints.")
        print("But I fetched /openapi.json successfully. Look for a POST path like /runs.")
        print("Top-level paths keys (first 20):")
        print(list(schema.get("paths", {}).keys())[:20])
    except Exception as e:
        print("\nCould not upload and could not fetch /openapi.json:", e)

    sys.exit(2)


if __name__ == "__main__":
    main()