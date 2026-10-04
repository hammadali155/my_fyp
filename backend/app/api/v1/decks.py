from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.deck import (
    AddWordRequest,
    BulkAddWordsRequest,
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckWordAddResponse,
)
from app.services.deck_service import DeckService

router = APIRouter(prefix="/decks", tags=["Decks"])
logger = get_logger("api.decks")


@router.get(
    "",
    response_model=DeckListResponse,
    summary="List the current user's decks with per-state card counts",
)
async def list_decks(db: DbSession, current_user: CurrentUser) -> DeckListResponse:
    service = DeckService(db)
    items = await service.list_decks(user_id=current_user.id)
    return DeckListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=DeckResponse,
    status_code=201,
    summary="Create a custom deck",
)
async def create_deck(req: DeckCreate, db: DbSession, current_user: CurrentUser) -> DeckResponse:
    service = DeckService(db)
    return await service.create_deck(user_id=current_user.id, req=req)


@router.post(
    "/{deck_id}/words",
    response_model=DeckWordAddResponse,
    summary="Add a word to a deck by word_id (duplicates rejected)",
)
async def add_word(deck_id: int, req: AddWordRequest, db: DbSession, current_user: CurrentUser) -> DeckWordAddResponse:
    service = DeckService(db)
    added, skipped, card_ids = await service.add_words(user_id=current_user.id, deck_id=deck_id, word_ids=[req.word_id])
    if skipped:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Word {req.word_id} already in deck")
    return DeckWordAddResponse(added=added, skipped_duplicates=0, card_ids=card_ids)


@router.post(
    "/{deck_id}/words/bulk",
    response_model=DeckWordAddResponse,
    summary="Add several words to a deck in one request",
)
async def add_words_bulk(deck_id: int, req: BulkAddWordsRequest, db: DbSession, current_user: CurrentUser) -> DeckWordAddResponse:
    service = DeckService(db)
    added, skipped, card_ids = await service.add_words(user_id=current_user.id, deck_id=deck_id, word_ids=req.word_ids)
    return DeckWordAddResponse(added=added, skipped_duplicates=skipped, card_ids=card_ids)


@router.delete(
    "/{deck_id}",
    status_code=204,
    summary="Delete a deck and its cards",
)
async def delete_deck(deck_id: int, db: DbSession, current_user: CurrentUser) -> None:
    service = DeckService(db)
    await service.delete_deck(user_id=current_user.id, deck_id=deck_id)
