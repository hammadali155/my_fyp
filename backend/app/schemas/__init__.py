from __future__ import annotations

from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import MessageResponse, PaginatedParams, PaginatedResponse
from app.schemas.quran import (
    QuranSearchResponse,
    SearchMatchItem,
    SurahDetailResponse,
    SurahListResponse,
    SurahResponse,
    VerseListResponse,
    VerseResponse,
    WordResponse,
)

__all__ = [
    "MessageResponse",
    "PaginatedParams",
    "PaginatedResponse",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserResponse",
    "UserUpdateRequest",
    "SurahResponse",
    "SurahDetailResponse",
    "SurahListResponse",
    "VerseResponse",
    "WordResponse",
    "VerseListResponse",
    "SearchMatchItem",
    "QuranSearchResponse",
]
