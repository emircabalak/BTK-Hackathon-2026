"""Gemini wrapper with mock fallback.

Design:
- Real mode (MOCK_MODE=false + GEMINI_API_KEY set): call google-genai SDK.
- Mock mode: each caller provides a `mock_fallback` callable that returns
  the same JSON shape the real model would. This lets us exercise the full
  agent loop deterministically without any API.

The wrapper is sync-first for the CLI test runner, with an async variant
for FastAPI endpoints.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.config import get_settings

log = logging.getLogger(__name__)

# Disk cache for live Gemini responses. Saves quota while iterating on
# prompts — same (system, messages, tier, temperature) returns the cached
# response. Opt-in via LLM_CACHE=1 env var. Set LLM_CACHE_BUST=1 to ignore.
_CACHE_DIR = Path(__file__).resolve().parent.parent / ".llm_cache"


def _cache_enabled() -> bool:
    return os.getenv("LLM_CACHE", "1") not in {"0", "false", "False"}


def _cache_bust() -> bool:
    return os.getenv("LLM_CACHE_BUST", "0") in {"1", "true", "True"}


def _cache_key(*, system: str, messages: list, tier: str, temperature: float, mode: str) -> str:
    payload = json.dumps(
        {
            "s": system,
            "m": [(m.role, m.content) for m in messages],
            "t": tier,
            "temp": round(temperature, 3),
            "mode": mode,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _cache_get(key: str) -> Any:
    if not _cache_enabled() or _cache_bust():
        return None
    path = _CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _cache_put(key: str, value: Any) -> None:
    if not _cache_enabled():
        return
    _CACHE_DIR.mkdir(exist_ok=True)
    path = _CACHE_DIR / f"{key}.json"
    try:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        log.warning("LLM cache write failed for %s", key)


@dataclass
class Message:
    role: Literal["user", "model", "system"]
    content: str


ModelTier = Literal["fast", "pro", "vision"]

MockFallback = Callable[[str, list[Message]], dict]
"""(system_prompt, messages) -> JSON-shaped response dict."""


_client_cache: Any = None


def _get_client():
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY env var not set. Either set it or use MOCK_MODE=true."
        )
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError(
            "google-genai not installed. Run: pip install google-genai"
        ) from e
    _client_cache = genai.Client(api_key=settings.gemini_api_key)
    return _client_cache


def _resolve_model(tier: ModelTier) -> str:
    settings = get_settings()
    return {
        "fast": settings.gemini_model_fast,
        "pro": settings.gemini_model_pro,
        "vision": settings.gemini_model_vision,
    }[tier]


def chat_json(
    *,
    system: str,
    messages: list[Message],
    tier: ModelTier = "fast",
    temperature: float = 0.7,
    mock_fallback: MockFallback | None = None,
) -> dict:
    """Send a chat completion and parse the response as JSON.

    Always returns a dict. In mock mode, calls `mock_fallback`.
    """
    settings = get_settings()

    if settings.mock_mode:
        if mock_fallback is None:
            raise RuntimeError(
                "MOCK_MODE=true but no mock_fallback provided for this call."
            )
        result = mock_fallback(system, messages)
        log.debug("mock response: %s", result)
        return result

    cache_key = _cache_key(
        system=system, messages=messages, tier=tier, temperature=temperature, mode="json"
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        log.debug("LLM cache hit %s", cache_key)
        return cached

    client = _get_client()
    from google.genai import types  # local import keeps SDK optional

    contents = []
    for msg in messages:
        if msg.role == "system":
            continue  # we use system_instruction
        gemini_role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=gemini_role, parts=[types.Part(text=msg.content)]))

    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        temperature=temperature,
    )
    response = client.models.generate_content(
        model=_resolve_model(tier),
        contents=contents,
        config=config,
    )
    text = response.text or "{}"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        log.warning("Gemini returned non-JSON, attempting recovery: %s", text[:200])
        parsed = _try_recover_json(text)
    _cache_put(cache_key, parsed)
    return parsed


def _try_recover_json(text: str) -> dict:
    """Best-effort: find first {...} block."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {"_raw": text, "_parse_error": True}


def chat_text(
    *,
    system: str,
    messages: list[Message],
    tier: ModelTier = "fast",
    temperature: float = 0.7,
    mock_fallback: Callable[[str, list[Message]], str] | None = None,
) -> str:
    """Plain-text response variant. Used by Decider for headline/explanation."""
    settings = get_settings()
    if settings.mock_mode:
        if mock_fallback is None:
            raise RuntimeError("MOCK_MODE=true but no mock_fallback provided.")
        return mock_fallback(system, messages)

    cache_key = _cache_key(
        system=system, messages=messages, tier=tier, temperature=temperature, mode="text"
    )
    cached = _cache_get(cache_key)
    if isinstance(cached, dict) and "_text" in cached:
        return cached["_text"]

    client = _get_client()
    from google.genai import types

    contents = []
    for msg in messages:
        gemini_role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=gemini_role, parts=[types.Part(text=msg.content)]))

    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
    )
    response = client.models.generate_content(
        model=_resolve_model(tier),
        contents=contents,
        config=config,
    )
    text = response.text or ""
    _cache_put(cache_key, {"_text": text})
    return text
