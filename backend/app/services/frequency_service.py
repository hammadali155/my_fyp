from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.models.quran import Word

PLACEHOLDER_ROOT = "ـ"
PLACEHOLDER_LEMMA = "ـ"


class FrequencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _frequencies(
        self,
        column: InstrumentedAttribute[str | None],
        placeholder: str,
        *,
        min_count: int | None,
        limit: int | None,
    ) -> list[tuple[str, int]]:
        count = func.count(Word.id)
        stmt = (
            select(column, count)
            .where(column.is_not(None), column != placeholder)
            .group_by(column)
        )
        if min_count is not None:
            stmt = stmt.having(count >= min_count)
        stmt = stmt.order_by(count.desc(), column.asc())
        if limit is not None:
            stmt = stmt.limit(limit)

        rows = (await self.db.execute(stmt)).all()
        return [(str(key), int(total)) for key, total in rows]

    async def root_frequencies(
        self, *, min_count: int | None = None, limit: int | None = None
    ) -> list[tuple[str, int]]:
        return await self._frequencies(
            Word.root,
            PLACEHOLDER_ROOT,
            min_count=min_count,
            limit=limit,
        )

    async def lemma_frequencies(
        self, *, min_count: int | None = None, limit: int | None = None
    ) -> list[tuple[str, int]]:
        return await self._frequencies(
            Word.lemma,
            PLACEHOLDER_LEMMA,
            min_count=min_count,
            limit=limit,
        )
