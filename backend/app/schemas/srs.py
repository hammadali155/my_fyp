from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SRSCardCreate(BaseModel):
    item_type: str = Field(default="root", description="root | vocabulary | verse_fill_blank | grammar_rule")
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    hint: str | None = None
    word_id: int | None = None
    surah_number: int | None = Field(default=None, ge=1, le=114)
    ayah_number: int | None = Field(default=None, ge=1)


class SRSReviewRequest(BaseModel):
    card_id: int
    rating: int = Field(..., ge=1, le=4, description="1=Again, 2=Hard, 3=Good, 4=Easy")
    review_duration_ms: int | None = Field(default=None, ge=0)


class SRSCardResponse(BaseModel):
    id: int
    item_type: str
    front: str
    back: str
    hint: str | None
    word_id: int | None
    surah_number: int | None
    ayah_number: int | None
    state: str
    ease_factor: float
    interval_days: int
    repetitions: int
    lapses: int
    due_date: datetime
    last_reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class SRSReviewResponse(BaseModel):
    card_id: int
    new_state: str
    new_interval_days: int
    new_ease_factor: float
    next_due: datetime


class SRSDueQueueResponse(BaseModel):
    cards: list[SRSCardResponse]
    total: int
    new_count: int
    learning_count: int
    review_count: int


class SRSStatsResponse(BaseModel):
    total_cards: int
    new_cards: int
    learning_cards: int
    review_cards: int
    graduated_cards: int
    reviews_today: int
    streak_days: int
    due_now: int
