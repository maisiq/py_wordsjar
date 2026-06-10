from typing import Annotated

from api.deps import get_auth_service, get_userdata
from api.v1.schemas import (
    AuthenticateRequest,
    CreateUserRequest,
    SuccessResponse,
    UserInfoResponse,
)
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
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
):
    try:
        tokens = await service.authenticate(req.username, req.password)
    except AuthError as e:
        return JSONResponse({"detail": str(e)}, 400)
    except Exception:
        return JSONResponse({"detail": "internal error"}, 500)
    return tokens


@router.get("/user/info")
async def user_info(
    userdata: Annotated[str, Depends(get_userdata)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserInfoResponse | None:
    info = await service.get_user_info(userdata.username)
    if not info:
        return JSONResponse({"detail": "not found"}, 404)
    return info


@router.post("/logout")
async def logout(
    userdata: Annotated[str, Depends(get_userdata)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse | None:
    try:
        await service.logout(userdata)
        return SuccessResponse()
    except Exception as e:
        return JSONResponse({"detail": str(e)}, 400)