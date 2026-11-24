from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.path import Lesson, LessonPrerequisite, LessonWord
from app.models.quran import Surah, Verse, Word
from app.services.frequency_service import PLACEHOLDER_ROOT, FrequencyService

logger = get_logger("services.lesson_seed")

LEVEL_ORDER = ("beginner", "intermediate", "advanced")
LEVEL_BANDS: dict[str, tuple[int, int]] = {
    "beginner": (1, 40),
    "intermediate": (41, 120),
    "advanced": (121, 300),
}
MIN_ROOT_OCCURRENCES = 3
MAX_FORMS = 4
EST_MINUTES = 10


@dataclass(frozen=True)
class LessonSpec:
    root: str
    level: str
    sequence: int
    rank: int


def rank_roots(
    rows: list[tuple[str, int]],
    min_occurrences: int = MIN_ROOT_OCCURRENCES,
) -> list[tuple[str, int]]:
    cleaned = [
        (root, count)
        for root, count in rows
        if root and root != PLACEHOLDER_ROOT and count >= min_occurrences
    ]
    return sorted(cleaned, key=lambda item: (-item[1], item[0]))


def lesson_specs(
    ranked: list[tuple[str, int]],
    bands: dict[str, tuple[int, int]] = LEVEL_BANDS,
) -> list[LessonSpec]:
    specs: list[LessonSpec] = []
    for level in LEVEL_ORDER:
        start, end = bands[level]
        last = min(end, len(ranked))
        for rank in range(start, last + 1):
            root, _ = ranked[rank - 1]
            specs.append(
                LessonSpec(
                    root=root,
                    level=level,
                    sequence=rank - start + 1,
                    rank=rank,
                )
            )
    return specs


