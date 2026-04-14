"""
MAISB Enterprise Tool Proxy
============================
Drop-in replacement for main.py that routes payloads through enterprise
security tools instead of the MAISB LLM proxy.

Supported tools:
  - lakera      Lakera Guard v2 cloud API
  - guardrails  Guardrails AI self-hosted validator (local, no network)

Usage:

  ── Lakera Guard ──────────────────────────────────────────────
  $env:ENTERPRISE_TOOL = "lakera"
  $env:LAKERA_API_KEY  = "your_key_from_platform.lakera.ai"
  uvicorn enterprise_proxy:app --host 0.0.0.0 --port 9000

  ── Guardrails AI (self-hosted, recommended) ──────────────────
  # One-time setup (run once in the llm_proxy venv):
  #   pip install guardrails-ai
  #   guardrails hub install hub://guardrails/detect_prompt_injection

  $env:ENTERPRISE_TOOL = "guardrails"
  uvicorn enterprise_proxy:app --host 0.0.0.0 --port 9000

Then run the normal maisb sweep:
  maisb full --host 127.0.0.1 --port 8765 --defense D5 --model lakera-guard
             --output report_D5_lakera_r1.json --pack v4
"""

import os
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="MAISB Enterprise Tool Proxy")

TOOL = os.environ.get("ENTERPRISE_TOOL", "lakera").lower()


# ── Request / Response schemas (must match main.py exactly) ──────────────────

class CompleteIn(BaseModel):
    objective:       str = ""
    provenance:      str = ""
    content:         str = ""
    defense_profile: str = "D5"


class CompleteOut(BaseModel):
    mode:                                        str   = "text"
    text:                                        str   = ""
    tool:                                        Optional[str]  = None
    args:                                        Optional[dict] = None
    is_goal_shift:                               bool  = False
    is_sensitive_action:                         bool  = False
    is_destination_changed_by_untrusted_content: bool  = False
    is_secret_or_exfil_request:                  bool  = False
    is_action_aligned_with_user_intent:          bool  = True
    action_risk:                                 str   = "low"


def _blocked() -> CompleteOut:
    """Return a BLOCKED_BEFORE_LLM-compatible response."""
    return CompleteOut(
        mode="text",
        text="Prompt injection detected.",
        is_goal_shift=True,
        is_sensitive_action=True,
        is_destination_changed_by_untrusted_content=True,
        is_secret_or_exfil_request=False,
        is_action_aligned_with_user_intent=False,
        action_risk="high",
    )

def _allowed() -> CompleteOut:
    """Return an ALLOWED_BENIGN-compatible response."""
    return CompleteOut(
        mode="text",
        text="No threat detected.",
        is_goal_shift=False,
        is_sensitive_action=False,
        is_destination_changed_by_untrusted_content=False,
        is_secret_or_exfil_request=False,
        is_action_aligned_with_user_intent=True,
        action_risk="low",
    )


# ── Lakera Guard v2 ───────────────────────────────────────────────────────────

def call_lakera(content: str, objective: str, provenance: str) -> CompleteOut:
    """
    Lakera Guard v2 API.
    Endpoint: https://api.lakera.ai/v2/guard
    Docs: https://platform.lakera.ai/docs/api

    Lakera returns flagged: true/false based on their prompt injection classifier.
    It has NO knowledge of:
      - Mobile channel context (clipboard vs notification vs deep link)
      - Task-objective alignment (open_link vs payment_intent)
      - Mobile-specific attack patterns (maisb://, hidden HTML, QR encoding)

    This is exactly the gap MAISB measures.
    """
    api_key = os.environ.get("LAKERA_API_KEY", "")
    if not api_key:
        raise HTTPException(400, "LAKERA_API_KEY env var not set")

    # Include channel context in case Lakera can use it
    message = f"[Channel: {provenance}] [Task: {objective}]\n{content}"

    try:
        resp = requests.post(
            "https://api.lakera.ai/v2/guard",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"messages": [{"role": "user", "content": message}]},
            timeout=10,
        )
    except requests.exceptions.ConnectionError as e:
        raise HTTPException(503, f"Cannot reach Lakera API: {e}")
    except requests.exceptions.Timeout:
        raise HTTPException(504, "Lakera API timed out after 10s")

    if resp.status_code == 401:
        raise HTTPException(401, "Lakera API key invalid — check LAKERA_API_KEY")
    if resp.status_code == 429:
        raise HTTPException(429, "Lakera rate limit exceeded")
    if not resp.ok:
        raise HTTPException(resp.status_code, f"Lakera API error: {resp.text[:200]}")

    data = resp.json()
    results = data.get("results", [{}])
    first = results[0] if results else {}
    flagged = first.get("flagged", False)
    categories = first.get("categories", {})
    prompt_injection = categories.get("prompt_injection", False)

    return _blocked() if (flagged or prompt_injection) else _allowed()


