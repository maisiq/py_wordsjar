from typing import Any

from cachetools import TTLCache
from core import config

_data = TTLCache(256, config.REFRESH_TOKEN_TTL)


class TokenStorage:
    async def store(self, key: str, value: Any, ttl: int) -> None:
        _data[key] = value

    async def get(self, key: str) -> str | None:
        return _data.get(key)