def _forms_for(rows: list[Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row.lemma or "", row.text_imlaei or row.text_uthmani)
        entry = grouped.get(key)
        if entry is None:
            entry = {
                "word_id": row.id,
                "count": 0,
                "text_uthmani": row.text_uthmani,
                "text_imlaei": row.text_imlaei,
                "lemma": row.lemma,
                "pos_tag": row.pos_tag,
                "gloss": row.translation_en,
            }
            grouped[key] = entry
        entry["count"] += 1
        if entry["gloss"] is None and row.translation_en:
            entry["gloss"] = row.translation_en
        if row.id < entry["word_id"]:
            entry["word_id"] = row.id

    ordered = sorted(
        grouped.values(),
        key=lambda item: (
            -item["count"],
            item["lemma"] or "",
            item["text_uthmani"] or "",
        ),
    )
    return ordered[:MAX_FORMS]


def _pick_example(
    root: str,
    candidates: dict[str, set[int]],
    verse_counts: dict[int, int],
    verse_by_id: dict[int, Any],
) -> int | None:
    verse_ids = [vid for vid in candidates.get(root, set()) if vid in verse_by_id]
    if not verse_ids:
        return None
    return min(
        verse_ids,
        key=lambda vid: (
            0 if 4 <= verse_counts.get(vid, 0) <= 12 else 1,
            len(verse_by_id[vid].text_uthmani or ""),
            verse_by_id[vid].number,
            verse_by_id[vid].ayah_number,
        ),
    )


async def seed_lessons(
    db: AsyncSession,
    *,
    bands: dict[str, tuple[int, int]] = LEVEL_BANDS,
    min_occurrences: int = MIN_ROOT_OCCURRENCES,
) -> dict[str, int]:
    ranked = rank_roots(
        await FrequencyService(db).root_frequencies(),
        min_occurrences,
    )
    specs = lesson_specs(ranked, bands)
    if not specs:
        logger.info("No roots qualified for lesson seeding")
        return {"lessons": 0, "words": 0, "roots": 0}

    rank_by_root = dict(ranked)
    roots = [spec.root for spec in specs]

    word_rows = (
        await db.execute(
            select(
                Word.id,
                Word.verse_id,
                Word.root,
                Word.lemma,
                Word.text_uthmani,
                Word.text_imlaei,
                Word.pos_tag,
                Word.translation_en,
            ).where(Word.root.in_(roots))
        )
    ).all()

    verse_counts = dict(
        (
            await db.execute(
                select(Word.verse_id, func.count()).group_by(Word.verse_id)
            )
        ).all()
    )

    words_by_root: dict[str, list[Any]] = defaultdict(list)
    candidates: dict[str, set[int]] = defaultdict(set)
    for row in word_rows:
        words_by_root[row.root].append(row)
        candidates[row.root].add(row.verse_id)

    candidate_ids = set().union(*candidates.values()) if candidates else set()
    verse_rows = (
        await db.execute(
            select(
                Verse.id,
                Verse.ayah_number,
                Verse.text_uthmani,
                Verse.translation_en,
                Surah.number,
            )
            .join(Surah, Surah.id == Verse.surah_id)
            .where(Verse.id.in_(candidate_ids))
        )
    ).all()
    verse_by_id = {row.id: row for row in verse_rows}

    example_by_root = {
        spec.root: _pick_example(spec.root, candidates, verse_counts, verse_by_id)
        for spec in specs
    }
    example_ids = {vid for vid in example_by_root.values() if vid is not None}
    example_word_rows = (
        await db.execute(
            select(
                Word.id,
                Word.verse_id,
                Word.position,
            )
            .where(Word.verse_id.in_(example_ids))
            .order_by(Word.verse_id, Word.position)
        )
    ).all()
    example_words: dict[int, list[Any]] = defaultdict(list)
    for example_row in example_word_rows:
        example_words[example_row.verse_id].append(example_row)

    existing = (
        await db.execute(select(Lesson).where(Lesson.module == "vocabulary"))
    ).scalars().all()
    existing_by_key = {(lesson.level, lesson.sequence): lesson for lesson in existing}

    forms_by_root: dict[str, list[dict[str, Any]]] = {}
    lessons: list[Lesson] = []
    for spec in specs:
        forms = _forms_for(words_by_root.get(spec.root, []))
        forms_by_root[spec.root] = forms
        example_id = example_by_root[spec.root]
        example = None
        if example_id is not None:
            verse = verse_by_id[example_id]
            example = {
                "surah_number": verse.number,
                "ayah_number": verse.ayah_number,
                "text_uthmani": verse.text_uthmani,
                "translation_en": verse.translation_en,
            }

        content: dict[str, Any] = {
            "root": spec.root,
            "rank": spec.rank,
            "occurrences": rank_by_root[spec.root],
            "forms": forms,
            "example": example,
        }

        lesson = existing_by_key.get((spec.level, spec.sequence))
        if lesson is None:
            lesson = Lesson(
                title=f"Root {spec.root}",
                module="vocabulary",
                level=spec.level,
                sequence=spec.sequence,
                root=spec.root,
                content_json=content,
                est_minutes=EST_MINUTES,
            )
            db.add(lesson)
        else:
            lesson.title = f"Root {spec.root}"
            lesson.root = spec.root
            lesson.content_json = content
            lesson.est_minutes = EST_MINUTES
        lessons.append(lesson)

    await db.flush()
    lesson_ids = [lesson.id for lesson in lessons]

    await db.execute(delete(LessonWord).where(LessonWord.lesson_id.in_(lesson_ids)))
    lesson_words: list[LessonWord] = []
    seen: set[tuple[int, int, str]] = set()
    for spec, lesson in zip(specs, lessons, strict=True):
        for index, form in enumerate(forms_by_root[spec.root]):
            key = (lesson.id, form["word_id"], "form")
            if key in seen:
                continue
            seen.add(key)
            lesson_words.append(
                LessonWord(
                    lesson_id=lesson.id,
                    word_id=form["word_id"],
                    kind="form",
                    sort_order=index,
                )
            )
        example_id = example_by_root[spec.root]
        if example_id is None:
            continue
        for row in example_words.get(example_id, []):
            key = (lesson.id, row.id, "example")
            if key in seen:
                continue
            seen.add(key)
            lesson_words.append(
                LessonWord(
                    lesson_id=lesson.id,
                    word_id=row.id,
                    kind="example",
                    sort_order=row.position,
                )
            )
    db.add_all(lesson_words)

    await db.execute(
        delete(LessonPrerequisite).where(
            LessonPrerequisite.lesson_id.in_(lesson_ids)
        )
    )
    db.add_all(
        [
            LessonPrerequisite(
                lesson_id=current.id,
                requires_lesson_id=previous.id,
            )
            for previous, current in zip(lessons, lessons[1:], strict=False)
        ]
    )

    await db.flush()
    logger.info(
        "Seeded %d lessons, %d words, from %d ranked roots",
        len(lessons),
        len(lesson_words),
        len(ranked),
    )
    return {
        "lessons": len(lessons),
        "words": len(lesson_words),
        "roots": len(ranked),
    }
