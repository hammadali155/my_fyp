from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from app.services.progress_service import compute_streak_update, xp_for_rating


def test_streak_same_day_unchanged():
    today = date(2026, 10, 4)
    assert compute_streak_update(today, 5, today) == 5


def test_streak_consecutive_day_increments():
    today = date(2026, 10, 4)
    assert compute_streak_update(today - timedelta(days=1), 5, today) == 6


def test_streak_missed_day_resets():
    today = date(2026, 10, 4)
    assert compute_streak_update(today - timedelta(days=2), 5, today) == 1
    assert compute_streak_update(None, 0, today) == 1


def test_xp_table():
    assert xp_for_rating(1) == 2
    assert xp_for_rating(4) == 15


@pytest.mark.asyncio
async def test_review_updates_user_progress_and_first_badge(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    from app.models.quran import Word

    word_id = (await db_session.execute(select(Word.id).limit(1))).scalar_one()
    r = await client.post(
        "/api/v1/srs/cards",
        json={"item_type": "vocabulary", "front": "f", "back": "b", "word_id": word_id},
        headers=auth_headers,
    )
    assert r.status_code == 201
    card_id = r.json()["id"]

    r = await client.post(
        "/api/v1/srs/review",
        json={"card_id": card_id, "rating": 4, "review_duration_ms": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 200

    user = (await db_session.execute(select(User))).scalars().one()
    assert user.xp == 15
    assert user.streak_days == 1
    assert user.last_review_date is not None

    r = await client.get("/api/v1/progress/badges", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    earned = {b["slug"]: b["earned"] for b in data["items"]}
    assert earned["first_review"] is True
    assert earned["reviews_100"] is False
    assert data["earned_count"] == 1


@pytest.mark.asyncio
async def test_first_custom_deck_badge(client: AsyncClient, auth_headers):
    await client.post("/api/v1/decks", json={"name": "My deck"}, headers=auth_headers)
    r = await client.get("/api/v1/progress/badges", headers=auth_headers)
    earned = {b["slug"]: b["earned"] for b in r.json()["items"]}
    assert earned["first_custom_deck"] is True


@pytest.mark.asyncio
async def test_badges_require_auth(client: AsyncClient):
    r = await client.get("/api/v1/progress/badges")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_srs_stats_use_user_streak(client: AsyncClient, auth_headers, seed_quran_data, db_session):
    user = (await db_session.execute(select(User))).scalars().one()
    user.streak_days = 7
    await db_session.commit()
    r = await client.get("/api/v1/srs/stats", headers=auth_headers)
    assert r.json()["streak_days"] == 7
