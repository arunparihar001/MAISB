# tools/apply_phase3_patch.py
"""
Apply MAISB Phase 3 Dashboard + Telemetry integration to scan_api.py.

Run from repo root:
    python tools/apply_phase3_patch.py

or from maisb/llm_proxy:
    python ..\..\tools\apply_phase3_patch.py
"""
from pathlib import Path
import re
import sys


def find_scan_api() -> Path:
    candidates = [
        Path("maisb/llm_proxy/api/scan_api.py"),
        Path("api/scan_api.py"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find scan_api.py. Run from repo root or maisb/llm_proxy.")


def patch_scan_api(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if "from api.phase3_dashboard import router as phase3_router" not in text:
        markers = [
            "from api.phase2_trace import",
            "from api.enterprise_routes import",
            "from api.billing import",
            "from fastapi.middleware.cors import CORSMiddleware",
        ]

        inserted = False
        for marker in markers:
            idx = text.find(marker)
            if idx != -1:
                line_end = text.find("\n", idx)
                text = text[:line_end + 1] + "from api.phase3_dashboard import router as phase3_router\n" + text[line_end + 1:]
                inserted = True
                break

        if not inserted:
            text = "from api.phase3_dashboard import router as phase3_router\n" + text

    if "app.include_router(phase3_router)" not in text:
        include_matches = list(re.finditer(r"app\.include_router\([^\n]+\)\n", text))
        if include_matches:
            last = include_matches[-1]
            text = text[:last.end()] + "app.include_router(phase3_router)\n" + text[last.end():]
        else:
            text = text.replace("# ── Request / Response models", "app.include_router(phase3_router)\n\n# ── Request / Response models", 1)

    # Update public version labels from 2.2.0 to 2.3.0 in scan_api.py only.
    # This keeps Phase 2 data/features but marks the API as Phase 3-enabled.
    text = text.replace("2.2.0", "2.3.0")

    # Add phase3 flag to simple health responses where possible.
    if '"phase3"' not in text and "'phase3'" not in text:
        text = text.replace('"phase2": True', '"phase2": True, "phase3": True')
        text = text.replace("'phase2': True", "'phase2': True, 'phase3': True")

    backup = path.with_suffix(".py.phase3_backup")
    if not backup.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    path.write_text(text, encoding="utf-8")
    print(f"Patched {path}")
    print(f"Backup saved to {backup}")


if __name__ == "__main__":
    try:
        patch_scan_api(find_scan_api())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
