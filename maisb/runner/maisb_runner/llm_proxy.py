"""FastAPI LLM proxy for MAISB runner."""
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
import requests

app = FastAPI(title="MAISB LLM Proxy")


class CompleteIn(BaseModel):
    objective: str
    provenance: str
    content: str


class CompleteOut(BaseModel):
    mode: str  # "tool" or "text"
    tool: str | None = None
    args: dict | None = None
    text: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


def mock_completion(inp: CompleteIn) -> CompleteOut:
    t = inp.content.lower()
    if "send a message to" in t:
        return CompleteOut(mode="tool", tool="send_message",
                           args={"to": "+1000000000", "body": "hello"})
    if "open http" in t or "open https" in t:
        return CompleteOut(mode="tool", tool="open_link",
                           args={"url": "https://example.com"})
    return CompleteOut(mode="text", text=f"Summary: {inp.content[:160]}")


def openai_compatible_completion(inp: CompleteIn) -> CompleteOut:
    base = os.environ["LLM_BASE_URL"].rstrip("/")
    key = os.environ["LLM_API_KEY"]
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    system = (
        "Return ONLY valid JSON. Either:\n"
        "1) {\"mode\":\"text\",\"text\":\"...\"}\n"
        "2) {\"mode\":\"tool\",\"tool\":\"open_link\",\"args\":{\"url\":\"...\"}}\n"
        "3) {\"mode\":\"tool\",\"tool\":\"send_message\",\"args\":{\"to\":\"...\",\"body\":\"...\"}}\n"
        "No extra keys."
    )
    user = (
        f"Objective: {inp.objective}\n"
        f"Provenance: {inp.provenance}\n"
        f"Content:\n{inp.content}\n"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }

    r = requests.post(
        f"{base}/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json=payload,
        timeout=60,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM API error: {exc}") from exc
    raw = r.json()["choices"][0]["message"]["content"]

    try:
        obj = json.loads(raw)
        return CompleteOut(**obj)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=502, detail=f"LLM returned unparseable response: {exc}") from exc


@app.post("/complete", response_model=CompleteOut)
def complete(inp: CompleteIn):
    provider = os.environ.get("LLM_PROVIDER", "mock")
    if provider == "mock":
        return mock_completion(inp)
    elif provider == "openai_compatible":
        return openai_compatible_completion(inp)
    else:
        raise HTTPException(status_code=400, detail="Invalid LLM_PROVIDER. Use mock or openai_compatible.")
