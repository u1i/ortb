"""Configuration loading via .env or environment variables."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env if present
# Attempt to load .env from the repository root (one level above this package)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class Settings:  # pylint: disable=too-few-public-methods
    """Singleton-like access to config values."""

    BOT_NAME: str = os.getenv("BOT_NAME", "monty")
    BOT_GREETING: str = os.getenv("BOT_GREETING", "Hi {{username}}! Send me a message and I'll reply with the power of LLMs.")

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    # OpenRouter / LLM
    OPENROUTER_LLM: str = os.getenv("OPENROUTER_LLM", "openai/gpt-3.5-turbo")
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_LLM_TEMPERATURE_SUPPORTED: bool = os.getenv("OPENROUTER_LLM_TEMPERATURE_SUPPORTED", "true").lower() in {"1","true","yes","on"}
    OPENROUTER_LLM_TEMPERATURE: float = float(os.getenv("OPENROUTER_LLM_TEMPERATURE", "0.7"))

    # Redis (mandatory)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Misc
    HISTORY_TTL_SECONDS: int = int(os.getenv("HISTORY_TTL_SECONDS", "86400"))
    ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "false").lower() in {"1","true","yes","on"}


settings = Settings()

__all__: list[str] = ["settings"]
