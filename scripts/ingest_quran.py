#!/usr/bin/env python3
"""
Jawhar — Quran Corpus Ingestion Script (local files only).

Reads a local corpus directory (default ``data/corpus/``) and upserts into
``surahs``, ``verses``, ``words`` and ``nahw_annotations``.

Expected files (all local, no network access):

* ``quran-uthmani.txt`` / ``quran-imlaei.txt`` — Tanzil-style simple text,
  one verse per line: ``surah|ayah|text``. Text is stored byte-for-byte as in
  the source; never normalized or edited.
* ``translation-en.txt`` / ``translation-ur.txt`` — same ``surah|ayah|text``
  line format.
* ``morphology.tsv`` — tab-separated, header row:
  ``surah  ayah  word  segment  form  root  lemma  pos  pattern  tense  voice  gender  number  person``
  ``word`` is the 1-based orthographic word position within the ayah (our
  one ``words`` row = one orthographic word). ``segment`` is the 0-based
  clitic/stem segment index inside that word. All segments of one
  (surah, ayah, word) group are merged into a single ``words`` row:
  ``text_uthmani`` = concatenation of segment forms in segment order,
  top-level morphology columns = first non-empty value across segments,
  per-segment detail preserved verbatim in ``features_json["segments"]``.
* ``nahw.tsv`` — tab-separated, header row:
  ``surah  ayah  token_index  role  dep_type  head_index  irab``
  ``token_index`` equals the 1-based word position; when the matching
  ``words`` row exists its id is stored in ``nahw_annotations.word_id``.

Properties:

* Idempotent: rows are keyed by natural keys (surah number; surah+ayah;
  verse+position; verse+token_index). Existing rows are left untouched,
  so re-running never duplicates.
* Commits in batches of 1,000 inserted rows.
* ``--dry-run`` parses and reports what would be inserted without writing.
* ``--limit-surahs N`` only ingests rows from the first N surahs.
* Progress is logged every 1,000 rows; a final validation report prints
  counts of surahs, verses, words and nahw_annotations.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed_data import SURAHS_DATA  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.models.quran import NahwAnnotation, Surah, Verse, Word  # noqa: E402

logger = get_logger("scripts.ingest_quran")

BATCH_SIZE = 1000
DEFAULT_CORPUS_DIR = ROOT_DIR / "data" / "corpus"


# ---------------------------------------------------------------------------
# Parsing (pure functions — no database)
# ---------------------------------------------------------------------------

def parse_tanzil_text(path: Path) -> dict[tuple[int, int], str]:
    """Parse a Tanzil-style file into {(surah, ayah): text}.

    Supports two formats:
    * pipe format: one verse per line as ``surah|ayah|text`` (translations).
    * plain format: comment lines start with ``#``, followed by one verse per
      line in surah/ayah order (Tanzil "Text" downloads). Positions are mapped
      using ``SURAHS_DATA`` verse counts.
    """
    out: dict[tuple[int, int], str] = {}
    if not path.exists():
        logger.warning("Missing file, skipping: %s", path)
        return out
    lines = [
        raw.strip()
        for raw in path.read_text(encoding="utf-8").splitlines()
        if raw.strip() and not raw.lstrip().startswith("#")
    ]
    if not lines:
        return out
    if any("|" in line for line in lines):
        for line_no, line in enumerate(lines, start=1):
            parts = line.split("|", 2)
            if len(parts) != 3:
                raise ValueError(f"{path}:{line_no}: expected 'surah|ayah|text', got {line!r}")
            out[(int(parts[0]), int(parts[1]))] = parts[2]  # stored exactly as in source
        return out
    idx = 0
    for meta in SURAHS_DATA:
        for ayah in range(1, meta["verse_count"] + 1):
            if idx >= len(lines):
                raise ValueError(f"{path}: ran out of verse lines at surah {meta['number']} ayah {ayah}")
            out[(meta["number"], ayah)] = lines[idx]  # stored exactly as in source
            idx += 1
    if idx != len(lines):
        raise ValueError(f"{path}: {len(lines)} lines but expected {idx} verses")
    return out


def parse_morphology(path: Path) -> dict[tuple[int, int, int], list[dict[str, str]]]:
    """Parse morphology.tsv into {(surah, ayah, word): [segment rows]}."""
    groups: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    if not path.exists():
        logger.warning("Missing file, skipping: %s", path)
        return groups
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    if not lines:
        return groups
    header = [h.strip() for h in lines[0].split("\t")]
    if header[:3] == ["LOCATION", "FORM", "TAG"]:
        return _parse_qac_morphology(lines[1:])
    required = {"surah", "ayah", "word", "segment", "form"}
    missing = required - set(header)
    if missing:
        raise ValueError(f"{path}: header missing columns {sorted(missing)}")
    for raw in lines[1:]:
        if not raw.strip() or raw.startswith("#"):
            continue
        cols = dict(zip(header, raw.split("\t"), strict=False))
        key = (int(cols["surah"]), int(cols["ayah"]), int(cols["word"]))
        groups[key].append({k: v.strip() for k, v in cols.items()})
    for segs in groups.values():
        segs.sort(key=lambda s: int(s["segment"]))
    return groups


def _parse_qac_morphology(data_lines: list[str]) -> dict[tuple[int, int, int], list[dict[str, str]]]:
    """Parse the official quranic-corpus-morphology-0.4.txt format:
    ``LOCATION(surah:ayah:word:segment)  FORM  TAG  FEATURES`` per segment."""
    groups: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    for raw in data_lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4:
            continue
        location, form, tag, features = parts[0], parts[1], parts[2], "\t".join(parts[3:])
        s, a, w, seg = location.strip("()").split(":")
        seg_dict = {"surah": s, "ayah": a, "word": w, "segment": seg, "form": form, "tag": tag, "features": features}
        seg_dict.update(_extract_qac_features(features, tag))
        groups[(int(s), int(a), int(w))].append(seg_dict)
    for segs in groups.values():
        segs.sort(key=lambda s: int(s["segment"]))
    return groups


def _extract_qac_features(features: str, tag: str) -> dict[str, str]:
    out: dict[str, str] = {"pos": tag}
    import re

    for token in features.split("|"):
        if token.startswith("POS:"):
            out["pos"] = token[4:]
        elif token.startswith("LEM:"):
            out["lemma"] = token[4:]
        elif token.startswith("ROOT:"):
            out["root"] = token[5:]
        elif m := re.fullmatch(r"\(([IVX]+)\)", token):
            out["pattern"] = m.group(1)
        elif token == "PERF":
            out["tense"] = "past"
        elif token == "IMPF":
            out["tense"] = "present"
        elif token == "IMPV":
            out["tense"] = "imperative"
        elif token == "PASS":
            out["voice"] = "passive"
        elif token == "ACT":
            out["voice"] = "active"
        elif token in ("M", "F"):
            out["gender"] = token
        elif token in ("S", "D", "P"):
            out["number"] = token
        elif m := re.fullmatch(r"([123])([MF]?)([SDP]?)", token):
            out["person"] = m.group(1)
            if m.group(2):
                out["gender"] = m.group(2)
            if m.group(3):
                out["number"] = m.group(3)
    return out


def parse_nahw(path: Path) -> list[dict[str, str]]:
    """Parse nahw.tsv into a list of annotation row dicts."""
    rows: list[dict[str, str]] = []
    if not path.exists():
        logger.warning("Missing file, skipping: %s", path)
        return rows
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return rows
    header = [h.strip() for h in lines[0].split("\t")]
    required = {"surah", "ayah", "token_index"}
    missing = required - set(header)
    if missing:
        raise ValueError(f"{path}: header missing columns {sorted(missing)}")
    for raw in lines[1:]:
        if not raw.strip():
            continue
        rows.append(dict(zip(header, raw.split("\t"), strict=False)))
    return rows


def parse_eqtb(path: Path) -> tuple[dict[tuple[int, int, int], dict[str, object]], list[dict[str, str]]]:
    """Parse the Extended Quranic Treebank ``Quranic.csv`` (UTF-16 TSV, 43 columns).

    Returns (words, nahw_rows):
    * words: {(surah, ayah, word): {...}} — one entry per orthographic word;
      ``text`` is the concatenation of the word's segment Uthmani tokens.
    * nahw_rows: one row per word, shaped like parse_nahw output.
    """
    import csv

    words: dict[tuple[int, int, int], dict[str, object]] = {}
    nahw_rows: list[dict[str, str]] = []
    if not path.exists():
        logger.warning("Missing file, skipping: %s", path)
        return words, nahw_rows

    grouped: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-16", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if row["word_id"] == "0":  # sentence-level placeholder rows
                continue
            key = (int(row["chapter_id"]), int(row["verse_id"]), int(row["word_id"]))
            grouped[key].append(row)

    for (s, a, w), rows in grouped.items():
        rows.sort(key=lambda r: int(r["tok_id"]))
        stem = next((r for r in rows if r["segment"] == "STEM"), rows[0])
        text = "".join(r["uthmani_token"] for r in rows if r["uthmani_token"] not in ("", "(*)"))
        text_imlaei = "".join(r["imlaai_token"] for r in rows if r["imlaai_token"] not in ("", "(*)"))
        words[(s, a, w)] = {
            "text": text,
            "text_imlaei": text_imlaei,
            "lemma": stem["lemma_ar"] or None,
            "root": stem["root_ar"] or None,
            "pos": stem["pos"] or None,
            "pattern": stem["verb_form"] or None,
            "tense": stem["verb_aspect"] or None,
            "voice": stem["verb_voice"] or None,
            "gender": stem["gender"] or None,
            "number": stem["number"] or None,
            "person": stem["person"] or None,
            "translation_en": stem["trans"] if stem["trans"] != "_" else None,
            "transliteration": stem["phonetic"] if stem["phonetic"] != "_" else None,
            "segments": [
                {"segment": r["segment"], "form": r["uthmani_token"], "pos": r["pos"], "features": r["features"]}
                for r in rows
            ],
        }
        nahw_rows.append(
            {
                "surah": str(s),
                "ayah": str(a),
                "token_index": str(w),
                "role": stem["rel_label_ar"] or stem["rel_label"],
                "dep_type": stem["rel_label"],
                "head_index": "",
                "irab": stem["nominal_case"] if stem["nominal_case"] != "_" else "",
            }
        )
    return words, nahw_rows


def _first_non_empty(segments: Iterable[dict[str, str]], key: str) -> str | None:
    for seg in segments:
        value = seg.get(key, "").strip()
        if value:
            return value
    return None


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

async def _existing_keys(session: AsyncSession) -> tuple[set[int], set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]]]:
    surah_nums = {n for (n,) in (await session.execute(select(Surah.number))).all()}
    verse_keys = {
        (sid, ayah)
        for sid, ayah in (await session.execute(select(Verse.surah_id, Verse.ayah_number))).all()
    }
    word_keys = {
        (vid, pos)
        for vid, pos in (await session.execute(select(Word.verse_id, Word.position))).all()
    }
    nahw_keys = {
        (vid, idx)
        for vid, idx in (
            await session.execute(select(NahwAnnotation.verse_id, NahwAnnotation.token_index))
        ).all()
    }
    return surah_nums, verse_keys, word_keys, nahw_keys


async def ingest(
    session: AsyncSession,
    corpus_dir: Path,
    *,
    limit_surahs: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Ingest corpus files. Returns per-section counts of inserted rows."""
    uthmani = parse_tanzil_text(corpus_dir / "quran-uthmani.txt")
    imlaei = parse_tanzil_text(corpus_dir / "quran-imlaei.txt")
    tr_en = parse_tanzil_text(corpus_dir / "translation-en.txt")
    tr_ur = parse_tanzil_text(corpus_dir / "translation-ur.txt")
    morphology_path = corpus_dir / "morphology.tsv"
    if not morphology_path.exists():
        morphology_path = corpus_dir / "quranic-corpus-morphology-0.4.txt"
    morphology = parse_morphology(morphology_path)

    eqtb_words: dict[tuple[int, int, int], dict[str, object]] = {}
    eqtb_nahw: list[dict[str, str]] = []
    for candidate in (corpus_dir / "Quranic.csv", corpus_dir / "eqtb.csv", corpus_dir / "Quranic.tsv"):
        if candidate.exists():
            eqtb_words, eqtb_nahw = parse_eqtb(candidate)
            break

    nahw_path = corpus_dir / "nahw.tsv"
    nahw_rows = parse_nahw(nahw_path) if nahw_path.exists() else eqtb_nahw

    if limit_surahs is not None:
        uthmani = {k: v for k, v in uthmani.items() if k[0] <= limit_surahs}
        imlaei = {k: v for k, v in imlaei.items() if k[0] <= limit_surahs}
        tr_en = {k: v for k, v in tr_en.items() if k[0] <= limit_surahs}
        tr_ur = {k: v for k, v in tr_ur.items() if k[0] <= limit_surahs}
        morphology = {k: v for k, v in morphology.items() if k[0] <= limit_surahs}
        eqtb_words = {k: v for k, v in eqtb_words.items() if k[0] <= limit_surahs}
        nahw_rows = [r for r in nahw_rows if int(r["surah"]) <= limit_surahs]

    surah_nums, verse_keys, word_keys, nahw_keys = await _existing_keys(session)
    verse_pk: dict[tuple[int, int], int] = {}
    for vid, sid, ayah in (
        await session.execute(select(Verse.id, Verse.surah_id, Verse.ayah_number))
    ).all():
        verse_pk[(sid, ayah)] = vid
    word_pk: dict[tuple[int, int], int] = {}
    for wid, vid, pos in (
        await session.execute(select(Word.id, Word.verse_id, Word.position))
    ).all():
        word_pk[(vid, pos)] = wid
    surah_pk: dict[int, int] = {}
    for sid, num in (await session.execute(select(Surah.id, Surah.number))).all():
        surah_pk[num] = sid

    inserted = {"surahs": 0, "verses": 0, "words": 0, "nahw_annotations": 0}
    pending = 0

    async def flush_if_batch() -> None:
        nonlocal pending
        if pending >= BATCH_SIZE:
            if not dry_run:
                await session.commit()
            logger.info("Progress: surahs=%d verses=%d words=%d nahw=%d", *inserted.values())
            pending = 0

    # 1. Surahs (metadata from verified seed, only those present in the files)
    referenced_surahs = {s for s, _ in uthmani}
    for meta in SURAHS_DATA:
        num = meta["number"]
        if num not in referenced_surahs:
            continue
        if num in surah_nums:
            continue
        surah = Surah(**meta)
        session.add(surah)
        inserted["surahs"] += 1
        pending += 1
        if not dry_run:
            await session.flush()
            surah_pk[num] = surah.id
        else:
            surah_pk[num] = -num  # placeholder so later stages can link
        await flush_if_batch()
    if not dry_run:
        await session.flush()
        for sid, num in (await session.execute(select(Surah.id, Surah.number))).all():
            surah_pk[num] = sid

    # 2. Verses
    for (surah_no, ayah_no), text in uthmani.items():
        surah_id = surah_pk.get(surah_no)
        if surah_id is None:
            if dry_run:
                surah_id = -surah_no  # placeholder; not persisted
            else:
                logger.warning("Surah %d missing, skipping ayah %d", surah_no, ayah_no)
                continue
        if (surah_id, ayah_no) in verse_keys:
            continue
        verse = Verse(
            surah_id=surah_id,
            ayah_number=ayah_no,
            text_uthmani=text,
            text_imlaei=imlaei.get((surah_no, ayah_no)),
            translation_en=tr_en.get((surah_no, ayah_no)),
            translation_ur=tr_ur.get((surah_no, ayah_no)),
        )
        session.add(verse)
        inserted["verses"] += 1
        pending += 1
        if not dry_run:
            await session.flush()
            verse_pk[(surah_id, ayah_no)] = verse.id
        else:
            verse_pk[(surah_id, ayah_no)] = -(len(verse_pk) + surah_no * 1000 + ayah_no)  # fake id
        verse_keys.add((surah_id, ayah_no))
        await flush_if_batch()

    # 3. Words (morphology groups + EQTB -> one row per orthographic word)
    word_keys_all = set(morphology.keys()) | set(eqtb_words.keys())
    for s_no, a_no, w_pos in sorted(word_keys_all):
        surah_id = surah_pk.get(s_no)
        verse_id: int | None = None
        if surah_id is not None:
            verse_id = verse_pk.get((surah_id, a_no))
        if verse_id is None:
            logger.warning("Verse %d:%d not found, skipping word %d", s_no, a_no, w_pos)
            continue
        if (verse_id, w_pos) in word_keys:
            continue
        segments = morphology.get((s_no, a_no, w_pos))
        eq = eqtb_words.get((s_no, a_no, w_pos))
        if eq is not None:
            text = str(eq["text"])
            text_imlaei = eq["text_imlaei"] if isinstance(eq["text_imlaei"], str) else None
            root = eq["root"] if isinstance(eq["root"], str) else None
            lemma = eq["lemma"] if isinstance(eq["lemma"], str) else None
            pos = eq["pos"] if isinstance(eq["pos"], str) else None
            pattern = eq["pattern"] if isinstance(eq["pattern"], str) else None
            tense = eq["tense"] if isinstance(eq["tense"], str) else None
            voice = eq["voice"] if isinstance(eq["voice"], str) else None
            gender = eq["gender"] if isinstance(eq["gender"], str) else None
            number = eq["number"] if isinstance(eq["number"], str) else None
            person = eq["person"] if isinstance(eq["person"], str) else None
            translation_en = eq["translation_en"] if isinstance(eq["translation_en"], str) else None
            transliteration = eq["transliteration"] if isinstance(eq["transliteration"], str) else None
            segs = segments if segments is not None else eq["segments"]  # type: ignore[assignment]
        else:
            assert segments is not None
            text = "".join(seg["form"] for seg in segments)
            text_imlaei = None
            translation_en = None
            transliteration = None
            root = _first_non_empty(segments, "root")
            lemma = _first_non_empty(segments, "lemma")
            pos = _first_non_empty(segments, "pos")
            pattern = _first_non_empty(segments, "pattern")
            tense = _first_non_empty(segments, "tense")
            voice = _first_non_empty(segments, "voice")
            gender = _first_non_empty(segments, "gender")
            number = _first_non_empty(segments, "number")
            person = _first_non_empty(segments, "person")
            segs = segments
        word = Word(
            verse_id=verse_id,
            position=w_pos,
            text_uthmani=text,
            text_imlaei=text_imlaei,
            root=root,
            lemma=lemma,
            pos_tag=pos,
            pattern=pattern,
            tense=tense,
            voice=voice,
            gender=gender,
            number=number,
            person=person,
            translation_en=translation_en,
            transliteration=transliteration,
            features_json={"segments": segs},
        )
        session.add(word)
        inserted["words"] += 1
        pending += 1
        if not dry_run:
            await session.flush()
            word_pk[(verse_id, w_pos)] = word.id
        word_keys.add((verse_id, w_pos))
        await flush_if_batch()

    # 4. Nahw annotations
    for row in nahw_rows:
        surah_id = surah_pk.get(int(row["surah"]))
        if surah_id is None:
            continue
        verse_id = verse_pk.get((surah_id, int(row["ayah"])))
        if verse_id is None:
            logger.warning("Verse %s:%s not found, skipping nahw token %s", row["surah"], row["ayah"], row["token_index"])
            continue
        token_index = int(row["token_index"])
        if (verse_id, token_index) in nahw_keys:
            continue
        head = row.get("head_index", "").strip()
        annotation = NahwAnnotation(
            verse_id=verse_id,
            word_id=word_pk.get((verse_id, token_index)),
            token_index=token_index,
            role=row.get("role", "").strip() or None,
            dep_type=row.get("dep_type", "").strip() or None,
            head_index=int(head) if head.lstrip("-").isdigit() else None,
            irab=row.get("irab", "").strip() or None,
        )
        session.add(annotation)
        inserted["nahw_annotations"] += 1
        pending += 1
        nahw_keys.add((verse_id, token_index))
        await flush_if_batch()

    if dry_run:
        await session.rollback()
    else:
        await session.commit()

    logger.info(
        "Ingestion finished (%s): surahs=%d verses=%d words=%d nahw_annotations=%d",
        "dry-run" if dry_run else "committed",
        inserted["surahs"],
        inserted["verses"],
        inserted["words"],
        inserted["nahw_annotations"],
    )
    return inserted


