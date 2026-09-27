from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserUpdateRequest,
)

logger = get_logger("services.auth")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def register(self, req: RegisterRequest) -> tuple[User, TokenResponse]:
        logger.info("Attempting registration for email=%s", req.email)

        # Check existing user
        existing = await self.db.execute(select(User).where(User.email == req.email.lower()))
        if existing.scalar_one_or_none() is not None:
            logger.warning("Registration failed: email %s already registered", req.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        hashed = hash_password(req.password)
        user = User(
            email=req.email.lower(),
            name=req.name,
            password_hash=hashed,
            native_lang=req.native_lang,
            ui_lang=req.ui_lang,
            level=req.level,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        tokens = await self._generate_tokens(user)
        await self.db.commit()

        logger.info("Successfully registered user id=%d email=%s", user.id, user.email)
        return user, tokens

    async def login(self, req: LoginRequest) -> tuple[User, TokenResponse]:
        logger.info("Attempting login for email=%s", req.email)

        result = await self.db.execute(select(User).where(User.email == req.email.lower()))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(req.password, user.password_hash):
            logger.warning("Invalid credentials for email=%s", req.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            logger.warning("Login rejected: user id=%d is inactive", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        tokens = await self._generate_tokens(user)
        await self.db.commit()

        logger.info("Successfully authenticated user id=%d", user.id)
        return user, tokens

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        logger.debug("Attempting token refresh")
        try:
            payload = decode_token(refresh_token_str)
        except ExpiredSignatureError as err:
            logger.warning("Refresh token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            ) from err
        except InvalidTokenError as err:
            logger.warning("Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from err

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token",
            )

        user_id = int(payload["sub"])
        token_hash = _hash_token(refresh_token_str)

        # Check in DB
        res = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        stored_token = res.scalar_one_or_none()

        if stored_token is None:
            logger.warning("Refresh token not found or already revoked for user_id=%d", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked or is invalid",
            )

        # Revoke old refresh token (rotation)
        stored_token.revoked_at = datetime.now(UTC)

        # Retrieve user
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer active",
            )

        # Generate new pair
        tokens = await self._generate_tokens(user)
        await self.db.commit()

        logger.info("Successfully refreshed tokens for user_id=%d", user_id)
        return tokens

    async def logout(self, user_id: int, refresh_token_str: str | None = None) -> None:
        logger.info("Logging out user_id=%d", user_id)
        if refresh_token_str:
            token_hash = _hash_token(refresh_token_str)
            res = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.token_hash == token_hash,
                )
            )
            token = res.scalar_one_or_none()
            if token and token.revoked_at is None:
                token.revoked_at = datetime.now(UTC)
                await self.db.commit()
                logger.debug("Revoked refresh token for user_id=%d", user_id)
        else:
            # Revoke all tokens for user
            tokens_res = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            for t in tokens_res.scalars():
                t.revoked_at = datetime.now(UTC)
            await self.db.commit()
            logger.debug("Revoked all active refresh tokens for user_id=%d", user_id)

    async def update_profile(self, user: User, req: UserUpdateRequest) -> User:
        logger.info("Updating profile for user_id=%d", user.id)
        if req.name is not None:
            user.name = req.name
        if req.native_lang is not None:
            user.native_lang = req.native_lang
        if req.ui_lang is not None:
            user.ui_lang = req.ui_lang
        if req.level is not None:
            user.level = req.level
        if req.learning_goal is not None:
            user.learning_goal = req.learning_goal

        await self.db.commit()
        await self.db.refresh(user)
        logger.info("Updated profile for user_id=%d successfully", user.id)
        return user

    async def _generate_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            subject=user.id,
            extra={"email": user.email, "role": user.role},
        )
        refresh_token = create_refresh_token(subject=user.id)

        # Store refresh token record
        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days),
        )
        self.db.add(refresh_record)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )
