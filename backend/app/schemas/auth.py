from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Level = Literal["beginner", "intermediate", "advanced"]


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    native_lang: str = Field(default="en", max_length=10)
    ui_lang: str = Field(default="en", max_length=10)
    level: Level = "beginner"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str
    native_lang: str
    ui_lang: str
    level: str
    learning_goal: str | None = None
    streak_days: int
    xp: int
    is_active: bool
    onb_complete: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    native_lang: str | None = Field(default=None, max_length=10)
    ui_lang: str | None = Field(default=None, max_length=10)
    level: Level | None = None
    learning_goal: str | None = Field(default=None, max_length=50)
