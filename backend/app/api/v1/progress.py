from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.progress import BadgeItem, BadgeListResponse
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])
logger = get_logger("api.progress")


@router.get(
    "/badges",
    response_model=BadgeListResponse,
    summary="List the current user's badge catalog with earned status",
)
async def list_badges(db: DbSession, current_user: CurrentUser) -> BadgeListResponse:
    service = ProgressService(db)
    badges = await service.get_badges(user_id=current_user.id)
    items = [BadgeItem(**b) for b in badges]
    earned = sum(1 for b in items if b.earned)
    return BadgeListResponse(items=items, total=len(items), earned_count=earned)
