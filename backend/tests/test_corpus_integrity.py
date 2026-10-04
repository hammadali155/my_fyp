from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import engine
from app.models.quran import NahwAnnotation, Surah, Verse, Word

pytestmark = pytest.mark.slow

session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _verse_count() -> int:
    async with session_factory() as session:
        return (await session.execute(select(func.count()).select_from(Verse))).scalar_one()


@pytest.fixture
async def real_db() -> AsyncSession:
    if (await _verse_count()) < 6236:
        pytest.skip("Database does not contain the full corpus (< 6,236 verses)")
    async with session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_total_counts(real_db: AsyncSession):
    surahs = (await real_db.execute(select(func.count()).select_from(Surah))).scalar_one()
    verses = (await real_db.execute(select(func.count()).select_from(Verse))).scalar_one()
    words = (await real_db.execute(select(func.count()).select_from(Word))).scalar_one()
    annotations = (await real_db.execute(select(func.count()).select_from(NahwAnnotation))).scalar_one()
    assert surahs == 114
    assert verses == 6236
    # source datasets yield 77,429 orthographic words (the "77,430" doc figure
    # counts the sentence-level basmala placeholder we deliberately exclude)
    assert words == 77429
    assert annotations > 0


@pytest.mark.asyncio
async def test_every_verse_has_at_least_one_word(real_db: AsyncSession):
    result = await real_db.execute(
        select(Verse.id)
        .outerjoin(Word, Word.verse_id == Verse.id)
        .group_by(Verse.id)
        .having(func.count(Word.id) == 0)
    )
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_no_word_has_empty_text(real_db: AsyncSession):
    result = await real_db.execute(
        select(func.count()).select_from(Word).where(
            (Word.text_uthmani.is_(None)) | (Word.text_uthmani == "")
        )
    )
    assert result.scalar_one() == 0


@pytest.mark.asyncio
async def test_surah_structure(real_db: AsyncSession):
    s1 = (
        await real_db.execute(
            select(func.count()).select_from(Verse).join(Surah, Verse.surah_id == Surah.id).where(Surah.number == 1)
        )
    ).scalar_one()
    s114 = (
        await real_db.execute(
            select(func.count()).select_from(Verse).join(Surah, Verse.surah_id == Surah.id).where(Surah.number == 114)
        )
    ).scalar_one()
    assert s1 == 7
    assert s114 == 6


@pytest.mark.asyncio
async def test_nahw_annotations_reference_existing_verses(real_db: AsyncSession):
    result = await real_db.execute(
        select(func.count())
        .select_from(NahwAnnotation)
        .outerjoin(Verse, NahwAnnotation.verse_id == Verse.id)
        .where(Verse.id.is_(None))
    )
    assert result.scalar_one() == 0
