#!/usr/bin/env python3
"""Jawhar — backfill Nahw syntax fields from the Extended Quranic Treebank.

Existing ``nahw_annotations`` rows were ingested before ``head_index`` was read
from EQTB (it was stored empty) and before ``sentence_index`` existed. This
script recomputes, from the same local ``Quranic.csv`` source:

* ``head_index``  — word-level dependency head: ``>= 1`` is the head's position
  in the verse named by ``head_surah_number``/``head_ayah_number``, ``-1`` means
  no separate head word (sentence root or a clitic of the same word) and ``0``
  means the head is an elided element EQTB records as a ``word_id`` 0 placeholder,
* ``head_surah_number`` / ``head_ayah_number`` — the verse the head position
  belongs to (EQTB sentences may span verses), null when ``head_index <= 0``,
* ``sentence_index`` — EQTB sentence id (sentences may span verse boundaries),
* ``irab`` — classical Arabic term (مرفوع/منصوب/مجرور/مجزوم) instead of the raw
  English ``NOM``/``ACC``/``GEN`` shorthand.

Nothing is guessed: every value comes from the corpus file, and the run prints a
reconciliation report (rows updated, rows whose derived values already matched,
and any stored (verse, token) pairs with no corpus row). Rerun-safe: it updates
in place and is idempotent.

Usage:
    uv run python ../scripts/backfill_nahw_syntax.py
    uv run python ../scripts/backfill_nahw_syntax.py --dry-run
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

from sqlalchemy import select  # noqa: E402

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402
from app.models.quran import NahwAnnotation, Surah, Verse  # noqa: E402
from app.services.nahw_backfill import derive_word_annotations  # noqa: E402

logger = get_logger("scripts.backfill_nahw_syntax")

DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "corpus"


def load_eqtb_rows(path: Path) -> list[dict[str, str]]:
    """Read the raw EQTB TSV rows (UTF-16), keeping sentence-level rows."""
    with path.open(encoding="utf-16", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


async def backfill(*, corpus_dir: Path, dry_run: bool) -> dict[str, int]:
    source = corpus_dir / "Quranic.csv"
    if not source.exists():
        raise SystemExit(f"EQTB source not found: {source}")

    derived = {
        (a.surah, a.ayah, a.position): a
        for a in derive_word_annotations(load_eqtb_rows(source))
    }
    logger.info("Derived %d word annotations from %s", len(derived), source.name)

    counts = defaultdict(int)
    async with async_session_factory() as session:
        verse_keys: dict[int, tuple[int, int]] = {}
        for verse_id, surah_number, ayah_number in (
            await session.execute(
                select(Verse.id, Surah.number, Verse.ayah_number).join(
                    Surah, Verse.surah_id == Surah.id
                )
            )
        ).all():
            verse_keys[verse_id] = (surah_number, ayah_number)

        rows = (
            await session.execute(select(NahwAnnotation).order_by(NahwAnnotation.id))
        ).scalars().all()
        logger.info("Loaded %d stored nahw annotations", len(rows))

        for row in rows:
            key = verse_keys.get(row.verse_id)
            if key is None:
                counts["verse_not_in_corpus"] += 1
                continue
            ann = derived.get((key[0], key[1], row.token_index))
            if ann is None:
                counts["no_corpus_row"] += 1
                continue
            changed = (
                row.head_index != ann.head_index
                or row.head_surah_number != ann.head_surah
                or row.head_ayah_number != ann.head_ayah
                or row.sentence_index != ann.sentence_index
                or row.irab != ann.irab
            )
            if not changed:
                counts["unchanged"] += 1
                continue
            row.head_index = ann.head_index
            row.head_surah_number = ann.head_surah
            row.head_ayah_number = ann.head_ayah
            row.sentence_index = ann.sentence_index
            row.irab = ann.irab
            counts["updated"] += 1

        if dry_run:
            await session.rollback()
            logger.info("Dry run: no changes written")
        else:
            await session.commit()
            logger.info("Committed backfill")

    counts["derived_total"] = len(derived)
    counts["stored_total"] = len(rows)
    for key in ("updated", "unchanged", "no_corpus_row", "verse_not_in_corpus"):
        counts.setdefault(key, 0)
    return dict(counts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()

    setup_logging()
    counts = asyncio.run(backfill(corpus_dir=args.corpus_dir, dry_run=args.dry_run))

    print("\nNahw syntax backfill report")
    print("=" * 40)
    for key in (
        "derived_total",
        "stored_total",
        "updated",
        "unchanged",
        "no_corpus_row",
        "verse_not_in_corpus",
    ):
        print(f"  {key:<20} {counts.get(key, 0)}")


if __name__ == "__main__":
    main()
