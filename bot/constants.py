from __future__ import annotations

from .config import settings

BOT_NAME = settings.BOT_NAME
CONV_ID = "default"

# Redis key patterns
def whitelist_key(user_id: int) -> str:
    return f"{BOT_NAME}.{user_id}"

def history_key(user_id: int, conv_id: str = CONV_ID) -> str:
    return f"{BOT_NAME}.{user_id}.{conv_id}"
