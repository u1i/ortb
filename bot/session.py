"""Conversation session utilities."""
from __future__ import annotations

from typing import List, Dict

from .constants import history_key
from .config import settings
from .redis_store import get_json, set_json


from pathlib import Path

# project root is one level up from the package directory
SYSTEM_PROMPT_MD = Path(__file__).resolve().parents[1] / "system_prompt.md"
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT_MD.read_text().strip() if SYSTEM_PROMPT_MD.exists() else "You are a helpful assistant."


class Conversation:
    """Represents a chat history for a given user."""

    def __init__(self, user_id: int, conv_id: str = "default") -> None:
        self.user_id = user_id
        self.conv_id = conv_id
        self._key = history_key(user_id, conv_id)
        self._messages: List[Dict[str, str]] = (
            get_json(self._key) or [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        )

    @property
    def messages(self) -> List[Dict[str, str]]:  # noqa: D401 (simple)
        return self._messages

    def append(self, role: str, content: str) -> None:  # noqa: D401
        self._messages.append({"role": role, "content": content})
        self._persist()

    # ---- helpers ----
    def reset(self) -> None:
        self._messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        self._persist()

    def _persist(self) -> None:
        set_json(self._key, self._messages, ttl=settings.HISTORY_TTL_SECONDS)
