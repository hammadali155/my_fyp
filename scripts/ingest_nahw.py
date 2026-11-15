#!/usr/bin/env python3
"""
Jawhar — Nahw annotations ingestion script.

Reads the Extended Quranic Treebank (Quranic.csv) and inserts rows into
``nahw_annotations`` mapping each treebank token to the correct row in the
``words`` table. This script does not modify the Quranic text or any existing
table content.

Properties:
* Idempotent: rows are keyed by (verse_id, token_index); existing rows are
  left untouched.
* Maps treebank tokens (by word_id) to ``words`` by (surah_id, ayah_number,
  position).
* Inserts in batches of 1,000 rows.
* Fails early with a clear message if the treebank file is missing.
* Prints counts at the end: rows read, rows inserted, rows skipped with reasons.
* Does not drop tokens silently — unmapped tokens are logged and counted.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.models.quran import NahwAnnotation, Surah, Verse, Word  # noqa: E402
from app.services.nahw_backfill import derive_word_annotations  # noqa: E402

logger = get_logger("scripts.ingest_nahw")

BATCH_SIZE = 1000
DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "corpus"
# Treebank file used by ingest scripts
TREEBANK_CANDIDATES = ["Quranic.csv", "eqtb.csv", "Quranic.tsv"]


def find_treebank(corpus_dir: Path) -> Path:
    for name in TREEBANK_CANDIDATES:
        path = corpus_dir / name
        if path.exists():
            return path
    raise SystemExit(
        f"Treebank file not found in {corpus_dir}. "
        f"Expected one of: {', '.join(TREEBANK_CANDIDATES)}"
    )


async def _existing_nahw_keys(session: AsyncSession) -> set[tuple[int, int]]:
    return {
        (vid, idx)
        for vid, idx in (
            await session.execute(
                select(NahwAnnotation.verse_id, NahwAnnotation.token_index)
            )
        ).all()
    }


async def ingest_nahw(
    session: AsyncSession,
    corpus_dir: Path,
    *,
    limit_surahs: int | None = None,
    dry_run: bool = False,
) -> tuple[dict[str, int], list[dict[str, object]]]:
    treebank_path = find_treebank(corpus_dir)
    logger.info("Reading treebank from %s", treebank_path)

    counts: dict[str, int] = defaultdict(int)
    counts["rows_read"] = 0

    # Read all raw rows
    raw_rows: list[dict[str, str]] = []
    with treebank_path.open(encoding="utf-16", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            raw_rows.append(row)
            counts["rows_read"] += 1

    if limit_surahs is not None:
        raw_rows = [r for r in raw_rows if int(r["chapter_id"]) <= limit_surahs]

    # Derive word-level annotations
    derived = {(a.surah, a.ayah, a.position): a for a in derive_word_annotations(raw_rows)}

    verse_pk: dict[tuple[int, int], int] = {}
    for verse_id, surah_number, ayah_number in (
        await session.execute(
            select(Verse.id, Surah.number, Verse.ayah_number).join(
                Surah, Verse.surah_id == Surah.id
            )
        )
    ).all():
        if limit_surahs is None or surah_number <= limit_surahs:
            verse_pk[(surah_number, ayah_number)] = verse_id

    verse_by_id = {verse_id: key for key, verse_id in verse_pk.items()}
    word_pk: dict[tuple[int, int], int] = {}
    for word_id, verse_id, position in (
        await session.execute(select(Word.id, Word.verse_id, Word.position))
    ).all():
        key = verse_by_id.get(verse_id)
        if key and (limit_surahs is None or key[0] <= limit_surahs):
            word_pk[(verse_id, position)] = word_id

    nahw_keys = await _existing_nahw_keys(session)
    unmapped: list[dict[str, object]] = []

    pending = 0
    for (surah_num, ayah_num, word_pos), ann in derived.items():
        if limit_surahs is not None and surah_num > limit_surahs:
            continue
        matched_verse_id = verse_pk.get((surah_num, ayah_num))
        if matched_verse_id is None:
            unmapped.append(
                {
                    "surah": surah_num,
                    "ayah": ayah_num,
                    "word_position": word_pos,
                    "reason": "verse not found in words table",
                }
            )
            counts["rows_skipped_verse_missing"] += 1
            continue
        if (matched_verse_id, word_pos) in nahw_keys:
            counts["rows_skipped_duplicate"] += 1
            continue
        matched_word_id = word_pk.get((matched_verse_id, word_pos))
        if matched_word_id is None:
            unmapped.append(
                {
                    "surah": surah_num,
                    "ayah": ayah_num,
                    "word_position": word_pos,
                    "reason": "word not found in words table (mapping failed)",
                }
            )
            counts["rows_skipped_word_missing"] += 1
            continue

        if not dry_run:
            annotation = NahwAnnotation(
                verse_id=matched_verse_id,
                word_id=matched_word_id,
                token_index=word_pos,
                role=ann.role,
                dep_type=ann.dep_type,
                head_index=ann.head_index,
                head_surah_number=ann.head_surah,
                head_ayah_number=ann.head_ayah,
                irab=ann.irab,
                sentence_index=ann.sentence_index,
            )
            session.add(annotation)
            pending += 1
            nahw_keys.add((matched_verse_id, word_pos))
            counts["rows_inserted"] += 1
            if pending >= BATCH_SIZE:
                await session.flush()
                pending = 0
        else:
            counts["rows_inserted"] += 1  # would insert

    if pending and not dry_run:
        await session.flush()

    if dry_run:
        await session.rollback()
    else:
        await session.commit()

    counts.setdefault("rows_skipped_duplicate", 0)
    counts.setdefault("rows_skipped_verse_missing", 0)
    counts.setdefault("rows_skipped_word_missing", 0)
    counts["rows_skipped_total"] = (
        counts["rows_skipped_duplicate"]
        + counts["rows_skipped_verse_missing"]
        + counts["rows_skipped_word_missing"]
    )
    counts.setdefault("rows_inserted", 0)
    counts["unmapped_tokens"] = len(unmapped)

    if unmapped:
        logger.warning("%d tokens could not be mapped to words table", len(unmapped))
        for item in unmapped[:20]:
            logger.warning(
                "UNMAPPED: surah=%s ayah=%s word_position=%s reason=%s",
                item["surah"],
                item["ayah"],
                item["word_position"],
                item["reason"],
            )
    else:
        logger.info("All derived tokens mapped successfully")

    return dict(counts), unmapped


async def report_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    models = (
        ("surahs", Surah),
        ("verses", Verse),
        ("words", Word),
        ("nahw_annotations", NahwAnnotation),
    )
    for name, model in models:
        counts[name] = (
            await session.execute(select(func.count()).select_from(model))
        ).scalar_one()
    return counts


async def run(args: argparse.Namespace) -> tuple[dict[str, int], list[dict[str, object]]]:
    corpus_dir = Path(args.corpus_dir)
    if not corpus_dir.is_dir():
        raise SystemExit(f"Corpus directory not found: {corpus_dir}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        counts, unmapped = await ingest_nahw(
            session,
            corpus_dir,
            limit_surahs=args.limit_surahs,
            dry_run=args.dry_run,
        )
        db_counts = await report_counts(session)

    logger.info(
        "Ingestion finished (%s): rows_read=%d rows_inserted=%d rows_skipped_total=%d (dup=%d verse_missing=%d word_missing=%d) unmapped=%d | DB totals: nahw_annotations=%d",
        "dry-run" if args.dry_run else "committed",
        counts["rows_read"],
        counts["rows_inserted"],
        counts["rows_skipped_total"],
        counts["rows_skipped_duplicate"],
        counts["rows_skipped_verse_missing"],
        counts["rows_skipped_word_missing"],
        counts["unmapped_tokens"],
        db_counts["nahw_annotations"],
    )

    await engine.dispose()
    return counts, unmapped


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Nahw annotations from EQTB treebank into Jawhar DB.")
    parser.add_argument("--corpus-dir", default=str(DEFAULT_CORPUS_DIR), help="Directory with treebank files")
    parser.add_argument("--limit-surahs", type=int, default=None, help="Only ingest the first N surahs")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing to the DB")
    args = parser.parse_args()
    setup_logging(level="INFO")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
