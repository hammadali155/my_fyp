#!/usr/bin/env python3
"""Print the exact Quran context block that would be sent to the model for a
message. Read-only: builds from the local corpus and never calls an LLM."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import async_session_factory, engine  # noqa: E402
from app.services.tutor_context import ContextReference, TutorContextService  # noqa: E402


async def run(args: argparse.Namespace) -> int:
    reference = None
    if args.word_id is not None:
        reference = ContextReference(word_id=args.word_id)
    elif args.surah is not None:
        reference = ContextReference(surah_number=args.surah, ayah_number=args.ayah)

    async with async_session_factory() as session:
        result = await TutorContextService(session).build(
            message=args.message,
            languages=tuple(args.lang),
            reference=reference,
            max_chars=args.max_chars,
        )

    if args.json:
        print(
            json.dumps(
                {
                    "text": result.text,
                    "citations": [citation.as_dict() for citation in result.citations],
                    "unresolved_references": result.unresolved_references,
                    "truncated": result.truncated,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(result.text)
        print()
        print(f"citations: {[citation.as_dict() for citation in result.citations]}")
        print(f"unresolved: {result.unresolved_references}")
        print(f"truncated: {result.truncated}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="the learner's message")
    parser.add_argument("--surah", type=int, help="explicit surah number")
    parser.add_argument("--ayah", type=int, help="explicit ayah number (default 1)")
    parser.add_argument("--word-id", type=int, help="explicit word id")
    parser.add_argument(
        "--lang",
        action="append",
        default=None,
        help="translation language code; repeatable (default: en)",
    )
    parser.add_argument("--max-chars", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.lang is None:
        args.lang = ["en"]
    try:
        return asyncio.run(run(args))
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    raise SystemExit(main())
