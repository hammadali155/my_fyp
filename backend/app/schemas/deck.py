from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DeckCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class DeckStateCounts(BaseModel):
    new: int = 0
    learning: int = 0
    review: int = 0
    graduated: int = 0


class DeckResponse(BaseModel):
    id: int
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    counts: DeckStateCounts
    total_cards: int

    model_config = {"from_attributes": True}


class DeckListResponse(BaseModel):
    items: list[DeckResponse]
    total: int


class AddWordRequest(BaseModel):
    word_id: int = Field(ge=1)


class BulkAddWordsRequest(BaseModel):
    word_ids: list[int] = Field(..., min_length=1, max_length=500)


class DeckWordAddResponse(BaseModel):
    added: int
    skipped_duplicates: int
    card_ids: list[int]
