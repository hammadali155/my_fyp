#!/usr/bin/env python3
"""Seed the learning-path lessons from the stored Quran corpus.

One lesson per real root, ranked by total word occurrences. Bands are
beginner ranks 1-40, intermediate 41-120, advanced 121-300. All lesson
content (forms, glosses, example verse) is read from the words/verses
tables; nothing is hand-written.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.logging import setup_logging  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.services.lesson_seed import (  # noqa: E402
    MIN_ROOT_OCCURRENCES,
    seed_lessons,
)


async def run(args: argparse.Namespace) -> None:
    async with async_session_factory() as session:
        result = await seed_lessons(
            session, min_occurrences=args.min_occurrences
        )
        await session.commit()
        print(
            f"lessons={result['lessons']} lesson_words={result['words']} "
            f"ranked_roots={result['roots']}"
        )
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed learning-path lessons from the Quran corpus"
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=MIN_ROOT_OCCURRENCES,
        help="Minimum root occurrences to qualify for a lesson",
    )
    args = parser.parse_args()
    setup_logging(level="INFO")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
