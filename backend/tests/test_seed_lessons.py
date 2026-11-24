from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, LessonPrerequisite, LessonWord
from app.services.lesson_seed import seed_lessons

TINY_BANDS = {
    "beginner": (1, 2),
    "intermediate": (3, 3),
    "advanced": (4, 4),
}


async def test_seed_creates_lessons_from_corpus_rows(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    result = await seed_lessons(
        db_session, bands=TINY_BANDS, min_occurrences=1
    )
    await db_session.commit()

    lessons = (
        await db_session.execute(select(Lesson).order_by(Lesson.id))
    ).scalars().all()
    assert result["lessons"] == 4
    assert [lesson.root for lesson in lessons] == ["رحم", "اله", "حمد", "سمو"]
    assert [lesson.level for lesson in lessons] == [
        "beginner",
        "beginner",
        "intermediate",
        "advanced",
    ]
    assert [lesson.sequence for lesson in lessons] == [1, 2, 1, 1]

    first = lessons[0]
    assert first.title == "Root رحم"
    assert first.content_json["occurrences"] == 2
    assert first.content_json["forms"]
    assert first.content_json["example"]["surah_number"] == 1
    assert first.content_json["example"]["ayah_number"] == 1
    assert first.content_json["example"]["translation_en"]


async def test_seed_writes_form_and_example_words(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await seed_lessons(db_session, bands=TINY_BANDS, min_occurrences=1)
    await db_session.commit()

    first = (
        await db_session.execute(select(Lesson).where(Lesson.root == "رحم"))
    ).scalar_one()
    rows = (
        await db_session.execute(
            select(LessonWord).where(LessonWord.lesson_id == first.id)
        )
    ).scalars().all()
    kinds = {row.kind for row in rows}
    assert kinds == {"form", "example"}
    assert {row.word_id for row in rows} <= {1, 2, 3, 4, 5}


async def test_seed_chains_prerequisites_in_band_order(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await seed_lessons(db_session, bands=TINY_BANDS, min_occurrences=1)
    await db_session.commit()

    lessons = (
        await db_session.execute(select(Lesson).order_by(Lesson.id))
    ).scalars().all()
    prereqs = (
        await db_session.execute(select(LessonPrerequisite))
    ).scalars().all()
    assert len(prereqs) == len(lessons) - 1
    pairs = {(p.lesson_id, p.requires_lesson_id) for p in prereqs}
    for previous, current in zip(lessons, lessons[1:], strict=False):
        assert (current.id, previous.id) in pairs


async def test_seed_is_idempotent(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await seed_lessons(db_session, bands=TINY_BANDS, min_occurrences=1)
    await db_session.commit()
    await seed_lessons(db_session, bands=TINY_BANDS, min_occurrences=1)
    await db_session.commit()

    lesson_count = (
        await db_session.execute(select(func.count()).select_from(Lesson))
    ).scalar_one()
    prereq_count = (
        await db_session.execute(select(func.count()).select_from(LessonPrerequisite))
    ).scalar_one()
    word_count = (
        await db_session.execute(select(func.count()).select_from(LessonWord))
    ).scalar_one()
    assert lesson_count == 4
    assert prereq_count == 3
    assert word_count > 0

    first = (
        await db_session.execute(select(Lesson).where(Lesson.root == "رحم"))
    ).scalar_one()
    rows = (
        await db_session.execute(
            select(func.count()).select_from(LessonWord).where(
                LessonWord.lesson_id == first.id
            )
        )
    ).scalar_one()
    assert rows == len({(r.kind, r.word_id) for r in (
        await db_session.execute(
            select(LessonWord).where(LessonWord.lesson_id == first.id)
        )
    ).scalars().all()})
