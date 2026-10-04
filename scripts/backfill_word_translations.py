#!/usr/bin/env python3
"""Backfill words.translation_en / words.transliteration from EQTB (Quranic.csv)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, update  # noqa: E402

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.models.quran import Surah, Verse, Word  # noqa: E402

sys.path.insert(0, str(ROOT_DIR / "scripts"))
from ingest_quran import parse_eqtb  # noqa: E402, N806

logger = get_logger("scripts.backfill_word_translations")


async def main_async(corpus_dir: Path, dry_run: bool) -> None:
    eqtb_path = next(
        (corpus_dir / name for name in ("Quranic.csv", "eqtb.csv", "Quranic.tsv") if (corpus_dir / name).exists()),
        None,
    )
    if eqtb_path is None:
        raise SystemExit(f"EQTB file not found in {corpus_dir}")
    eqtb_words, _ = parse_eqtb(eqtb_path)
    logger.info("Parsed %d EQTB words", len(eqtb_words))

    async with async_session_factory() as session:
        verse_lookup: dict[tuple[int, int], int] = {}
        for vid, sid, ayah in (await session.execute(select(Verse.id, Verse.surah_id, Verse.ayah_number))).all():
            surah_number = (await session.get(Surah, sid)).number  # type: ignore[union-attr]
            verse_lookup[(surah_number, ayah)] = vid

        updated = 0
        for (s, a, w), info in eqtb_words.items():
            translation = info["translation_en"] if isinstance(info["translation_en"], str) else None
            translit = info["transliteration"] if isinstance(info["transliteration"], str) else None
            if translation is None and translit is None:
                continue
            vid = verse_lookup.get((s, a))
            if vid is None:
                continue
            result = await session.execute(
                update(Word)
                .where(Word.verse_id == vid, Word.position == w)
                .where((Word.translation_en.is_(None)) | (Word.transliteration.is_(None)))
                .values(translation_en=translation, transliteration=translit)
            )
            updated += result.rowcount or 0
            if updated and updated % 10000 < 1:
                logger.info("Updated %d words so far", updated)
        if dry_run:
            await session.rollback()
            logger.info("Dry run: %d words would be updated", updated)
        else:
            await session.commit()
            logger.info("Updated %d words", updated)
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default=str(ROOT_DIR / "data" / "corpus"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    setup_logging(level="INFO")
    asyncio.run(main_async(Path(args.corpus_dir), args.dry_run))


if __name__ == "__main__":
    main()
