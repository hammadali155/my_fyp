from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, LessonPrerequisite, QuizAttempt, UserLesson
from app.models.user import User


async def _seed(db: AsyncSession) -> dict[str, int]:
    user = (
        await db.execute(select(User).where(User.email == "talib@example.com"))
    ).scalar_one()
    specs = [
        ("vocabulary", 1, "رحم"),
        ("vocabulary", 2, "علم"),
        ("vocabulary", 3, "قول"),
        ("sarf", 4, "كتب"),
    ]
    lessons: list[Lesson] = []
    for module, sequence, root in specs:
        lesson = Lesson(
            title=f"Root {root}",
            module=module,
            level="beginner",
            sequence=sequence,
            root=root,
            content_json={"root": root, "forms": [], "example": None},
            est_minutes=10,
        )
        db.add(lesson)
        lessons.append(lesson)
    await db.flush()

    for previous, current in zip(lessons, lessons[1:], strict=False):
        db.add(
            LessonPrerequisite(
                lesson_id=current.id, requires_lesson_id=previous.id
            )
        )
    db.add(
        UserLesson(
            user_id=user.id,
            lesson_id=lessons[0].id,
            status="completed",
            score=5,
            completed_at=datetime.now(UTC),
        )
    )
    db.add(
        UserLesson(
            user_id=user.id,
            lesson_id=lessons[1].id,
            status="in_progress",
        )
    )

    now = datetime.now(UTC)
    db.add_all(
        [
            QuizAttempt(
                user_id=user.id,
                lesson_id=lessons[0].id,
                kind="lesson",
                seed=1,
                questions_json=[],
                answer_key_json=[],
                status="submitted",
                score=4,
                total=5,
                completed_at=now - timedelta(hours=1),
            ),
            QuizAttempt(
                user_id=user.id,
                lesson_id=lessons[1].id,
                kind="lesson",
                seed=2,
                questions_json=[],
                answer_key_json=[],
                status="submitted",
                score=2,
                total=5,
                completed_at=now - timedelta(hours=3),
            ),
            QuizAttempt(
                user_id=user.id,
                lesson_id=lessons[2].id,
                kind="lesson",
                seed=3,
                questions_json=[],
                answer_key_json=[],
                status="open",
                total=5,
            ),
        ]
    )
    user.xp = 55
    user.streak_days = 4
    user.last_activity_date = date.today()
    await db.commit()
    return {f"lesson{i}": lesson.id for i, lesson in enumerate(lessons, start=1)}


async def test_progress_reports_counts_modules_and_activity(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed(db_session)

    response = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["level"] == "beginner"
    assert body["counts"] == {
        "total": 4,
        "completed": 1,
        "available": 1,
        "locked": 2,
        "percent": 25.0,
    }
    assert body["modules"] == [
        {"module": "vocabulary", "total": 3, "completed": 1},
        {"module": "sarf", "total": 1, "completed": 0},
    ]
    assert body["xp"] == 55
    assert body["streak_days"] == 4
    assert body["last_activity_date"] == date.today().isoformat()
    assert body["next_lesson"]["id"] == ids["lesson2"]


async def test_progress_lists_only_submitted_quizzes_newest_first(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed(db_session)

    response = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert response.status_code == 200
    quizzes = response.json()["recent_quizzes"]
    assert [item["score"] for item in quizzes] == [4, 2]
    assert [item["lesson_id"] for item in quizzes] == [
        ids["lesson1"],
        ids["lesson2"],
    ]
    assert [item["passed"] for item in quizzes] == [True, False]
    assert all(item["total"] == 5 for item in quizzes)


async def test_empty_progress_is_well_formed(client, auth_headers) -> None:
    response = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["total"] == 0
    assert body["counts"]["percent"] == 0.0
    assert body["modules"] == []
    assert body["next_lesson"] is None
    assert body["recent_quizzes"] == []
    assert body["xp"] == 0


async def test_progress_requires_authentication(client) -> None:
    assert (await client.get("/api/v1/path/progress")).status_code == 401
