from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.quran import Surah, Verse
from app.schemas.quran import SearchMatchItem

logger = get_logger("services.quran")


class QuranService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_surahs(self) -> list[Surah]:
        logger.debug("Fetching all surahs")
        stmt = select(Surah).order_by(Surah.number.asc())
        result = await self.db.execute(stmt)
        surahs = list(result.scalars().all())
        logger.debug("Found %d surahs", len(surahs))
        return surahs

    async def get_surah(self, surah_id_or_number: int) -> Surah:
        logger.debug("Fetching surah with id/number=%d", surah_id_or_number)
        stmt = select(Surah).where(
            or_(Surah.id == surah_id_or_number, Surah.number == surah_id_or_number)
        )
        result = await self.db.execute(stmt)
        surah = result.scalar_one_or_none()
        if surah is None:
            logger.warning("Surah not found: %d", surah_id_or_number)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Surah {surah_id_or_number} not found",
            )
        return surah

    async def list_verses(
        self,
        surah_id: int | None = None,
        juz_number: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Verse], int]:
        logger.debug(
            "Listing verses filter: surah_id=%s juz_number=%s page=%d page_size=%d",
            surah_id,
            juz_number,
            page,
            page_size,
        )

        base_stmt = select(Verse)
        count_stmt = select(func.count(Verse.id))

        if surah_id is not None:
            base_stmt = base_stmt.where(Verse.surah_id == surah_id)
            count_stmt = count_stmt.where(Verse.surah_id == surah_id)

        if juz_number is not None:
            base_stmt = base_stmt.where(Verse.juz_number == juz_number)
            count_stmt = count_stmt.where(Verse.juz_number == juz_number)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            base_stmt.options(selectinload(Verse.words))
            .order_by(Verse.surah_id.asc(), Verse.ayah_number.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        verses = list(result.scalars().all())

        # Sort words in memory to ensure position order
        for v in verses:
            v.words.sort(key=lambda w: w.position)

        logger.debug("Retrieved %d verses out of %d total", len(verses), total)
        return verses, total

    async def get_verse(self, verse_id: int) -> Verse:
        logger.debug("Fetching verse id=%d", verse_id)
        stmt = (
            select(Verse)
            .options(selectinload(Verse.words))
            .where(Verse.id == verse_id)
        )
        result = await self.db.execute(stmt)
        verse = result.scalar_one_or_none()
        if verse is None:
            logger.warning("Verse not found: %d", verse_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verse {verse_id} not found",
            )
        verse.words.sort(key=lambda w: w.position)
        return verse

    async def search(self, query: str, limit: int = 50) -> tuple[list[SearchMatchItem], int]:
        clean_q = query.strip()
        if not clean_q:
            return [], 0

        logger.info("Performing Quran search for query=%r limit=%d", clean_q, limit)

        # Match against text_uthmani, text_imlaei, translation_en, or translation_ur
        pattern = f"%{clean_q}%"
        stmt = (
            select(Verse, Surah)
            .join(Surah, Verse.surah_id == Surah.id)
            .where(
                or_(
                    Verse.text_uthmani.ilike(pattern),
                    Verse.text_imlaei.ilike(pattern),
                    Verse.translation_en.ilike(pattern),
                    Verse.translation_ur.ilike(pattern),
                )
            )
            .order_by(Verse.surah_id.asc(), Verse.ayah_number.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = [
            SearchMatchItem(
                surah_number=surah.number,
                surah_name_english=surah.name_english,
                ayah_number=verse.ayah_number,
                text_uthmani=verse.text_uthmani,
                translation_en=verse.translation_en,
                translation_ur=verse.translation_ur,
            )
            for verse, surah in rows
        ]

        logger.info("Found %d search matches for query=%r", len(items), clean_q)
        return items, len(items)
