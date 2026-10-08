from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.bookmark import Bookmark
from app.models.quran import Surah, Verse
from app.schemas.bookmark import BookmarkCreate, BookmarkResponse

logger = get_logger("services.bookmark")


class BookmarkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update(self, user_id: int, req: BookmarkCreate) -> BookmarkResponse:
        verse_exists = await self.db.execute(select(Verse.id).where(Verse.id == req.verse_id))
        if verse_exists.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Verse {req.verse_id} not found")

        result = await self.db.execute(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.verse_id == req.verse_id)
        )
        bookmark = result.scalar_one_or_none()
        if bookmark is None:
            bookmark = Bookmark(user_id=user_id, verse_id=req.verse_id)
            self.db.add(bookmark)
        bookmark.note = req.note
        bookmark.collection = req.collection
        await self.db.commit()
        await self.db.refresh(bookmark)
        return await self._to_response(bookmark)

    async def list(self, user_id: int, collection: str | None = None) -> list[BookmarkResponse]:
        stmt = select(Bookmark).where(Bookmark.user_id == user_id)
        if collection is not None:
            stmt = stmt.where(Bookmark.collection == collection)
        stmt = stmt.order_by(Bookmark.created_at.desc())
        rows = (await self.db.execute(stmt)).scalars().all()
        return [await self._to_response(b) for b in rows]

    async def delete(self, user_id: int, bookmark_id: int) -> None:
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user_id)
        )
        bookmark = result.scalar_one_or_none()
        if bookmark is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
        await self.db.delete(bookmark)
        await self.db.commit()

    async def _to_response(self, bookmark: Bookmark) -> BookmarkResponse:
        result = await self.db.execute(
            select(Verse, Surah)
            .join(Surah, Verse.surah_id == Surah.id)
            .where(Verse.id == bookmark.verse_id)
        )
        row = result.first()
        return BookmarkResponse(
            id=bookmark.id,
            verse_id=bookmark.verse_id,
            note=bookmark.note,
            collection=bookmark.collection,
            created_at=bookmark.created_at,
            updated_at=bookmark.updated_at,
            surah_number=row[1].number if row else None,
            ayah_number=row[0].ayah_number if row else None,
        )
