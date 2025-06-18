"""Wrapper around OpenRouter compatible models via OpenAI python SDK."""
from __future__ import annotations

from typing import Sequence
import json
import logging
from datetime import datetime
from pathlib import Path

import openai
from openai import OpenAI

from .config import settings

openai.api_key = settings.OPENROUTER_API_KEY
openai.base_url = "https://openrouter.ai/api/v1"  # OpenRouter endpoint

_openai_client = OpenAI(api_key=settings.OPENROUTER_API_KEY, base_url=openai.base_url)

# --- optional detailed logging ---
_logger: logging.Logger | None = None
if settings.ENABLE_LOGGING:
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / f"logfile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    _logger = logging.getLogger("openrouter")
    _logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)


def chat(messages: Sequence[dict[str, str]], model: str | None = None, temperature: float | None = None) -> str:
    """Return assistant completion text."""
    kwargs = {
        "model": model or settings.OPENROUTER_LLM,
        "messages": list(messages),
    }
    if settings.OPENROUTER_LLM_TEMPERATURE_SUPPORTED:
        kwargs["temperature"] = temperature if temperature is not None else settings.OPENROUTER_LLM_TEMPERATURE

    if _logger:
        _logger.info("REQUEST %s", json.dumps(kwargs, ensure_ascii=False))

    response = _openai_client.chat.completions.create(**kwargs)

    if _logger:
        try:
            resp_dict = response.model_dump()  # type: ignore[attr-defined]
        except AttributeError:  # fallback
            resp_dict = response.__dict__
        _logger.info("RESPONSE %s", json.dumps(resp_dict, ensure_ascii=False))

    return response.choices[0].message.content  # type: ignore[attr-defined]
