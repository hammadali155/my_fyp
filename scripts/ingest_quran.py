#!/usr/bin/env python3
"""
Jawhar — Quran Corpus Ingestion Script
Seeds verified Quran Surahs, Verses, and Word tokens into the database.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import sys

# Ensure backend package is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, func, select
from app.core.logging import get_logger, setup_logging
from app.db.base import Base
from app.db.seed_data import SEED_VERSES_DATA, SURAHS_DATA
from app.db.session import async_session_factory, engine
from app.models.quran import Surah, Verse, Word

setup_logging(level="INFO")
logger = get_logger("scripts.ingest_quran")


async def seed_surahs(session) -> dict[int, int]:
    """Seed all 114 Surahs metadata. Returns mapping of surah_number -> surah_id."""
    logger.info("Checking Surahs table...")
    existing = await session.execute(select(Surah))
    surah_map = {s.number: s.id for s in existing.scalars().all()}

    inserted_count = 0
    for s_data in SURAHS_DATA:
        if s_data["number"] not in surah_map:
            surah = Surah(
                number=s_data["number"],
                name_arabic=s_data["name_arabic"],
                name_transliteration=s_data["name_transliteration"],
                name_english=s_data["name_english"],
                revelation_place=s_data["revelation_place"],
                verse_count=s_data["verse_count"],
            )
            session.add(surah)
            inserted_count += 1

    if inserted_count > 0:
        await session.flush()
        logger.info("Inserted %d new Surahs.", inserted_count)
        # Refresh map
        res = await session.execute(select(Surah))
        surah_map = {s.number: s.id for s in res.scalars().all()}
    else:
        logger.info("All 114 Surahs already present in database.")

    return surah_map


async def seed_verses(session, surah_map: dict[int, int]) -> None:
    """Seed initial verified verses and words."""
    logger.info("Seeding verified verses and words...")
    inserted_verses = 0
    inserted_words = 0

    for v_data in SEED_VERSES_DATA:
        surah_id = surah_map.get(v_data["surah_number"])
        if not surah_id:
            logger.warning("Surah %d not found in database, skipping ayah %d", v_data["surah_number"], v_data["ayah_number"])
            continue

        # Check existing verse
        v_check = await session.execute(
            select(Verse).where(Verse.surah_id == surah_id, Verse.ayah_number == v_data["ayah_number"])
        )
        existing_v = v_check.scalar_one_or_none()
        if existing_v:
            continue

        verse = Verse(
            surah_id=surah_id,
            ayah_number=v_data["ayah_number"],
            text_uthmani=v_data["text_uthmani"],
            text_imlaei=v_data["text_imlaei"],
            translation_en=v_data["translation_en"],
            translation_ur=v_data["translation_ur"],
            juz_number=v_data["juz_number"],
            hizb_number=v_data["hizb_number"],
            page_number=v_data["page_number"],
        )
        session.add(verse)
        await session.flush()
        inserted_verses += 1

        for w_data in v_data.get("words", []):
            word = Word(
                verse_id=verse.id,
                position=w_data["position"],
                text_uthmani=w_data["text_uthmani"],
                text_imlaei=w_data.get("text_imlaei"),
                translation_en=w_data.get("translation_en"),
                transliteration=w_data.get("transliteration"),
                root=w_data.get("root"),
                lemma=w_data.get("lemma"),
                pos_tag=w_data.get("pos_tag"),
            )
            session.add(word)
            inserted_words += 1

    await session.commit()
    logger.info("Ingestion summary: %d verses and %d words inserted.", inserted_verses, inserted_words)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Quran corpus data into Jawhar database.")
    parser.add_argument("--reset", action="store_true", help="Clear existing Quran tables before seeding")
    args = parser.parse_args()

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        if args.reset:
            logger.warning("Reset flag provided. Truncating words, verses, surahs...")
            await session.execute(delete(Word))
            await session.execute(delete(Verse))
            await session.execute(delete(Surah))
            await session.commit()
            logger.info("Cleared existing Quran tables.")

        surah_map = await seed_surahs(session)
        await seed_verses(session, surah_map)

    await engine.dispose()
    logger.info("Quran corpus ingestion completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
