from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
SCRIPTS_DIR = ROOT_DIR / "scripts"
for p in (str(BACKEND_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ingest_quran  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.models.quran import NahwAnnotation, Surah, Verse, Word  # noqa: E402

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"


def make_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def count(session: AsyncSession, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


@pytest.mark.asyncio
async def test_ingest_counts_and_grouping():
    engine, factory = make_session_factory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        inserted = await ingest_quran.ingest(session, FIXTURE_CORPUS)
        assert inserted == {"surahs": 2, "verses": 3, "words": 5, "nahw_annotations": 3}
        assert await count(session, Surah) == 2
        assert await count(session, Verse) == 3
        assert await count(session, Word) == 5
        assert await count(session, NahwAnnotation) == 3

        # morphology segments merged into one word per orthographic word
        w = (
            await session.execute(
                select(Word).where(Word.verse_id == 1, Word.position == 1)
            )
        ).scalar_one()
        assert w.text_uthmani == "بِسْمِ"
        assert w.root == "سمو"
        assert w.lemma == "اسْم"
        assert w.pos_tag == "P"
        assert len(w.features_json["segments"]) == 2

        # nahw annotation linked to its word
        ann = (
            await session.execute(
                select(NahwAnnotation).where(NahwAnnotation.token_index == 2, NahwAnnotation.verse_id == 1)
            )
        ).scalar_one()
        assert ann.word_id is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_ingest_is_idempotent():
    engine, factory = make_session_factory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        await ingest_quran.ingest(session, FIXTURE_CORPUS)
        second = await ingest_quran.ingest(session, FIXTURE_CORPUS)
        assert second == {"surahs": 0, "verses": 0, "words": 0, "nahw_annotations": 0}
        assert await count(session, Surah) == 2
        assert await count(session, Verse) == 3
        assert await count(session, Word) == 5
        assert await count(session, NahwAnnotation) == 3
    await engine.dispose()


@pytest.mark.asyncio
async def test_dry_run_writes_nothing():
    engine, factory = make_session_factory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        inserted = await ingest_quran.ingest(session, FIXTURE_CORPUS, dry_run=True)
        assert inserted["verses"] == 3
        assert await count(session, Verse) == 0
        assert await count(session, Word) == 0
        assert await count(session, NahwAnnotation) == 0
    await engine.dispose()


@pytest.mark.asyncio
async def test_limit_surahs():
    engine, factory = make_session_factory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        inserted = await ingest_quran.ingest(session, FIXTURE_CORPUS, limit_surahs=1)
        assert inserted["surahs"] == 1
        assert inserted["verses"] == 2
        assert await count(session, Surah) == 1
        assert await count(session, Verse) == 2
    await engine.dispose()


def test_parse_tanzil_text_preserves_text():
    rows = ingest_quran.parse_tanzil_text(FIXTURE_CORPUS / "quran-uthmani.txt")
    assert rows[(1, 1)] == "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    assert len(rows) == 3
