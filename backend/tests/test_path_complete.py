from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, LessonPrerequisite
from app.models.user import User


async def _learner(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "talib@example.com"))
    ).scalar_one()


async def _lesson(db: AsyncSession, sequence: int, root: str) -> Lesson:
    lesson = Lesson(
        title=f"Root {root}",
        module="vocabulary",
        level="beginner",
        sequence=sequence,
        root=root,
        content_json={"root": root, "forms": [], "example": None},
        est_minutes=10,
    )
    db.add(lesson)
    await db.flush()
    return lesson


async def _seed_chain(db: AsyncSession) -> list[int]:
    roots = ["رحم", "علم", "قول", "كتب", "حمد"]
    lessons = [await _lesson(db, index + 1, root) for index, root in enumerate(roots)]
    for previous, current in zip(lessons, lessons[1:], strict=False):
        db.add(
            LessonPrerequisite(
                lesson_id=current.id, requires_lesson_id=previous.id
            )
        )
    await db.commit()
    return [lesson.id for lesson in lessons]


async def _complete(client, auth_headers, lesson_id: int):
    return await client.post(
        f"/api/v1/path/lessons/{lesson_id}/complete", headers=auth_headers
    )


async def test_first_completion_awards_xp_and_unlocks_next(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await _complete(client, auth_headers, ids[0])
    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"] == ids[0]
    assert body["status"] == "completed"
    assert body["score"] is None
    assert body["unlocked"] == [ids[1]]
    assert body["xp_awarded"] == 20
    assert body["streak_days"] == 1

    db_session.expire_all()
    user = await _learner(db_session)
    assert user.xp == 20
    assert user.streak_days == 1
    assert user.last_activity_date == datetime.now(UTC).date()

    plan = await client.get("/api/v1/path/plan", headers=auth_headers)
    statuses = {row["id"]: row["status"] for row in plan.json()["lessons"]}
    assert statuses[ids[0]] == "completed"
    assert statuses[ids[1]] == "available"
    assert statuses[ids[2]] == "locked"


async def test_repeating_completion_is_idempotent(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    first = await _complete(client, auth_headers, ids[0])
    second = await _complete(client, auth_headers, ids[0])
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["xp_awarded"] == 0
    assert second.json()["unlocked"] == []

    db_session.expire_all()
    user = await _learner(db_session)
    assert user.xp == 20


async def test_completing_a_locked_lesson_returns_409(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await _complete(client, auth_headers, ids[2])
    assert response.status_code == 409


async def test_streak_counts_one_day_once_and_resets_after_a_gap(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    for lesson_id in ids[:3]:
        assert (await _complete(client, auth_headers, lesson_id)).status_code == 200

    db_session.expire_all()
    user = await _learner(db_session)
    assert user.xp == 60
    assert user.streak_days == 1

    user.last_activity_date = datetime.now(UTC).date() - timedelta(days=1)
    user.streak_days = 1
    await db_session.commit()

    response = await _complete(client, auth_headers, ids[3])
    assert response.status_code == 200
    assert response.json()["streak_days"] == 2

    db_session.expire_all()
    user = await _learner(db_session)
    user.last_activity_date = datetime.now(UTC).date() - timedelta(days=3)
    user.streak_days = 5
    await db_session.commit()

    response = await _complete(client, auth_headers, ids[4])
    assert response.status_code == 200
    assert response.json()["streak_days"] == 1


async def test_complete_requires_authentication(client, db_session: AsyncSession) -> None:
    ids = await _seed_chain(db_session)
    response = await client.post(f"/api/v1/path/lessons/{ids[0]}/complete")
    assert response.status_code == 401


async def test_completed_lesson_still_reads_its_content(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)
    await _complete(client, auth_headers, ids[0])

    response = await client.get(
        f"/api/v1/path/lessons/{ids[0]}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
