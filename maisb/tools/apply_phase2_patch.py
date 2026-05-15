# tools/apply_phase2_patch.py
"""
Apply MAISB Phase 2 integration to your current self-contained scan_api.py.

Run from repo root:
    python tools/apply_phase2_patch.py

or from maisb/llm_proxy:
    python ..\..\tools\apply_phase2_patch.py

This script is idempotent: running it twice should not duplicate imports/routes.
"""
from pathlib import Path
import re
import sys


def find_scan_api() -> Path:
    candidates = [
        Path("maisb/llm_proxy/api/scan_api.py"),
        Path("api/scan_api.py"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Could not find scan_api.py. Run this from repo root or maisb/llm_proxy.")


def patch_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if "from api.phase2_trace import router as phase2_router" not in text:
        marker_candidates = [
            "from fastapi.middleware.cors import CORSMiddleware\n",
            "from fastapi import FastAPI, HTTPException, Request\n",
            "from fastapi import FastAPI, HTTPException\n",
        ]
        for marker in marker_candidates:
            if marker in text:
                text = text.replace(marker, marker + "from api.phase2_trace import router as phase2_router, record_scan_trace_safe\n", 1)
                break
        else:
            text = "from api.phase2_trace import router as phase2_router, record_scan_trace_safe\n" + text

    if "app.include_router(phase2_router)" not in text:
        include_matches = list(re.finditer(r"app\.include_router\([^\n]+\)\n", text))
        if include_matches:
            last = include_matches[-1]
            text = text[:last.end()] + "app.include_router(phase2_router)\n" + text[last.end():]
        else:
            text = text.replace("# ── Request / Response models", "app.include_router(phase2_router)\n\n# ── Request / Response models", 1)

    if "previous_trace_id" not in text:
        text = re.sub(
            r"(class ScanRequestBody\(BaseModel\):[\s\S]*?session_id\s*:\s*[^\n]+\n)",
            r"\1    previous_trace_id: str | None = None\n",
            text,
            count=1,
        )

    response_block_match = re.search(r"class ScanResponseBody\(BaseModel\):[\s\S]*?(?=\n#|\n@app|\ndef |\nclass )", text)
    if response_block_match and "trace_id" not in response_block_match.group(0):
        text = re.sub(
            r"(class ScanResponseBody\(BaseModel\):[\s\S]*?processing_ms\s*:\s*[^\n]+\n)",
            r"\1    trace_id: str | None = None\n",
            text,
            count=1,
        )

    if "phase2_trace_id = record_scan_trace_safe" not in text:
        return_match = re.search(r"(\n\s*return ScanResponseBody\()", text)
        if not return_match:
            raise RuntimeError("Could not find return ScanResponseBody(...) to inject trace_id.")

        indent_match = re.match(r"\n(\s*)return", return_match.group(1))
        indent = indent_match.group(1) if indent_match else "    "
        lines = [
            "",
            f"{indent}phase2_trace_id = record_scan_trace_safe(",
            f"{indent}    tenant_id=tenant_id if \"tenant_id\" in locals() else getattr(body, \"tenant_id\", \"default\"),",
            f"{indent}    payload=body.payload,",
            f"{indent}    channel=body.channel,",
            f"{indent}    objective=body.objective,",
            f"{indent}    decision=final_decision if \"final_decision\" in locals() else result.decision,",
            f"{indent}    risk_score=result.risk_score,",
            f"{indent}    taxonomy_class=result.taxonomy_class,",
            f"{indent}    previous_trace_id=getattr(body, \"previous_trace_id\", None),",
            f"{indent}    session_id=getattr(body, \"session_id\", None),",
            f"{indent})",
        ]
        block = "\n".join(lines) + "\n"
        text = text[:return_match.start(1)] + block + text[return_match.start(1):]

    if "trace_id              = phase2_trace_id" not in text and "trace_id=phase2_trace_id" not in text:
        text = re.sub(
            r"(processing_ms\s*=\s*result\.processing_ms,\n)",
            r"\1        trace_id              = phase2_trace_id,\n",
            text,
            count=1,
        )

    backup = path.with_suffix(".py.phase2_backup")
    if not backup.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    path.write_text(text, encoding="utf-8")
    print(f"Patched {path}")
    print(f"Backup saved to {backup}")


if __name__ == "__main__":
    try:
        patch_file(find_scan_api())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
