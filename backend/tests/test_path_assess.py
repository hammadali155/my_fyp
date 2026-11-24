from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.quiz_service import QuizService


async def _answers(db: AsyncSession, correct_count: int) -> list[dict[str, str | int]]:
    questions, key = await QuizService(db).build_assessment()
    answers: list[dict[str, str | int]] = []
    for position, item in enumerate(key):
        correct = item["correct_option_id"]
        if position < correct_count:
            chosen = correct
        else:
            chosen = next(
                option.id
                for option in questions[item["index"] - 1].options
                if option.id != correct
            )
        answers.append({"index": item["index"], "option_id": chosen})
    return answers


async def test_assessment_returns_twenty_questions(
    client, auth_headers, seed_quiz_data: None
) -> None:
    response = await client.get("/api/v1/path/assess", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 20
    assert len(body["questions"]) == 20
    counts: dict[str, int] = {}
    for question in body["questions"]:
        counts[question["type"]] = counts.get(question["type"], 0) + 1
        assert len(question["options"]) >= 2
    assert counts == {
        "root": 5,
        "meaning": 5,
        "fill_blank": 5,
        "pos": 5,
    }
    assert "correct_option_id" not in response.text


async def test_assessment_is_deterministic(
    client, auth_headers, seed_quiz_data: None
) -> None:
    first = await client.get("/api/v1/path/assess", headers=auth_headers)
    second = await client.get("/api/v1/path/assess", headers=auth_headers)
    assert first.json() == second.json()


async def test_all_correct_places_advanced(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    answers = await _answers(db_session, correct_count=20)
    response = await client.post(
        "/api/v1/path/assess",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 20
    assert body["total"] == 20
    assert body["placed_level"] == "advanced"
    assert body["previous_level"] == "beginner"

    db_session.expire_all()
    user = (await db_session.execute(select(User))).scalars().one()
    assert user.level == "advanced"


async def test_twelve_correct_places_intermediate(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    answers = await _answers(db_session, correct_count=12)
    response = await client.post(
        "/api/v1/path/assess",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["score"] == 12
    assert response.json()["placed_level"] == "intermediate"


async def test_all_wrong_places_beginner(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    answers = await _answers(db_session, correct_count=0)
    response = await client.post(
        "/api/v1/path/assess",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["score"] == 0
    assert response.json()["placed_level"] == "beginner"


async def test_assessment_requires_authentication(client) -> None:
    assert (await client.get("/api/v1/path/assess")).status_code == 401
    assert (
        await client.post("/api/v1/path/assess", json={"answers": []})
    ).status_code == 401
