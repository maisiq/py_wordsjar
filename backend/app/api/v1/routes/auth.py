from typing import Annotated

from api.deps import get_auth_service, get_refresh_token, get_userdata_strict
from api.v1.schemas import (
    AuthenticateRequest,
    CreateUserRequest,
    SuccessResponse,
    TokensResponse,
    UserInfoResponse,
)
from core.errors import AlreadyExistsError, InvalidToken
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from models.domain import Tokens
from services.auth import AuthError, AuthService

router = APIRouter(
    tags=["auth"],
)


@router.post("/signup")
async def create_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    req: CreateUserRequest,
):
    try:
        await service.create_user(req.username, req.password)
        return SuccessResponse()
    except AlreadyExistsError as e:
        return JSONResponse({"detail": str(e)}, status.HTTP_400_BAD_REQUEST)


@router.post("/auth")
async def authenticate_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    req: AuthenticateRequest,
) -> TokensResponse:
    try:
        return await service.authenticate(req.username, req.password)
    except AuthError as e:
        return JSONResponse({"detail": str(e)}, 400)


@router.get("/user/info")
async def user_info(
    userdata: Annotated[str, Depends(get_userdata_strict)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserInfoResponse | None:
    info = await service.get_user_info(userdata.username)
    if not info:
        return JSONResponse({"detail": "not found"}, 404)
    return info


@router.post("/logout")
async def logout(
    userdata: Annotated[str, Depends(get_userdata_strict)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse | None:
    await service.logout(userdata)
    return SuccessResponse()


@router.post("/refresh")
async def refresh(
    token: Annotated[str, Depends(get_refresh_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokensResponse:
    try:
        return await service.get_new_tokens(token)
    except InvalidToken as e:
        return JSONResponse({"detail": str(e)}, 400)