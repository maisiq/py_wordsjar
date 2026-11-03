from logging import Logger
from typing import Annotated

from api.middleware.request import client_ip
from core import config
from core.errors import AppError, RateLimited
from db.postgres import get_sessionmaker
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import SecurityScopes
from logger import get_logger
from models.domain import Tokens
from repository import (
    JarRepository,
    SecretRepository,
    TokenStorage,
    UserRepository,
    WordRepository,
)
from services import AuthService, ExamService, JarService, WordService
from services.helpers import decode_access_token
from services.ratelimit import login_limiter, refresh_limiter, signup_limiter
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session():
    sessionmaker = get_sessionmaker()
    session = sessionmaker()

    try:
        yield session
    except BaseException:
        # Repositories commit on their own; anything that escapes must not leave
        # an aborted transaction behind for the next user of this connection.
        await session.rollback()
        raise
    finally:
        await session.close()


def get_jwt_settings() -> config.JWTSettings:
    return config.get_jwt_settings()


async def get_word_repo(sess: Annotated[AsyncSession, Depends(get_session)]) -> WordRepository:
    return WordRepository(sess)


async def get_word_service(
    logger: Annotated[Logger, Depends(get_logger)],
    repo: Annotated[WordRepository, Depends(get_word_repo)],
):
    return WordService(logger, repo)


async def get_secret_repo(cfg: Annotated[config.JWTSettings, Depends(get_jwt_settings)]) -> SecretRepository:
    return SecretRepository(cfg)


async def get_cursor_secret(
    repo: Annotated[SecretRepository, Depends(get_secret_repo)],
) -> str:
    return await repo.get_cursor_secret()


async def get_user_repo(sess: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return UserRepository(sess)


async def get_token_storage(
    sess: Annotated[AsyncSession, Depends(get_session)],
) -> TokenStorage:
    return TokenStorage(sess)


async def get_auth_service(
    repo: Annotated[UserRepository, Depends(get_user_repo)],
    secret: Annotated[SecretRepository, Depends(get_secret_repo)],
    storage: Annotated[TokenStorage, Depends(get_token_storage)],
    logger: Annotated[Logger, Depends(get_logger)],
    cfg: Annotated[config.JWTSettings, Depends(get_jwt_settings)],
):
    return AuthService(logger, cfg, repo, secret, storage)


async def get_jar_repo(sess: Annotated[AsyncSession, Depends(get_session)]) -> JarRepository:
    return JarRepository(sess)


async def get_jar_service(
    repo: Annotated[JarRepository, Depends(get_jar_repo)],
    logger: Annotated[Logger, Depends(get_logger)],
):
    return JarService(logger, repo)


async def get_exam_service(
    logger: Annotated[Logger, Depends(get_logger)],
    repo: Annotated[JarRepository, Depends(get_jar_repo)],
):
    return ExamService(logger, repo)


def get_access_token(
    x_auth_token: Annotated[str | None, Header()] = None,
):
    return x_auth_token


def get_refresh_token(
    x_refresh_token: Annotated[str | None, Header()] = None,
):
    return x_refresh_token


def _enforce(limiter, request: Request, bucket: str) -> None:
    retry_after = limiter.hit(f"{bucket}:{client_ip(request)}")
    if retry_after is not None:
        raise RateLimited(retry_after)


async def login_rate_limit(request: Request) -> None:
    _enforce(login_limiter, request, "login")


async def signup_rate_limit(request: Request) -> None:
    _enforce(signup_limiter, request, "signup")


async def refresh_rate_limit(request: Request) -> None:
    _enforce(refresh_limiter, request, "refresh")


async def _get_userdata(
    request: Request,
    security_scopes: SecurityScopes,
    repo: Annotated[SecretRepository, Depends(get_secret_repo)],
    user_service: Annotated[AuthService, Depends(get_auth_service)],
    storage: Annotated[TokenStorage, Depends(get_token_storage)],
    x_auth_token: Annotated[str | None, Depends(get_access_token)],
    x_refresh_token: Annotated[str | None, Depends(get_refresh_token)],
    cfg: Annotated[config.JWTSettings, Depends(get_jwt_settings)],
):
    if not x_auth_token:
        return None

    # Every mandatory dependency here returns None instead of raising: the
    # optional variant of this dependency is used by endpoints that also serve
    # anonymous users.
    if await storage.is_revoked(x_auth_token):
        return None

    try:
        sign_key = await repo.get_key()
        claims = decode_access_token(cfg, sign_key, x_auth_token)
    except AppError:
        return None

    username = claims.get("sub")
    # Every mandatory dependency here returns None instead of raising: the
    # optional variant of this dependency is used by endpoints that also serve
    # anonymous users.
    if await storage.is_revoked(x_auth_token):
        return None

    try:
        sign_key = await repo.get_key()
        claims = decode_access_token(cfg, sign_key, x_auth_token)
    except AppError:
        return None

    username = claims.get("sub")
    if not username:
        return None
        return None

    user_info = await user_service.get_user_info(username)
    if user_info is None:
        return None

    if security_scopes.scopes and user_info.role not in security_scopes.scopes:
        # Valid token, insufficient role: remember it so that the strict
        # dependency can answer 403 instead of 401.
        request.state.auth_denied = True
        return None

    return Tokens(
        username=username,
        access=x_auth_token,
        refresh=x_refresh_token,
    )


async def get_userdata_strict(
    request: Request,
    userdata: Annotated[Tokens | None, Depends(_get_userdata)],
) -> Tokens:
    if userdata is None:
        if getattr(request.state, "auth_denied", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        if getattr(request.state, "auth_denied", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired Token",
        )
    return userdata


async def get_userdata(
    data: Annotated[Tokens | None, Depends(_get_userdata)],
) -> Tokens | None:
    return data
