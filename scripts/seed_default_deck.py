#!/usr/bin/env python3
"""Seed a default deck per user containing one card from each of the N most
frequent Quranic roots. Card front = the word's own uthmani text, back = the
word's own translation_en from the words table (never hand-written)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.models.deck import Deck  # noqa: E402
from app.models.quran import Surah, Verse, Word  # noqa: E402
from app.models.srs import SRSCard  # noqa: E402
from app.models.user import User  # noqa: E402

logger = get_logger("scripts.seed_default_deck")

DEFAULT_NAME = "Most Frequent Roots"


async def seed_for_user(session: AsyncSession, user_id: int, limit: int) -> tuple[int, int]:
    existing = (
        await session.execute(
            select(Deck).where(Deck.user_id == user_id, Deck.name == DEFAULT_NAME)
        )
    ).scalar_one_or_none()
    if existing is None:
        deck = Deck(user_id=user_id, name=DEFAULT_NAME, is_default=True)
        session.add(deck)
        await session.flush()
    else:
        deck = existing

    top_roots = (
        await session.execute(
            select(Word.root, func.count(Word.id))
            .where(Word.root.is_not(None))
            .group_by(Word.root)
            .order_by(func.count(Word.id).desc())
            .limit(limit)
        )
    ).all()

    added = 0
    skipped = 0
    for root, _count in top_roots:
        dup = await session.execute(
            select(SRSCard.id).where(
                SRSCard.user_id == user_id,
                SRSCard.deck_id == deck.id,
                SRSCard.hint == root,
            )
        )
        if dup.scalar_one_or_none() is not None:
            skipped += 1
            continue
        candidate = (
            await session.execute(
                select(Word)
                .where(Word.root == root, Word.translation_en.is_not(None), Word.translation_en != "")
                .order_by(Word.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if candidate is None:
            continue
        verse = (
            await session.execute(select(Verse).where(Verse.id == candidate.verse_id))
        ).scalar_one_or_none()
        surah_number = None
        if verse is not None:
            surah = (await session.execute(select(Surah).where(Surah.id == verse.surah_id))).scalar_one_or_none()
            surah_number = surah.number if surah else None
        card = SRSCard(
            user_id=user_id,
            word_id=candidate.id,
            deck_id=deck.id,
            item_type="vocabulary",
            front=candidate.text_uthmani,
            back=candidate.translation_en or "",
            hint=root,
            surah_number=surah_number,
            ayah_number=verse.ayah_number if verse is not None else None,
        )
        session.add(card)
        added += 1
    await session.commit()
    return added, skipped


async def run(args: argparse.Namespace) -> None:
    async with async_session_factory() as session:
        if args.user_id is not None:
            user_ids = [args.user_id]
        else:
            user_ids = [u for (u,) in (await session.execute(select(User.id))).all()]
        for uid in user_ids:
            added, skipped = await seed_for_user(session, uid, args.limit)
            logger.info("user_id=%d: added %d cards, skipped %d existing", uid, added, skipped)
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed default frequent-root deck(s)")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--user-id", type=int, default=None)
    args = parser.parse_args()
    setup_logging(level="INFO")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
