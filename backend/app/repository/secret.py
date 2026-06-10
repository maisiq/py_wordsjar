from core.config import BASE_DIR


class SecretRepository:
     async def get_key(self) -> str:
          with open(BASE_DIR / "key", mode="r", encoding="utf8") as f:
               key = f.read()
               return key
