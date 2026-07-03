from typing import Annotated

from api.deps import get_auth_service, get_refresh_token, get_userdata_strict
from api.v1.schemas import (
    AuthenticateRequest,
    CreateUserRequest,
    SuccessResponse,
    TokensResponse,
    UserInfoResponse,
)
from core.errors import InvalidToken
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
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"detail": str(e)}, 400)


@router.post("/auth")
async def authenticate_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    req: AuthenticateRequest,
) -> TokensResponse:
    try:
        tokens = await service.authenticate(req.username, req.password)
    except AuthError as e:
        return JSONResponse({"detail": str(e)}, 400)
    except Exception:
        return JSONResponse({"detail": "internal error"}, 500)
    return tokens


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
    try:
        await service.logout(userdata)
        return SuccessResponse()
    except Exception:
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/refresh")
async def refresh(
    token: Annotated[str, Depends(get_refresh_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokensResponse:
    try:
        return await service.get_new_tokens(token)
    except InvalidToken as e:
        return JSONResponse({"detail": str(e)}, 400)
    except Exception as e:
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)