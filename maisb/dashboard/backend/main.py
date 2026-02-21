"""MAISB Dashboard Backend – FastAPI server.

Reads evaluation report JSON files written by the maisb runner and exposes
them via a simple REST API consumed by the dashboard frontend.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("maisb.backend")

app = FastAPI(title="MAISB Dashboard API", version="0.3.0")

# CORS: default to localhost origins suitable for local development.
# Override with a comma-separated list via the CORS_ORIGINS env var.
_raw_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS: List[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/app/reports"))


def _list_report_files() -> List[Path]:
    if not REPORTS_DIR.exists():
        return []
    return sorted(REPORTS_DIR.glob("report_*.json"))


def _load_report(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "version": "0.3.0"}


@app.get("/reports")
def list_reports() -> Dict[str, List[str]]:
    files = _list_report_files()
    return {"reports": [f.name for f in files]}


@app.get("/reports/{name}")
def get_report(name: str) -> Any:
    if "/" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid report name")
    path = REPORTS_DIR / name
    if not path.exists() or path.suffix != ".json":
        raise HTTPException(status_code=404, detail="Report not found")
    return _load_report(path)


@app.get("/metrics/summary")
def metrics_summary() -> Dict[str, List[Dict[str, Any]]]:
    """Return a summary row for every single-run report in REPORTS_DIR."""
    summaries: List[Dict[str, Any]] = []
    for path in _list_report_files():
        try:
            report = _load_report(path)
            # Skip sweep reports (they are a JSON array of run objects)
            if isinstance(report, list):
                continue
            metrics = report.get("metrics", {})
            summaries.append(
                {
                    "name": path.name,
                    "pack_version": report.get("pack_version", ""),
                    "timestamp": report.get("timestamp", ""),
                    "model_id": report.get("model_id", ""),
                    **metrics,
                }
            )
        except Exception as exc:
            logger.warning("Failed to load report %s: %s", path.name, exc)
            continue
    return {"summaries": summaries}
