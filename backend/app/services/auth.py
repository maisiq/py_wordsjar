import datetime as dt
from logging import Logger
from typing import Protocol

from core import config
from core.errors import (
    AlreadyExistsError,
    AppError,
    AuthError,
    InternalError,
    InvalidToken,
)
from models.domain import Roles, Tokens, User, UserInfo

from .helpers import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password_async,
    normalize_username,
    verify_dummy_password,
    verify_password_async,
)


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...
    async def get(self, username: str) -> User | None: ...
    async def get_by_id(self, user_id: int) -> User | None: ...


class SecretRepository(Protocol):
    async def get_key(self) -> str: ...


class TokenStorage(Protocol):
    async def store(self, token: str, *, user_id: int, ttl: int, kind: str = ...) -> None: ...
    async def consume(self, token: str, kind: str = ...) -> int | None: ...
    async def is_revoked(self, token: str, kind: str = ...) -> bool: ...


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
        username = normalize_username(username)
        hashed = await hash_password_async(password)

        user = User(
            username=username,
            hashed_password=hashed,
            role=Roles.USER.value,
        )
        try:
            await self._user_repo.add(user)
        except AlreadyExistsError:
            raise
        except Exception as e:
            self._log.error("failed to add user: %s", e)
            raise InternalError("failed to create the user")

    async def authenticate(self, username: str, plain_password: str) -> Tokens:
        username = normalize_username(username)

        user = await self._get_user(username)
        if user is None:
            # Burn the same time as a real verification so that an unknown
            # username is indistinguishable from a wrong password.
            await verify_dummy_password(plain_password)
            raise AuthError("invalid credentials")

        if not await verify_password_async(plain_password, user.hashed_password):
            raise AuthError("invalid credentials")

        return await self._issue_tokens(user)

    async def get_user_info(self, username: str) -> UserInfo | None:
        user = await self._get_user(username)
        if user is None:
            return None
        user = await self._get_user(username)
        if user is None:
            return None

        return UserInfo(
            username=user.username,
            role=user.role,
        )

    async def get_user(self, username: str) -> User | None:
        return await self._get_user(username)

    async def logout(self, tokens: Tokens) -> None:
        """Revoke the access token until it expires and drop the refresh session."""
        """Revoke the access token until it expires and drop the refresh session."""
        try:
            if tokens.access:
                await self._revoke_access_token(tokens.access, tokens.username)
                await self._revoke_access_token(tokens.access, tokens.username)
            if tokens.refresh:
                await self._token_storage.consume(tokens.refresh)
        except AppError:
            raise
        except Exception as e:
            # Failing loudly is the point: a silently failed revocation would
            # leave a working token behind while the client believes it is out.
            self._log.error("failed to revoke tokens: %s", e)
            raise InternalError("failed to log out")

    async def get_new_tokens(self, refresh_token: str) -> Tokens:
        try:
            user_id = await self._token_storage.consume(refresh_token)
        except Exception as e:
            self._log.error("failed to consume refresh token: %s", e)
            raise InternalError("failed to refresh the session")

        if user_id is None:
            # Unknown, already rotated or expired: the session must not be
            # revived, the client has to sign in again.
            raise InvalidToken("invalid refresh token")

        try:
            user = await self._user_repo.get_by_id(user_id)
        except Exception as e:
            self._log.error("failed to get user by id(%s): %s", user_id, e)
            raise InternalError("failed to refresh the session")

        if user is None:
            raise InvalidToken("invalid refresh token")

        return await self._issue_tokens(user)

    async def _revoke_access_token(self, access_token: str, username: str | None) -> None:
        if username is None:
            return

        try:
            key = await self._secret_repo.get_key()
            claims = decode_access_token(self._jwt_cfg, key, access_token)
        except AppError:
            # Already expired or unreadable: nothing left to revoke.
            return

        user = await self._get_user(username)
        if user is None or user.id is None:
            return

        expires_at = claims.get("exp")
        if expires_at:
            ttl = int(expires_at - dt.datetime.now(dt.UTC).timestamp())
        else:
            ttl = self._jwt_cfg.access_token_ttl

        if ttl <= 0:
            return

        await self._token_storage.store(access_token, user_id=user.id, ttl=ttl, kind="access")

    async def _issue_tokens(self, user: User) -> Tokens:
        if user.id is None:
            self._log.error("cannot issue tokens for a user without id: %s", user.username)
            raise InternalError("failed to issue tokens")

        try:
            key = await self._secret_repo.get_key()
        except Exception as e:
            self._log.error("failed to get sign key from secret repo: %s", e)
            raise InternalError("failed to issue tokens")

        access, _ = create_access_token(self._jwt_cfg, key, user.username, user.role)
        refresh = generate_refresh_token()

        try:
            await self._token_storage.store(
                refresh,
                user_id=user.id,
                ttl=self._jwt_cfg.refresh_token_ttl,
            )

        except Exception as e:
            self._log.error("failed to store refresh token for user(%s): %s", user.username, e)
            raise InternalError("failed to issue tokens")

        return Tokens(
            username=user.username,
            access=access,
            username=user.username,
            access=access,
            refresh=refresh,
        )

    async def _get_user(self, username: str) -> User | None:
        try:
            return await self._user_repo.get(username)
        except Exception as e:
            self._log.error("failed to get user: %s", e)
            raise InternalError("failed to get the user")
