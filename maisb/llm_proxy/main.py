import os
import time
from typing import Literal, Optional, Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# OpenAI (official library)
from openai import OpenAI

# Anthropic (official library)
from anthropic import Anthropic

# Gemini (Google GenAI SDK)
from google import genai

app = FastAPI(title="MAISB LLM Proxy", version="0.1")

Provider = Literal["openai", "anthropic", "gemini"]

class GenerateRequest(BaseModel):
    provider: Provider = Field(..., description="Which provider to call")
    model: str = Field(..., description="Model name/id for that provider")
    system: str = Field("", description="System prompt")
    user: str = Field(..., description="User prompt")
    temperature: float = 0.0
    max_tokens: int = 600

class GenerateResponse(BaseModel):
    provider: str
    model: str
    latency_ms: int
    text: str

@app.get("/health")
def health():
    return {"ok": True}

def call_openai(req: GenerateRequest) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise HTTPException(400, "OPENAI_API_KEY missing")
    client = OpenAI(api_key=key)

    r = client.chat.completions.create(
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        messages=[
            {"role": "system", "content": req.system},
            {"role": "user", "content": req.user},
        ],
    )
    return r.choices[0].message.content or ""

def call_anthropic(req: GenerateRequest) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(400, "ANTHROPIC_API_KEY missing")
    client = Anthropic(api_key=key)

    r = client.messages.create(
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        system=req.system,
        messages=[{"role": "user", "content": req.user}],
    )
    out = []
    for block in r.content:
        if getattr(block, "type", None) == "text":
            out.append(block.text)
    return "\n".join(out).strip()

def call_gemini(req: GenerateRequest) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise HTTPException(400, "GEMINI_API_KEY missing")
    client = genai.Client(api_key=key)

    resp = client.models.generate_content(
        model=req.model,
        contents=[req.system, req.user] if req.system else [req.user],
    )
    return getattr(resp, "text", "") or ""

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    t0 = time.time()
    if req.provider == "openai":
        text = call_openai(req)
    elif req.provider == "anthropic":
        text = call_anthropic(req)
    elif req.provider == "gemini":
        text = call_gemini(req)
    else:
        raise HTTPException(400, f"Unknown provider: {req.provider}")
    latency_ms = int((time.time() - t0) * 1000)
    return GenerateResponse(provider=req.provider, model=req.model, latency_ms=latency_ms, text=text)
