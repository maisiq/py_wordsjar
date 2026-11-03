import asyncio

from core.config import JWTSettings

_KEY_STRING: str | None = None


class SecretRepository:
    def __init__(self, cfg: JWTSettings):
        self._cfg = cfg

    async def get_key(self) -> str:
        """Return the JWT signing key.

        The value comes from ``WORDSJAR_BACKEND_JWT_KEY`` when it is set and is
        read from the key file otherwise. Reading the file is blocking, so it
        runs in a thread - and only once per process.
        """
        global _KEY_STRING

        if _KEY_STRING is None:
            _KEY_STRING = await asyncio.to_thread(self._cfg.read_signing_key)
        return _KEY_STRING