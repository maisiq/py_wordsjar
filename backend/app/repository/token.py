from typing import Any

from cachetools import TTLCache

_data = TTLCache(256, 60*60*12)


class TokenStorage:
    async def store(self, key: str, value: Any, ttl: int) -> None:
        _data[key] = value

    async def get(self, key: str) -> str | None:
        return _data.get(key)
