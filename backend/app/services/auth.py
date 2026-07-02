from logging import Logger
from typing import Any, Protocol

from core import config
from core.errors import AlreadyExistsError, AuthError, InternalError
from models.domain import Tokens, User, UserInfo

from .helpers import *


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...
    async def get(self, username: str) -> User | None: ...


class SecretRepository(Protocol):
    async def get_key(self) -> str: ...


class TokenStorage(Protocol):
    async def store(self, key: str, value: Any, ttl: int) -> None: ...
    async def get(self, key: str) -> Any: ...


class AuthService:
    def __init__(
        self,
        log: Logger,
        jwt_cfg: config.JWTSettings,
        user_repo: UserRepository,
        secret_repo: SecretRepository,
        token_storage: TokenStorage,
    ):
        self._log = log
        self._user_repo = user_repo
        self._secret_repo = secret_repo
        self._token_storage = token_storage
        self._jwt_cfg = jwt_cfg
    
    async def create_user(self, username: str, password: str) -> None:
        hashed = hash_password(password)
        username = normalize_username(username)

        user = User(
            username=username,
            hashed_password=hashed,
        )
        try:
            await self._user_repo.add(user)
        except AlreadyExistsError as e:
            raise e
        except Exception as e:
            self._log.error("Failed to add user: %s", e)
            raise InternalError("internal error")

    async def authenticate(self, username: str, plain_password: str) -> Tokens | None:
        username = normalize_username(username)

        try:
            user = await self._user_repo.get(username)
        except Exception as e:
            self._log.error("failed to get user: %s", e)
            raise InternalError("internal error")

        if not user:
            raise AuthError("user not found")

        ok = verify_password(plain_password, user.hashed_password)
        if not ok:
            raise AuthError("failed to verify password")
        
        try:
            key = await self._secret_repo.get_key()
        except Exception as e:
            self._log.error("failed to get sign key from secret repo: %s", e)
            raise InternalError("internal error")

        ss = create_access_token(self._jwt_cfg, key, user.username, user.role)
        refresh = generate_refresh_token()

        return Tokens(
            access=ss,
            refresh=refresh,
        )

    async def get_user_info(self, username: str) -> UserInfo | None:
        try:
            user = await self._user_repo.get(username)
        except Exception as e:
            self._log.error("failed to get user: %s", e)
            raise InternalError("internal error")

        if not user:
            return

        return UserInfo(
            username=user.username,
            role=user.role,
        )
    
    async def get_user(self, username: str) -> User | None:
        try:
            return await self._user_repo.get(username)
        except Exception as e:
            self._log.error("failed to get user: %s", e)
            raise InternalError("internal error")

    async def logout(self, tokens: Tokens) -> None:
        try:
            if tokens.access:
                await self._token_storage.store(tokens.access, "1", config.ACCESS_TOKEN_TTL)
            if tokens.refresh:
                await self._token_storage.store(tokens.refresh, "1", config.REFRESH_TOKEN_TTL)
        except Exception as e:
            self._log.error("failed to store tokens: %s", e)
            raise InternalError("internal error")
