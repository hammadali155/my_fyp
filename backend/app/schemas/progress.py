from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BadgeItem(BaseModel):
    slug: str
    label: str
    icon: str | None = None
    criteria: dict[str, object]
    earned: bool
    earned_at: datetime | None = None


class BadgeListResponse(BaseModel):
    items: list[BadgeItem]
    total: int
    earned_count: int
