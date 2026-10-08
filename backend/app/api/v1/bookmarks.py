from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.bookmark import BookmarkCreate, BookmarkListResponse, BookmarkResponse
from app.services.bookmark_service import BookmarkService

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])
logger = get_logger("api.bookmarks")


@router.post(
    "",
    response_model=BookmarkResponse,
    summary="Create or update a bookmark for a verse",
)
async def create_or_update_bookmark(
    req: BookmarkCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> BookmarkResponse:
    service = BookmarkService(db)
    return await service.create_or_update(user_id=current_user.id, req=req)


@router.get(
    "",
    response_model=BookmarkListResponse,
    summary="List the current user's bookmarks, optionally filtered by collection",
)
async def list_bookmarks(
    db: DbSession,
    current_user: CurrentUser,
    collection: str | None = Query(default=None, description="Filter by collection name"),
) -> BookmarkListResponse:
    service = BookmarkService(db)
    items = await service.list(user_id=current_user.id, collection=collection)
    return BookmarkListResponse(items=items, total=len(items))


@router.delete(
    "/{bookmark_id}",
    status_code=204,
    summary="Delete one of the current user's bookmarks",
)
async def delete_bookmark(
    bookmark_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    service = BookmarkService(db)
    await service.delete(user_id=current_user.id, bookmark_id=bookmark_id)
