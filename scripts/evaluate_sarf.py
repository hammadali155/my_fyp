#!/usr/bin/env python3
"""Evaluate Sarf (root) extraction accuracy against our gold corpus.

Samples 500 words (fixed seed 42) from `words` where root is known,
runs the analyzer on the undiacritized (imlaei) form, and reports
root accuracy overall and by gold pos_tag. Errors go to a CSV.

The analyzer path under test is: CAMeL (if installed) with rule-based
fallback, bypassing the corpus lookup that `analyze_word` prefers —
otherwise the "evaluation" would trivially reuse gold data.
"""

from __future__ import annotations

import argparse
import csv
import random
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
for p in (str(BACKEND_DIR), str(ROOT_DIR / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.camel_service import analyze_with_camel, camel_available, map_camel_output  # noqa: E402
from app.services.morphology_service import normalize_arabic, strip_tashkeel  # noqa: E402

PRD_TARGET = 0.90


async def _predict_via_endpoint(words: list[str]) -> list[tuple[str | None, str]]:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.morphology_service import MorphologyService

    engine = create_async_engine(f"sqlite+aiosqlite:///{BACKEND_DIR / 'jawhar.db'}")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    out: list[tuple[str | None, str]] = []
    async with factory() as session:
        service = MorphologyService(session)
        for w in words:
            res = await service.analyze_word(w)
            out.append((res.get("root"), res.get("source", "rules")))
    await engine.dispose()
    return out


def predict_root(word: str, use_bert: bool = False) -> tuple[str | None, str]:
    if use_bert:
        from app.services.camel_service import analyze_with_bert

        raw = analyze_with_bert(word)
        if raw is not None:
            mapped = map_camel_output(raw, word)
            return mapped["root"], "bert"
        return None, "none"
    raw = analyze_with_camel(word)
    if raw is not None:
        mapped = map_camel_output(raw, word)
        return mapped["root"], "camel"
    return None, "none"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=str(ROOT_DIR / "sarf_eval_errors.csv"))
    parser.add_argument("--analyzer-only", action="store_true", help="Bypass corpus lookup; measure CAMeL/rules only")
    parser.add_argument("--bert", action="store_true", help="Use BERT disambiguator instead of raw first-analysis")
    args = parser.parse_args()

    conn = sqlite3.connect(BACKEND_DIR / "jawhar.db")
    rows = conn.execute(
        "SELECT id, text_imlaei, root, pos_tag FROM words WHERE root IS NOT NULL AND text_imlaei IS NOT NULL AND text_imlaei != ''"
    ).fetchall()
    conn.close()
    assert len(rows) >= args.sample, f"need at least {args.sample} gold words, got {len(rows)}"

    sample = random.Random(args.seed).sample(rows, args.sample)
    print(f"camel available: {camel_available()}; sample: {len(sample)}; seed: {args.seed}")

    if args.analyzer_only:
        predictions = [predict_root(strip_tashkeel(text), use_bert=args.bert) for _id, text, gold_root, pos_tag in sample]
    else:
        import asyncio

        predictions = asyncio.run(_predict_via_endpoint([text for _id, text, _g, _p in sample]))

    errors = []
    by_pos: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    correct = 0
    t0 = time.time()
    for i, ((_id, text, gold_root, pos_tag), (pred, source)) in enumerate(zip(sample, predictions, strict=True)):
        gold_n = normalize_arabic(gold_root)
        pred_n = normalize_arabic(pred) if pred else ""
        ok = pred_n != "" and pred_n == gold_n
        if ok:
            correct += 1
        else:
            errors.append({"word": text, "gold_root": gold_root, "predicted_root": pred or "", "pos_tag": pos_tag or "", "source": source})
        key = pos_tag or "?"
        by_pos[key][0] += int(ok)
        by_pos[key][1] += 1
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(sample)} done, accuracy so far {correct / (i + 1):.3f}")

    elapsed = time.time() - t0
    acc = correct / len(sample)
    print(f"\nOverall root accuracy: {correct}/{len(sample)} = {acc:.3f} (PRD target {PRD_TARGET:.2f}) -> {'PASS' if acc >= PRD_TARGET else 'BELOW TARGET'}")
    print(f"Elapsed: {elapsed:.1f}s")
    print("\nBy gold pos_tag:")
    for pos, (c, n) in sorted(by_pos.items(), key=lambda kv: -kv[1][1]):
        print(f"  {pos:>6}: {c}/{n} = {c / n:.3f}")

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["word", "gold_root", "predicted_root", "pos_tag", "source"])
        w.writeheader()
        w.writerows(errors)
    print(f"\nErrors written to {args.out}: {len(errors)} rows")


if __name__ == "__main__":
    main()
