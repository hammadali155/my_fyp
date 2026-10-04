#!/usr/bin/env python3
"""Smoke test: run CAMeL Tools Analyzer on 5 words sampled from our words table."""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from camel_tools.morphology.analyzer import Analyzer
from camel_tools.morphology.database import MorphologyDB

DB = Path(__file__).resolve().parent.parent / "backend" / "jawhar.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT text_uthmani FROM words WHERE text_uthmani IS NOT NULL AND text_uthmani != '' ORDER BY RANDOM() LIMIT 5"
    ).fetchall()
    conn.close()
    words = [r[0] for r in rows]

    db = MorphologyDB.builtin_db()
    analyzer = Analyzer(db)

    for w in words:
        analyses = analyzer.analyze(w)
        print(f"=== {w} -> {len(analyses)} analyses ===")
        if not analyses:
            continue
        first = analyses[0]
        print("  keys:", sorted(first.keys()))
        for key in ("root", "pattern", "pos", "cat", "stem", "gloss"):
            if key in first:
                print(f"  {key}: {first[key]}")
        print("  features:", first)
        break
    print()
    for w in words:
        analyses = analyzer.analyze(w)
        if not analyses:
            print(f"{w}: <no analysis>")
            continue
        first = analyses[0]
        print(
            f"{w}: root={first.get('root')!r} pos={first.get('pos')!r} "
            f"pattern={first.get('pattern')!r} lemma={first.get('lemma')!r}"
        )


if __name__ == "__main__":
    main()
