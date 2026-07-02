from core.config import JWTSettings

_KEY_STRING: str | None = None


class SecretRepository:
     def __init__(self, cfg: JWTSettings):
          self._cfg = cfg

     async def get_key(self) -> str:
          global _KEY_STRING

          if not _KEY_STRING:
               with open(self._cfg.key_file_path, mode="r", encoding="utf8") as f:
                    _KEY_STRING = f.read()
          if not _KEY_STRING:
               raise RuntimeError("no key string in secret repository")
          return _KEY_STRING
