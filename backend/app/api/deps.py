from logging import Logger
from typing import Annotated

from db.postgres import get_sessionmaker
from fastapi import Depends, Header, HTTPException, status
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
from services.helpers import validate_access_token
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session():
    session = get_sessionmaker()

    async with session() as session:
        yield session


async def get_word_repo(sess: Annotated[AsyncSession, Depends(get_session)]) -> WordRepository:
    return WordRepository(sess)


async def get_word_service(
    logger: Annotated[Logger, Depends(get_logger)],
    repo: Annotated[WordRepository, Depends(get_word_repo)]
):
    return WordService(logger, repo)


async def get_secret_repo() -> SecretRepository:
    return SecretRepository()


async def get_user_repo(sess: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return UserRepository(sess)


async def get_token_storage() -> TokenStorage:
    return TokenStorage()


async def get_auth_service(
    repo: Annotated[UserRepository, Depends(get_user_repo)],
    secret: Annotated[UserRepository, Depends(get_secret_repo)],
    storage: Annotated[TokenStorage, Depends(get_token_storage)],
    logger: Annotated[Logger, Depends(get_logger)],
):
    return AuthService(logger, repo, secret, storage)


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
    if not x_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Auth Token",
        )
    return x_auth_token


def get_refresh_token(
    x_refresh_token: Annotated[str | None, Header()] = None,
):
    return x_refresh_token


async def get_userdata(
    security_scopes: SecurityScopes,
    repo: Annotated[SecretRepository, Depends(get_secret_repo)],
    user_service: Annotated[AuthService, Depends(get_auth_service)],
    storage: Annotated[TokenStorage, Depends(get_token_storage)],
    x_auth_token: Annotated[str, Depends(get_access_token)],
    x_refresh_token: Annotated[str | None, Depends(get_refresh_token)],
):
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired Token",
    )

    if await storage.get(x_auth_token):
        raise exc

    sign_key = await repo.get_key()
    username = validate_access_token(sign_key, x_auth_token)
    if not username:
        raise exc
    
    user_info = await user_service.get_user_info(username)
    if not user_info or user_info.role not in security_scopes.scopes:
        raise exc

    user_data = Tokens(
        username=username,
        access=x_auth_token,
        refresh=x_refresh_token,
    )

    return user_data
