from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, LessonPrerequisite, UserLesson
from app.models.user import User


async def _learner(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "talib@example.com"))
    ).scalar_one()


async def _lesson(
    db: AsyncSession,
    *,
    level: str,
    sequence: int,
    root: str,
    module: str = "vocabulary",
) -> Lesson:
    lesson = Lesson(
        title=f"Root {root}",
        module=module,
        level=level,
        sequence=sequence,
        root=root,
        content_json={"root": root, "forms": [], "example": None},
        est_minutes=10,
    )
    db.add(lesson)
    await db.flush()
    return lesson


async def _seed_chain(db: AsyncSession) -> dict[str, int]:
    first = await _lesson(db, level="beginner", sequence=1, root="رحم")
    second = await _lesson(db, level="beginner", sequence=2, root="علم")
    third = await _lesson(db, level="beginner", sequence=3, root="قول")
    other = await _lesson(db, level="intermediate", sequence=1, root="كتب")
    db.add(LessonPrerequisite(lesson_id=second.id, requires_lesson_id=first.id))
    db.add(LessonPrerequisite(lesson_id=third.id, requires_lesson_id=second.id))
    user = await _learner(db)
    db.add(
        UserLesson(
            user_id=user.id,
            lesson_id=first.id,
            status="completed",
        )
    )
    await db.commit()
    return {
        "first": first.id,
        "second": second.id,
        "third": third.id,
        "other": other.id,
    }


async def test_plan_lists_only_the_users_band_with_derived_status(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await client.get("/api/v1/path/plan", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["level"] == "beginner"
    assert [lesson["id"] for lesson in body["lessons"]] == [
        ids["first"],
        ids["second"],
        ids["third"],
    ]
    assert [lesson["status"] for lesson in body["lessons"]] == [
        "completed",
        "available",
        "locked",
    ]
    assert body["counts"] == {
        "total": 3,
        "completed": 1,
        "available": 1,
        "locked": 1,
    }
    assert body["next_lesson_id"] == ids["second"]
    assert ids["other"] not in [lesson["id"] for lesson in body["lessons"]]


async def test_lessons_endpoint_filters_by_status(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await client.get(
        "/api/v1/path/lessons", params={"status": "locked"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["lessons"][0]["id"] == ids["third"]


async def test_lesson_detail_available_returns_content(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await client.get(
        f"/api/v1/path/lessons/{ids['second']}", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == ids["second"]
    assert body["status"] == "available"
    assert body["content"]["root"] == "علم"


async def test_lesson_detail_locked_returns_409(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await client.get(
        f"/api/v1/path/lessons/{ids['third']}", headers=auth_headers
    )
    assert response.status_code == 409


async def test_lesson_detail_outside_band_returns_404(
    client, auth_headers, db_session: AsyncSession
) -> None:
    ids = await _seed_chain(db_session)

    response = await client.get(
        f"/api/v1/path/lessons/{ids['other']}", headers=auth_headers
    )
    assert response.status_code == 404


async def test_lesson_detail_unknown_returns_404(
    client, auth_headers
) -> None:
    response = await client.get("/api/v1/path/lessons/999999", headers=auth_headers)
    assert response.status_code == 404


async def test_plan_requires_authentication(client) -> None:
    response = await client.get("/api/v1/path/plan")
    assert response.status_code == 401


async def test_empty_plan_is_well_formed(client, auth_headers) -> None:
    response = await client.get("/api/v1/path/plan", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["lessons"] == []
    assert body["counts"]["total"] == 0
    assert body["next_lesson_id"] is None


async def test_registration_rejects_unknown_level(client) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "expert@example.com",
            "name": "Expert",
            "password": "SecurePassword123!",
            "level": "expert",
        },
    )
    assert response.status_code == 422
