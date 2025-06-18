"""Thin Redis wrapper with graceful fallback to in-memory dict when disabled."""
from __future__ import annotations

import json
from typing import Any, Optional

from redis import Redis, RedisError  # type: ignore

from .config import settings


class _DummyRedis:  # pylint: disable=too-few-public-methods
    """Fallback store when Redis is not enabled."""

    _store: dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:  # noqa: D401 (simple one-line)
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: D401
        self._store[key] = value

    def exists(self, key: str) -> bool:  # noqa: D401
        return key in self._store


try:
    redis_client: Any = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
except RedisError as exc:  # pragma: no cover
    print("Redis connection failed, falling back to dummy store:", exc)
    redis_client = _DummyRedis()


# Helper functions

def get_json(key: str) -> Any | None:
    raw = redis_client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_json(key: str, value: Any, ttl: int | None = None) -> None:
    redis_client.set(key, json.dumps(value), ex=ttl)


def key_exists(key: str) -> bool:
    return redis_client.exists(key)


def delete_key(key: str) -> None:
    try:
        redis_client.delete(key)
    except Exception:  # noqa: BLE001
        pass
