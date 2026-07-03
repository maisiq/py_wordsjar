from typing import Any

from cachetools import TTLCache
from core import config

_data: TTLCache | None = None


class TokenStorage:
    def __init__(self, cfg: config.JWTSettings):
        global _data
        if _data is None:
            _data = TTLCache(256, cfg.refresh_token_ttl)

    async def store(self, key: str, value: Any, ttl: int) -> None:
        _data[key] = value

    async def get(self, key: str) -> str | None:
        return _data.get(key)
    
    async def delete(self, key: str) -> None:
        try:
            _data.pop(key)
        except KeyError:
            return
