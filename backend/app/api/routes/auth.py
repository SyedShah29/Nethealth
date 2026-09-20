from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies.auth import get_auth_service, get_current_user, require_trusted_origin
from app.core.config import Settings, get_settings
from app.models.auth import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth")


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(require_trusted_origin)],
)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    result = await service.login(
        payload.email,
        payload.password,
        request_id=getattr(request.state, "request_id", None),
    )
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=result.token,
        max_age=settings.auth_session_hours * 60 * 60,
        expires=result.expires_at,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/api",
    )
    return LoginResponse(
        user=UserResponse.model_validate(result.user),
        expires_at=result.expires_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def logout(
    response: Response,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    await service.logout(
        request.cookies.get(settings.auth_cookie_name),
        request_id=getattr(request.state, "request_id", None),
    )
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/api",
        secure=settings.app_env == "production",
        httponly=True,
        samesite="strict",
    )


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
