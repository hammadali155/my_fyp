from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import (
    AssessmentAttempt,
    Lesson,
    LessonPrerequisite,
    LessonWord,
    UserLesson,
)
from app.models.user import User


async def _make_user(db: AsyncSession, email: str = "path@example.com") -> User:
    user = User(email=email, name="Path Learner", password_hash="x")
    db.add(user)
    await db.flush()
    return user


async def _make_lesson(db: AsyncSession, **overrides: object) -> Lesson:
    data: dict[str, object] = {
        "title": "Root رحم",
        "module": "vocabulary",
        "level": "beginner",
        "sequence": 1,
        "content_json": {"root": "رحم"},
        "est_minutes": 10,
        "root": "رحم",
    }
    data.update(overrides)
    lesson = Lesson(**data)
    db.add(lesson)
    await db.flush()
    return lesson


async def test_lesson_round_trip(db_session: AsyncSession) -> None:
    lesson = await _make_lesson(db_session)
    await db_session.commit()

    row = (
        await db_session.execute(select(Lesson).where(Lesson.id == lesson.id))
    ).scalar_one()
    assert row.title == "Root رحم"
    assert row.root == "رحم"
    assert row.content_json == {"root": "رحم"}
    assert row.est_minutes == 10


async def test_duplicate_sequence_is_rejected(db_session: AsyncSession) -> None:
    await _make_lesson(db_session)
    with pytest.raises(IntegrityError):
        await _make_lesson(db_session, title="Other")
    await db_session.rollback()


async def test_self_prerequisite_is_rejected(db_session: AsyncSession) -> None:
    lesson = await _make_lesson(db_session)
    db_session.add(
        LessonPrerequisite(lesson_id=lesson.id, requires_lesson_id=lesson.id)
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


async def test_duplicate_user_lesson_is_rejected(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    lesson = await _make_lesson(db_session)
    db_session.add(UserLesson(user_id=user.id, lesson_id=lesson.id))
    await db_session.flush()

    db_session.add(UserLesson(user_id=user.id, lesson_id=lesson.id))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


async def test_deleting_a_lesson_cascades(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await db_session.execute(text("PRAGMA foreign_keys=ON"))
    user = await _make_user(db_session)
    first = await _make_lesson(db_session)
    second = await _make_lesson(db_session, sequence=2, root="علم")
    db_session.add(
        LessonPrerequisite(lesson_id=second.id, requires_lesson_id=first.id)
    )
    db_session.add(LessonWord(lesson_id=first.id, word_id=1, kind="form"))
    db_session.add(UserLesson(user_id=user.id, lesson_id=first.id))
    attempt = AssessmentAttempt(
        user_id=user.id,
        score=12,
        placed_level="intermediate",
        answers_json=[],
    )
    db_session.add(attempt)
    await db_session.commit()

    await db_session.execute(text("DELETE FROM lessons WHERE id = :id"), {"id": first.id})
    await db_session.commit()

    assert (
        await db_session.execute(
            select(LessonPrerequisite).where(
                LessonPrerequisite.requires_lesson_id == first.id
            )
        )
    ).scalars().all() == []
    assert (
        await db_session.execute(
            select(LessonWord).where(LessonWord.lesson_id == first.id)
        )
    ).scalars().all() == []
    assert (
        await db_session.execute(
            select(UserLesson).where(UserLesson.lesson_id == first.id)
        )
    ).scalars().all() == []
    assert (
        await db_session.execute(select(AssessmentAttempt))
    ).scalars().all() != []
