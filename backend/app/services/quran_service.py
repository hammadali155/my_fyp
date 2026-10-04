from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.quran import Surah, Verse, Word
from app.schemas.quran import SearchMatchItem
from app.services.morphology_service import normalize_arabic

logger = get_logger("services.quran")


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in text)


def _is_latin(text: str) -> bool:
    return any(ch.isascii() and ch.isalpha() for ch in text)


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
        page_number: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Verse], int]:
        logger.debug(
            "Listing verses filter: surah_id=%s juz_number=%s page_number=%s page=%d page_size=%d",
            surah_id,
            juz_number,
            page_number,
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

        if page_number is not None:
            base_stmt = base_stmt.where(Verse.page_number == page_number)
            count_stmt = count_stmt.where(Verse.page_number == page_number)

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
        stmt = select(Verse).options(selectinload(Verse.words)).where(Verse.id == verse_id)
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

    async def get_verse_by_surah_ayah(self, surah_number: int, ayah_number: int) -> Verse:
        logger.debug("Fetching verse %d:%d", surah_number, ayah_number)
        stmt = (
            select(Verse)
            .join(Surah, Verse.surah_id == Surah.id)
            .options(selectinload(Verse.words))
            .where(Surah.number == surah_number, Verse.ayah_number == ayah_number)
        )
        result = await self.db.execute(stmt)
        verse = result.scalar_one_or_none()
        if verse is None:
            logger.warning("Verse not found: %d:%d", surah_number, ayah_number)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verse {surah_number}:{ayah_number} not found",
            )
        verse.words.sort(key=lambda w: w.position)
        return verse

    async def list_roots(
        self,
        min_count: int | None = None,
        pos_tag: str | None = None,
        surah_number: int | None = None,
        limit: int = 50,
    ) -> list[tuple[str, int]]:
        logger.debug(
            "Ranking roots: min_count=%s pos_tag=%s surah_number=%s limit=%d",
            min_count,
            pos_tag,
            surah_number,
            limit,
        )
        stmt = select(Word.root, func.count(Word.id)).where(Word.root.is_not(None))
        if pos_tag is not None:
            stmt = stmt.where(Word.pos_tag == pos_tag)
        if surah_number is not None:
            stmt = stmt.join(Verse, Word.verse_id == Verse.id).join(Surah, Verse.surah_id == Surah.id).where(Surah.number == surah_number)
        stmt = stmt.group_by(Word.root)
        if min_count is not None:
            stmt = stmt.having(func.count(Word.id) >= min_count)
        stmt = stmt.order_by(func.count(Word.id).desc(), Word.root.asc()).limit(limit)
        result = await self.db.execute(stmt)
        rows = [(root, count) for root, count in result.all() if root]
        logger.debug("Found %d roots", len(rows))
        return rows

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SearchMatchItem], int]:
        clean_q = query.strip()
        if not clean_q:
            return [], 0

        logger.info("Performing Quran search for query=%r page=%d page_size=%d", clean_q, page, page_size)

        if _is_arabic(clean_q):
            items = await self._search_arabic(clean_q)
        elif _is_latin(clean_q):
            items = await self._search_translation(clean_q, field="translation_en")
        else:
            items = await self._search_translation(clean_q, field="translation_ur")

        total = len(items)
        page_items = items[(page - 1) * page_size : page * page_size]
        logger.info("Found %d search matches for query=%r", total, clean_q)
        return page_items, total

    async def _search_arabic(self, query: str) -> list[SearchMatchItem]:
        nq = normalize_arabic(query)
        stmt = select(Verse, Surah).join(Surah, Verse.surah_id == Surah.id).order_by(Verse.surah_id.asc(), Verse.ayah_number.asc())
        rows = (await self.db.execute(stmt)).all()
        out = []
        for verse, surah in rows:
            if verse.text_imlaei and nq in normalize_arabic(verse.text_imlaei):
                out.append(
                    SearchMatchItem(
                        surah_number=surah.number,
                        surah_name_english=surah.name_english,
                        ayah_number=verse.ayah_number,
                        text_uthmani=verse.text_uthmani,
                        translation_en=verse.translation_en,
                        translation_ur=verse.translation_ur,
                        matched_field="text_imlaei",
                    )
                )
        return out

    async def _search_translation(self, query: str, field: str) -> list[SearchMatchItem]:
        column = Verse.translation_en if field == "translation_en" else Verse.translation_ur
        pattern = f"%{query}%"
        stmt = (
            select(Verse, Surah)
            .join(Surah, Verse.surah_id == Surah.id)
            .where(column.ilike(pattern))
            .order_by(Verse.surah_id.asc(), Verse.ayah_number.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            SearchMatchItem(
                surah_number=surah.number,
                surah_name_english=surah.name_english,
                ayah_number=verse.ayah_number,
                text_uthmani=verse.text_uthmani,
                translation_en=verse.translation_en,
                translation_ur=verse.translation_ur,
                matched_field=field,
            )
            for verse, surah in rows
        ]
