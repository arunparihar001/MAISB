import argparse
import json
from pathlib import Path
import requests

def req(method, url, payload=None):
    r = requests.request(method, url, json=payload, timeout=30)
    return r.status_code, r.text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--report", required=True)
    ap.add_argument("--name", default="", help="Optional name in dashboard (default: filename)")
    args = ap.parse_args()

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    name = args.name.strip() or report_path.stem  # e.g. report_full
    api = args.api.rstrip("/")

    # Try PUT /reports/{name} with report JSON as body
    url_put = f"{api}/reports/{name}"
    sc, txt = req("PUT", url_put, report)
    if 200 <= sc < 300:
        print(f"✅ Uploaded via PUT {url_put} ({sc})")
        return

    # Try POST /reports with common body shapes
    url_post = f"{api}/reports"
    variants = [
        {"name": name, "report": report},
        {"name": name, "data": report},
        {"name": name, "content": report},
        {"name": name, "json": report},
    ]
    for v in variants:
        sc, txt = req("POST", url_post, v)
        if 200 <= sc < 300:
            print(f"✅ Uploaded via POST {url_post} ({sc}) using keys: {list(v.keys())}")
            return

    print("❌ Upload failed.")
    print("PUT status/text:", sc, txt[:300])
    # Also show available endpoints quickly
    try:
        schema = requests.get(f"{api}/openapi.json", timeout=15).json()
        methods = []
        for p, ops in schema.get("paths", {}).items():
            for m in ops.keys():
                methods.append((m.upper(), p))
        methods = sorted(set(methods))
        print("\nAvailable API routes (method path):")
        for m, p in methods:
            print(m, p)
    except Exception as e:
        print("Could not fetch openapi.json:", e)

if __name__ == "__main__":
    main()