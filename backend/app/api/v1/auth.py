from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger("api.auth")


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new learner account",
)
async def register(req: RegisterRequest, db: DbSession) -> AuthResponse:
    auth_service = AuthService(db)
    user, tokens = await auth_service.register(req)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Log in with email and password",
)
async def login(req: LoginRequest, db: DbSession) -> AuthResponse:
    auth_service = AuthService(db)
    user, tokens = await auth_service.login(req)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an expired access token using a refresh token",
)
async def refresh_token(req: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    auth_service = AuthService(db)
    return await auth_service.refresh(req.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the refresh token / log out session",
)
async def logout(
    current_user: CurrentUser,
    db: DbSession,
    req: RefreshTokenRequest | None = None,
) -> MessageResponse:
    auth_service = AuthService(db)
    token_str = req.refresh_token if req else None
    await auth_service.logout(current_user.id, token_str)
    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged in user profile",
)
async def get_current_profile(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current logged in user profile preferences",
)
async def update_profile(
    req: UserUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    auth_service = AuthService(db)
    updated = await auth_service.update_profile(current_user, req)
    return UserResponse.model_validate(updated)
