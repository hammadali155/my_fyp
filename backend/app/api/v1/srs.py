from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.srs import (
    SRSCardCreate,
    SRSCardResponse,
    SRSDueQueueResponse,
    SRSReviewRequest,
    SRSReviewResponse,
    SRSStatsResponse,
)
from app.services.srs_service import SRSService

router = APIRouter(prefix="/srs", tags=["Spaced Repetition (SRS)"])
logger = get_logger("api.srs")


@router.post(
    "/cards",
    response_model=SRSCardResponse,
    status_code=201,
    summary="Create a new SRS flashcard for the authenticated user",
)
async def create_card(
    req: SRSCardCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> SRSCardResponse:
    service = SRSService(db)
    return await service.create_card(user_id=current_user.id, req=req)


@router.get(
    "/due",
    response_model=SRSDueQueueResponse,
    summary="Fetch cards due for review right now",
)
async def get_due_queue(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100, description="Max cards to return"),
) -> SRSDueQueueResponse:
    service = SRSService(db)
    return await service.get_due_queue(user_id=current_user.id, limit=limit)


@router.post(
    "/review",
    response_model=SRSReviewResponse,
    summary="Submit a review rating for a card (1=Again, 2=Hard, 3=Good, 4=Easy)",
)
async def submit_review(
    req: SRSReviewRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> SRSReviewResponse:
    service = SRSService(db)
    return await service.submit_review(
        user_id=current_user.id,
        card_id=req.card_id,
        rating=req.rating,
        review_duration_ms=req.review_duration_ms,
    )


@router.get(
    "/stats",
    response_model=SRSStatsResponse,
    summary="Get SRS learning statistics and streak for the authenticated user",
)
async def get_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> SRSStatsResponse:
    service = SRSService(db)
    return await service.get_stats(user_id=current_user.id)


@router.delete(
    "/cards/{card_id}",
    status_code=204,
    summary="Delete a specific SRS card (and all its review history)",
)
async def delete_card(
    card_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    service = SRSService(db)
    await service.delete_card(user_id=current_user.id, card_id=card_id)
