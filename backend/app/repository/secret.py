from core.config import JWT_KEY_FILE_PATH

_KEY_STRING: str | None = None


class SecretRepository:
     async def get_key(self) -> str:
          global _KEY_STRING

          if _KEY_STRING is None:
               with open(JWT_KEY_FILE_PATH, mode="r", encoding="utf8") as f:
                    _KEY_STRING = f.read()
          return _KEY_STRING