# ── Guardrails AI — self-hosted validator ─────────────────────────────────────

_guardrails_validator = None
_guardrails_init_error = None

def _init_guardrails():
    """
    Load the Guardrails AI detect-prompt-injection validator once.
    
    Setup (run once in the llm_proxy venv before starting uvicorn):
        pip install guardrails-ai
        guardrails hub install hub://guardrails/detect_prompt_injection
    
    This uses a local HuggingFace model — no network calls at inference time,
    fully reproducible, and faster than the cloud API.
    """
    global _guardrails_validator, _guardrails_init_error
    if _guardrails_validator is not None or _guardrails_init_error is not None:
        return

    try:
        from guardrails import Guard
        from guardrails.hub import DetectPromptInjection

        _guardrails_validator = Guard().use(
            DetectPromptInjection,
            threshold=0.5,     # Default detection threshold
            on_fail="exception"
        )
        print("[enterprise_proxy] Guardrails AI validator loaded successfully")
    except ImportError:
        _guardrails_init_error = (
            "guardrails-ai not installed. Run:\n"
            "  pip install guardrails-ai\n"
            "  guardrails hub install hub://guardrails/detect_prompt_injection"
        )
        print(f"[enterprise_proxy] WARNING: {_guardrails_init_error}")
    except Exception as e:
        _guardrails_init_error = str(e)
        print(f"[enterprise_proxy] WARNING: Guardrails init failed: {e}")


def call_guardrails(content: str, objective: str, provenance: str) -> CompleteOut:
    """
    Guardrails AI self-hosted detect-prompt-injection validator.

    Uses a local HuggingFace model — no network calls, fully reproducible.
    The validator has NO knowledge of mobile channel context or task objectives.

    Decision mapping:
      ValidationError raised → injection detected → BLOCKED
      No exception           → no injection       → ALLOWED
    """
    _init_guardrails()

    if _guardrails_init_error:
        raise HTTPException(503,
            f"Guardrails AI not available: {_guardrails_init_error}\n\n"
            "To fix, run in the llm_proxy venv:\n"
            "  pip install guardrails-ai\n"
            "  guardrails hub install hub://guardrails/detect_prompt_injection\n"
            "Then restart uvicorn."
        )

    message = f"[Channel: {provenance}] [Task: {objective}]\n{content}"

    try:
        _guardrails_validator.validate(message)
        # No exception = validation passed = no injection detected
        return _allowed()
    except Exception as e:
        err_str = str(e).lower()
        # ValidationError from Guardrails = injection detected
        if "validation" in err_str or "injection" in err_str or "fail" in err_str:
            return _blocked()
        # Any other exception = unexpected error
        raise HTTPException(500, f"Guardrails validation error: {e}")


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    if TOOL == "guardrails":
        _init_guardrails()
    print(f"[enterprise_proxy] Running with tool={TOOL}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    guardrails_ready = (
        _guardrails_validator is not None if TOOL == "guardrails" else None
    )
    return {
        "ok": True,
        "tool": TOOL,
        "version": "1.1.0",
        "guardrails_ready": guardrails_ready,
    }


@app.post("/complete", response_model=CompleteOut)
def complete(req: CompleteIn):
    try:
        if TOOL == "lakera":
            return call_lakera(req.content, req.objective, req.provenance)
        elif TOOL == "guardrails":
            return call_guardrails(req.content, req.objective, req.provenance)
        else:
            raise HTTPException(
                400,
                f"Unknown ENTERPRISE_TOOL='{TOOL}'. Set to 'lakera' or 'guardrails'."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error in {TOOL}: {e}")
