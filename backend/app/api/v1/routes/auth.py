from typing import Annotated

from api.deps import get_auth_service, get_refresh_token, get_userdata_strict
from api.v1.schemas import (
    AuthenticateRequest,
    CreateUserRequest,
    SuccessResponse,
    TokensResponse,
    UserInfoResponse,
)
from core.errors import InvalidToken, NotFound
from fastapi import APIRouter, Depends, status
from models.domain import Tokens
from services.auth import AuthService

router = APIRouter(
    tags=["auth"],
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    req: CreateUserRequest,
) -> SuccessResponse:
    # Duplicate usernames are reported by AuthService as AlreadyExistsError -> 409.
    await service.create_user(req.username, req.password)
    return SuccessResponse()


@router.post("/auth")
async def authenticate_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    req: AuthenticateRequest,
) -> TokensResponse:
    # Wrong credentials raise AuthError -> 401.
    return await service.authenticate(req.username, req.password)


@router.get("/user/info")
async def user_info(
    userdata: Annotated[Tokens, Depends(get_userdata_strict)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserInfoResponse:
    info = await service.get_user_info(userdata.username)
    if info is None:
        raise NotFound("user not found")
    return info


@router.post("/logout")
async def logout(
    userdata: Annotated[Tokens, Depends(get_userdata_strict)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse:
    await service.logout(userdata)
    return SuccessResponse()


@router.post("/refresh")
async def refresh(
    token: Annotated[str | None, Depends(get_refresh_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokensResponse:
    if not token:
        raise InvalidToken("refresh token is required")
    return await service.get_new_tokens(token)