async def report_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, model in (("surahs", Surah), ("verses", Verse), ("words", Word), ("nahw_annotations", NahwAnnotation)):
        counts[name] = (await session.execute(select(func.count()).select_from(model))).scalar_one()
    return counts


async def run(args: argparse.Namespace) -> None:
    corpus_dir = Path(args.corpus_dir)
    if not corpus_dir.is_dir():
        raise SystemExit(f"Corpus directory not found: {corpus_dir}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        inserted = await ingest(
            session,
            corpus_dir,
            limit_surahs=args.limit_surahs,
            dry_run=args.dry_run,
        )
        counts = await report_counts(session)

    logger.info(
        "Validation report — inserted this run: %s | totals in DB: surahs=%d verses=%d words=%d nahw_annotations=%d",
        inserted,
        counts["surahs"],
        counts["verses"],
        counts["words"],
        counts["nahw_annotations"],
    )
    if not args.dry_run:
        expected = {"verses": 6236, "words": 77430}
        for key, target in expected.items():
            if counts[key] < target:
                logger.warning("Count check: %s=%d (target %d) — corpus may be incomplete.", key, counts[key], target)

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local Quran corpus files into Jawhar DB.")
    parser.add_argument("--corpus-dir", default=str(DEFAULT_CORPUS_DIR), help="Directory with corpus files")
    parser.add_argument("--limit-surahs", type=int, default=None, help="Only ingest the first N surahs")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing to the DB")
    args = parser.parse_args()
    setup_logging(level="INFO")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
