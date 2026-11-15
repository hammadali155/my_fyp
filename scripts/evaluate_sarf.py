#!/usr/bin/env python3
"""Evaluate Sarf (root) extraction accuracy against our gold corpus.

Reports three numbers from one sample (fixed seed):

  (a) accuracy on words whose gold root is a real root — the only number
      compared against the 90% PRD target;
  (b) accuracy on rootless words (gold root = the EQTB placeholder `ـ`) —
      a prediction counts as correct here only when it is empty/None,
      i.e. the analyzer abstained instead of inventing a root;
  (c) combined (a)+(b).

By default the corpus is never consulted (--analyzer-only is the default):
the analyzer runs on the undiacritized (imlaei) form of each sampled word.
--via-endpoint opts back into the old circular behaviour, where
MorphologyService.analyze_word looks roots up in the gold corpus itself.

Scoring: predictions first pass through camel_service.convert_weak_placeholders
(CAMeL writes `#` for weak radicals it leaves unspecified); a `#` that cannot
be resolved from the lemma is compared as a wildcard over weak letters by
morphology_service.score_root_prediction, and how many correct real-root
matches relied on that wildcard is reported.

--pos and --min-length restrict the eligible pool before sampling; skipped
word counts (with reasons) are printed with the sample size and seed.
With --bert the sample words are grouped by verse and each verse's stored
text is disambiguated in a single BERT call (words keep their context);
words of verses whose token count disagrees with the stored word count
fall back to the single-word path, and the fallback counts are printed.
--lemma-remap replaces a real CAMeL root with the train-split gold root
recorded for its analysis lemma (camel_service.remap_root_by_lemma) —
corpus-assisted prediction, counted and attributed in the analyzer column
(+lemma-remap), never presented as analyzer output. --heldout-surahs
LOW-HIGH evaluates every eligible word of that surah range while excluding
the range from the lexicon and the lemma->root map (held-out discipline).
Errors go to a CSV with the original columns plus predicted_raw (the
analyzer's output before normalisation) and analyzer (which analyzer
produced the answer).
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
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
for p in (str(BACKEND_DIR), str(ROOT_DIR / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.camel_service import (  # noqa: E402
    EVAL_SURAH_SQL,
    _get_lexicon,
    _has_real_root,
    analyze_with_bert,
    analyze_with_camel,
    camel_available,
    convert_weak_placeholders,
    disambiguate_verse_with_bert,
    remap_root_by_lemma,
    set_lexicon_exclusion,
)
from app.services.morphology_service import (  # noqa: E402
    is_rootless_gold,
    normalize_arabic,
    score_root_prediction,
    strip_tashkeel,
)

PRD_TARGET = 0.90
ERROR_FIELDS = ["word", "gold_root", "predicted_root", "pos_tag", "source", "predicted_raw", "analyzer"]


async def _predict_via_endpoint(words: list[str]) -> list[dict[str, Any]]:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.morphology_service import MorphologyService

    engine = create_async_engine(f"sqlite+aiosqlite:///{BACKEND_DIR / 'jawhar.db'}")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    out: list[dict[str, Any]] = []
    async with factory() as session:
        service = MorphologyService(session)
        for w in words:
            res = await service.analyze_word(w)
            source = str(res.get("source", "rules"))
            features = res.get("features_json")
            lex = features.get("lex") if isinstance(features, dict) else None
            analyzer = {"corpus": "corpus", "camel": "camel-analyzer"}.get(source, "rules")
            out.append({"raw": res.get("root") or "", "lex": lex, "source": source, "analyzer": analyzer})
    await engine.dispose()
    return out


def predict_analyzer(text: str, use_bert: bool, rank: bool = True, remap: bool = False) -> dict[str, Any]:
    """Analyzer-only prediction: the corpus is never consulted.

    ``rank=False`` selects the old first-usable analysis behaviour instead
    of the lexicon-ranked pick. ``remap=True`` applies the train-split
    lemma->root remap (``camel_service.remap_root_by_lemma``) and appends
    ``+lemma-remap`` to the analyzer label whenever the root was replaced,
    so remapped answers are never attributed to the analyzer itself.
    """
    stripped = strip_tashkeel(text)
    if use_bert:
        raw = analyze_with_bert(stripped, rank=rank)
        if raw is None:
            return {"raw": "", "lex": None, "source": "none", "analyzer": "none"}
        # Attribute the answer: analyze_with_bert falls back to the plain
        # analyzer on OOV words, and that path caches its analysis under
        # this same word — the identical object proves which analyzer spoke.
        plain = analyze_with_camel(stripped, rank=rank)
        analyzer = "camel-analyzer" if plain is not None and plain is raw else "camel-bert"
        remapped = False
        if remap:
            new_raw = remap_root_by_lemma(raw)
            remapped = new_raw is not raw
            raw = new_raw if remapped else raw
            if remapped:
                analyzer += "+lemma-remap"
        return {
            "raw": raw.get("root") or "",
            "lex": raw.get("lex"),
            "source": "bert",
            "analyzer": analyzer,
            "remapped": remapped,
        }
    raw = analyze_with_camel(stripped, rank=rank)
    if raw is None:
        return {"raw": "", "lex": None, "source": "none", "analyzer": "none"}
    analyzer = "camel-analyzer"
    remapped = False
    if remap:
        new_raw = remap_root_by_lemma(raw)
        remapped = new_raw is not raw
        raw = new_raw if remapped else raw
        if remapped:
            analyzer += "+lemma-remap"
    return {
        "raw": raw.get("root") or "",
        "lex": raw.get("lex"),
        "source": "camel",
        "analyzer": analyzer,
        "remapped": remapped,
    }


def _predict_bert_by_verse(
    sample: list[tuple[str, str, str | None, int, int]], *, rank: bool, remap: bool = False
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """BERT predictions with one disambiguation call per sampled verse.

    Groups the sample by verse, disambiguates each verse's stored text in a
    single call (every word keeps its context) and reads each word's answer
    at its position. Falls back to the single-word path (predict_analyzer
    with use_bert=True) for every word of a verse whose token count
    disagrees with the stored word count, and per word when the position's
    analysis is missing or has a placeholder root. ``remap`` applies the
    train-split lemma->root remap on every path (see predict_analyzer).
    Returns the predictions
    plus counters: verses_run, verse_words, verse_fallbacks (verses on the
    token-count-mismatch path), verse_fallback_words (sample words affected
    by those), verse_disambig_failed (verses whose BERT call failed),
    word_fallbacks (words whose position analysis was missing/unusable).
    """
    conn = sqlite3.connect(BACKEND_DIR / "jawhar.db")
    verse_text = dict(conn.execute("SELECT id, text_imlaei FROM verses").fetchall())
    stored_count = dict(
        conn.execute("SELECT verse_id, COUNT(*) FROM words GROUP BY verse_id").fetchall()
    )
    conn.close()

    grouped: dict[int, list[int]] = defaultdict(list)
    for idx, (_t, _g, _p, verse_id, _wp) in enumerate(sample):
        grouped[verse_id].append(idx)

    stats: dict[str, int] = defaultdict(int)
    picks: dict[int, dict[str, Any]] = {}
    for verse_id, indices in grouped.items():
        text = verse_text.get(verse_id)
        tokens = text.split() if text else []
        if len(tokens) != stored_count.get(verse_id):
            stats["verse_fallbacks"] += 1
            stats["verse_fallback_words"] += len(indices)
            for idx in indices:
                picks[idx] = predict_analyzer(sample[idx][0], True, rank=rank, remap=remap)
            continue
        analyses = disambiguate_verse_with_bert(text)
        if analyses is None:
            stats["verse_disambig_failed"] += 1
            for idx in indices:
                picks[idx] = predict_analyzer(sample[idx][0], True, rank=rank, remap=remap)
            continue
        if len(analyses) != stored_count[verse_id]:
            stats["verse_fallbacks"] += 1
            stats["verse_fallback_words"] += len(indices)
            for idx in indices:
                picks[idx] = predict_analyzer(sample[idx][0], True, rank=rank, remap=remap)
            continue
        stats["verses_run"] += 1
        stats["verse_words"] += len(indices)
        for idx in indices:
            word = sample[idx][0]
            word_pos = sample[idx][4]
            analysis = analyses.get(word_pos)
            if analysis is not None and _has_real_root(analysis):
                analyzer = "camel-bert"
                remapped = False
                if remap:
                    new_analysis = remap_root_by_lemma(analysis)
                    remapped = new_analysis is not analysis
                    if remapped:
                        analysis = new_analysis
                        analyzer += "+lemma-remap"
                picks[idx] = {
                    "raw": analysis.get("root") or "",
                    "lex": analysis.get("lex"),
                    "source": "bert",
                    "analyzer": analyzer,
                    "remapped": remapped,
                }
            else:
                stats["word_fallbacks"] += 1
                picks[idx] = predict_analyzer(word, True, rank=rank, remap=remap)
    return [picks[i] for i in range(len(sample))], dict(stats)


def main() -> None:
    t_start = time.time()
    parser = argparse.ArgumentParser(description="Root-extraction accuracy against the EQTB gold corpus.")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=str(ROOT_DIR / "sarf_eval_errors.csv"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--analyzer-only",
        action="store_true",
        help="default behaviour: analyze words without consulting the corpus",
    )
    mode.add_argument(
        "--via-endpoint",
        action="store_true",
        help="old circular behaviour: MorphologyService.analyze_word, which looks roots up in the gold corpus",
    )
    parser.add_argument(
        "--bert",
        action="store_true",
        help="use the CAMeL BERT disambiguator, one call per verse (analyzer-only mode)",
    )
    parser.add_argument(
        "--no-lexicon",
        action="store_true",
        help="old behaviour: first usable CAMeL analysis, no lemma/root lexicon ranking",
    )
    parser.add_argument(
        "--split",
        choices=("all", "test"),
        default="all",
        help="'test' samples only even-numbered surahs (the lexicon's train split is excluded); "
        "'all' samples the whole corpus (only valid together with --no-lexicon)",
    )
    parser.add_argument(
        "--lemma-remap",
        action="store_true",
        help="replace a real CAMeL root with the train-split gold root recorded for its lemma "
        "(corpus-assisted; remapped predictions are counted and labelled +lemma-remap)",
    )
    parser.add_argument(
        "--heldout-surahs",
        metavar="LOW-HIGH",
        default=None,
        help="evaluate every eligible word of this surah range, excluding the range from the "
        "lexicon and the lemma->root map (e.g. 100-114); overrides --sample and --split",
    )
    parser.add_argument("--pos", help="only sample words whose gold pos_tag equals this value (e.g. N, V, P)")
    parser.add_argument(
        "--min-length",
        type=int,
        default=0,
        help="only sample words whose undiacritized text is at least N characters",
    )
    args = parser.parse_args()

    heldout: tuple[int, int] | None = None
    if args.heldout_surahs:
        try:
            lo_str, hi_str = args.heldout_surahs.split("-", 1)
            heldout = (int(lo_str), int(hi_str))
        except ValueError:
            parser.error("--heldout-surahs expects LOW-HIGH, e.g. 100-114")
        if heldout[0] > heldout[1]:
            parser.error("--heldout-surahs expects LOW <= HIGH")
        if args.via_endpoint:
            parser.error(
                "--heldout-surahs with --via-endpoint would read the held-out words back "
                "from the corpus (direct leakage); use analyzer-only modes"
            )
        set_lexicon_exclusion(heldout)

    if heldout is None and args.split == "all" and not args.no_lexicon:
        parser.error(
            "the lexicon sets are built from train (odd-numbered) surahs; sampling all surahs "
            "would include their gold labels in the sample. Use --split test, or --no-lexicon "
            "for the old first-analysis behaviour."
        )
    if args.lemma_remap and heldout is None and args.split == "all":
        parser.error(
            "the lemma->root map is built from train (odd-numbered) surahs; sampling all surahs "
            "would let a word's own lemma root answer it. Use --split test or --heldout-surahs."
        )

    via_endpoint = args.via_endpoint
    use_bert = args.bert and not via_endpoint
    if via_endpoint:
        mode_name = "via-endpoint (MorphologyService.analyze_word — consults the gold corpus)"
    elif use_bert:
        mode_name = "analyzer-only (CAMeL BERT disambiguator, whole-verse context)"
    else:
        mode_name = "analyzer-only (CAMeL plain analyzer)"
    if args.lemma_remap:
        mode_name += " + train-split lemma->root remap"
    print(f"mode: {mode_name}")
    if via_endpoint and args.bert:
        print("note: --bert is ignored in via-endpoint mode")
    if via_endpoint and not args.no_lexicon:
        print("note: the lexicon ranking flag does not change the endpoint's internal analyzer calls")
    print(f"camel available: {camel_available()}")
    if args.no_lexicon:
        print("lexicon ranking: off (old first-usable behaviour)")
    else:
        lemmas, roots, lemma_roots = _get_lexicon()
        train_desc = "train = odd-numbered surahs"
        if heldout:
            train_desc += f" minus held-out surahs {heldout[0]}-{heldout[1]}"
        print(
            f"lexicon ranking: on ({train_desc}; {len(lemmas)} lemma keys, "
            f"{len(roots)} root keys, {len(lemma_roots)} lemma->root entries)"
        )
    if heldout:
        print(f"held-out: surahs {heldout[0]}-{heldout[1]} (every eligible word; excluded from the lexicon)")
    else:
        print("split: test (even-numbered surahs only)" if args.split == "test" else "split: all surahs")

    conn = sqlite3.connect(BACKEND_DIR / "jawhar.db")
    if heldout:
        rows = conn.execute(
            "SELECT w.text_imlaei, w.root, w.pos_tag, w.verse_id, w.position FROM words w"
            " JOIN verses v ON w.verse_id = v.id"
            " JOIN surahs s ON v.surah_id = s.id"
            " WHERE s.number BETWEEN ? AND ?",
            heldout,
        ).fetchall()
    elif args.split == "test":
        rows = conn.execute(
            "SELECT w.text_imlaei, w.root, w.pos_tag, w.verse_id, w.position FROM words w"
            " JOIN verses v ON w.verse_id = v.id"
            " JOIN surahs s ON v.surah_id = s.id"
            f" WHERE {EVAL_SURAH_SQL}"
        ).fetchall()
    else:
        rows = conn.execute("SELECT text_imlaei, root, pos_tag, verse_id, position FROM words").fetchall()
    conn.close()

    skipped = {"missing text": 0, "missing gold root": 0, "filtered by --pos": 0, "filtered by --min-length": 0}
    pool: list[tuple[str, str, str | None, int, int]] = []
    for text, root, pos, verse_id, word_pos in rows:
        if not text or not text.strip():
            skipped["missing text"] += 1
            continue
        if root is None or not root.strip():
            skipped["missing gold root"] += 1
            continue
        if args.pos is not None and (pos or "") != args.pos:
            skipped["filtered by --pos"] += 1
            continue
        if args.min_length and len(strip_tashkeel(text)) < args.min_length:
            skipped["filtered by --min-length"] += 1
            continue
        pool.append((text, root, pos, verse_id, word_pos))

    if heldout:
        sample_size = len(pool)
    else:
        sample_size = args.sample
        if len(pool) < sample_size:
            print(f"note: pool has only {len(pool)} eligible words; sampling all of them")
            sample_size = len(pool)
    sample = random.Random(args.seed).sample(pool, sample_size) if sample_size else []
    n_rootless = sum(1 for _t, g, _p, _v, _wp in sample if is_rootless_gold(g))
    print(f"seed: {args.seed}; sample size: {len(sample)} of {len(pool)} eligible words")
    print("skipped: " + ", ".join(f"{count} {reason}" for reason, count in skipped.items()))
    print(f"sample: {len(sample) - n_rootless} real-root words, {n_rootless} rootless words (gold = ـ)")
    if not sample:
        print("no eligible words — nothing to evaluate")
        return

    if via_endpoint:
        import asyncio

        predictions = asyncio.run(_predict_via_endpoint([t for t, _g, _p, _v, _wp in sample]))
    elif use_bert:
        predictions, bert_stats = _predict_bert_by_verse(sample, rank=not args.no_lexicon, remap=args.lemma_remap)
        print(
            "verse batching: "
            f"{bert_stats.get('verses_run', 0)} verses disambiguated in one call "
            f"({bert_stats.get('verse_words', 0)} sample words); "
            f"{bert_stats.get('verse_fallbacks', 0)} verses fell back to the single-word path "
            f"(token-count mismatch, {bert_stats.get('verse_fallback_words', 0)} sample words); "
            f"{bert_stats.get('verse_disambig_failed', 0)} verses fell back (BERT verse call failed); "
            f"{bert_stats.get('word_fallbacks', 0)} words fell back (missing/unusable position analysis)"
        )
    else:
        predictions = [
            predict_analyzer(t, False, rank=not args.no_lexicon, remap=args.lemma_remap)
            for t, _g, _p, _v, _wp in sample
        ]

    if args.lemma_remap:
        remap_hits = sum(1 for p in predictions if p.get("remapped"))
        print(f"lemma-remap: {remap_hits} of {len(sample)} predictions had their root replaced from the train-split map")

    errors: list[dict[str, Any]] = []
    by_pos: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    correct_a = correct_b = wildcard_hits = n_a = n_b = 0
    for i, ((text, gold, pos, _verse_id, _word_pos), pred) in enumerate(zip(sample, predictions, strict=True)):
        converted = convert_weak_placeholders(pred["raw"] or None, pred.get("lex"))
        ok, wildcard = score_root_prediction(gold, converted)
        if is_rootless_gold(gold):
            n_b += 1
            correct_b += int(ok)
        else:
            n_a += 1
            correct_a += int(ok)
            wildcard_hits += int(ok and wildcard)
            key = pos or "?"
            by_pos[key][0] += int(ok)
            by_pos[key][1] += 1
        if not ok:
            errors.append(
                {
                    "word": text,
                    "gold_root": gold,
                    "predicted_root": normalize_arabic(converted).replace(".", "") if converted else "",
                    "pos_tag": pos or "",
                    "source": pred["source"],
                    "predicted_raw": pred["raw"] or "",
                    "analyzer": pred["analyzer"],
                }
            )
        if (i + 1) % 100 == 0:
            running = f"{correct_a}/{n_a}" if n_a else "n/a"
            print(f"  {i + 1}/{len(sample)} done, real-root accuracy so far {running}")

    elapsed = time.time() - t_start
    acc_a = correct_a / n_a if n_a else None
    acc_b = correct_b / n_b if n_b else None
    print()
    if acc_a is None:
        print("(a) real-root words: none in sample — 90% target not evaluated")
    else:
        verdict = "PASS" if acc_a >= PRD_TARGET else "BELOW TARGET"
        print(f"(a) real-root accuracy: {correct_a}/{n_a} = {acc_a:.3f} (PRD target {PRD_TARGET:.2f}) -> {verdict}")
    if acc_b is None:
        print("(b) rootless words: none in sample")
    else:
        print(f"(b) rootless accuracy (correct only if no root predicted): {correct_b}/{n_b} = {acc_b:.3f}")
    combined = (correct_a + correct_b) / len(sample)
    print(f"(c) combined: {correct_a + correct_b}/{len(sample)} = {combined:.3f}")
    print(f"real-root matches that relied on the weak-'#' wildcard: {wildcard_hits}")
    print(f"elapsed: {elapsed:.1f}s")

    print("\nBy gold pos_tag (real-root words):")
    for pos, (c, n) in sorted(by_pos.items(), key=lambda kv: -kv[1][1]):
        print(f"  {pos:>6}: {c}/{n} = {c / n:.3f}")

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ERROR_FIELDS)
        w.writeheader()
        w.writerows(errors)
    print(f"\nErrors written to {args.out}: {len(errors)} rows")


if __name__ == "__main__":
    main()
