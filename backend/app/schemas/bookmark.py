from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookmarkCreate(BaseModel):
    verse_id: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=2000)
    collection: str | None = Field(default=None, max_length=100)


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verse_id: int
    note: str | None = None
    collection: str | None = None
    created_at: datetime
    updated_at: datetime
    surah_number: int | None = None
    ayah_number: int | None = None


class BookmarkListResponse(BaseModel):
    items: list[BookmarkResponse]
    total: int
