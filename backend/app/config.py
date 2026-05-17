"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
    _ENV_LOADED = True


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model_fast: str
    gemini_model_pro: str
    gemini_model_vision: str
    mock_mode: bool
    scraper_cache_ttl: int
    negotiation_max_turns: int
    negotiation_target_discount_pct: int


def get_settings() -> Settings:
    _ensure_env_loaded()
    api_key = os.getenv("GEMINI_API_KEY") or None
    mock_mode = _bool("MOCK_MODE", default=(api_key is None))
    return Settings(
        gemini_api_key=api_key,
        gemini_model_fast=os.getenv("GEMINI_MODEL_FAST", "gemini-2.5-flash"),
        gemini_model_pro=os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro"),
        gemini_model_vision=os.getenv("GEMINI_MODEL_VISION", "gemini-2.5-flash"),
        mock_mode=mock_mode,
        scraper_cache_ttl=_int("SCRAPER_CACHE_TTL", 3600),
        negotiation_max_turns=_int("NEGOTIATION_MAX_TURNS", 6),
        negotiation_target_discount_pct=_int("NEGOTIATION_TARGET_DISCOUNT_PCT", 15),
    )
