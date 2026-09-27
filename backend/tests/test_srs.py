from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.srs import SRSCard
from app.services.srs_service import _sm2_schedule

# ---------------------------------------------------------------------------
# Unit tests: SM-2 scheduling algorithm
# ---------------------------------------------------------------------------


def _make_card(state: str = "new", ef: float = 2.50, interval: int = 0, reps: int = 0) -> SRSCard:
    card = SRSCard(
        user_id=1,
        item_type="root",
        front="كتب",
        back="to write",
        state=state,
        ease_factor=ef,
        interval_days=interval,
        repetitions=reps,
        lapses=0,
        due_date=datetime.now(UTC),
    )
    return card


def test_sm2_again_resets_to_learning():
    card = _make_card(state="review", ef=2.5, interval=10, reps=5)
    new_state, new_interval, new_ef, new_due = _sm2_schedule(card, rating=1, now=datetime.now(UTC))
    assert new_state == "learning"
    assert new_interval == 1
    assert new_ef < 2.5


def test_sm2_new_card_good_stays_learning():
    card = _make_card(state="new", reps=0)
    new_state, new_interval, new_ef, _ = _sm2_schedule(card, rating=3, now=datetime.now(UTC))
    assert new_state == "learning"
    assert new_interval >= 1


def test_sm2_new_card_easy_graduates_immediately():
    card = _make_card(state="new", reps=0)
    new_state, new_interval, _, _ = _sm2_schedule(card, rating=4, now=datetime.now(UTC))
    assert new_state == "review"
    assert new_interval >= 4


def test_sm2_review_good_multiplies_interval():
    card = _make_card(state="review", ef=2.5, interval=10, reps=3)
    new_state, new_interval, new_ef, _ = _sm2_schedule(card, rating=3, now=datetime.now(UTC))
    assert new_state == "review"
    assert new_interval == 25  # 10 * 2.5
    assert new_ef == pytest.approx(2.5, abs=0.01)


def test_sm2_review_hard_applies_multiplier():
    card = _make_card(state="review", ef=2.5, interval=10, reps=3)
    new_state, new_interval, new_ef, _ = _sm2_schedule(card, rating=2, now=datetime.now(UTC))
    assert new_state == "review"
    assert new_interval == 12  # round(10 * 1.20)
    assert new_ef < 2.5


def test_sm2_review_easy_boosts_ef():
    card = _make_card(state="review", ef=2.5, interval=10, reps=3)
    new_state, new_interval, new_ef, _ = _sm2_schedule(card, rating=4, now=datetime.now(UTC))
    assert new_state == "review"
    assert new_ef > 2.5
    assert new_interval > 10


def test_sm2_ef_never_below_minimum():
    card = _make_card(state="review", ef=1.30, interval=5, reps=3)
    _, _, new_ef, _ = _sm2_schedule(card, rating=1, now=datetime.now(UTC))
    assert new_ef >= 1.30


def test_sm2_due_date_is_future():
    card = _make_card(state="review", ef=2.5, interval=5, reps=2)
    now = datetime.now(UTC)
    _, new_interval, _, new_due = _sm2_schedule(card, rating=3, now=now)
    assert new_due > now
    assert (new_due - now).days >= new_interval - 1  # allow timedelta rounding


# ---------------------------------------------------------------------------
# Integration tests: SRS API endpoints
# ---------------------------------------------------------------------------


@pytest.fixture
async def srs_card_payload() -> dict:
    return {
        "item_type": "root",
        "front": "كتب",
        "back": "to write; root of writing-related words",
        "hint": "Think of 'kitaab' (book)",
        "surah_number": 2,
        "ayah_number": 2,
    }


async def test_create_card_requires_auth(client: AsyncClient, srs_card_payload: dict):
    resp = await client.post("/api/v1/srs/cards", json=srs_card_payload)
    assert resp.status_code == 401


async def test_create_card_authenticated(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
):
    resp = await client.post("/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["front"] == "كتب"
    assert data["state"] == "new"
    assert data["ease_factor"] == pytest.approx(2.5)
    assert data["interval_days"] == 0


async def test_due_queue_empty_for_new_user(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/srs/due", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["cards"] == []


async def test_due_queue_returns_due_cards(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
    db_session: AsyncSession,
):
    create_resp = await client.post(
        "/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers
    )
    assert create_resp.status_code == 201
    card_id = create_resp.json()["id"]

    due_resp = await client.get("/api/v1/srs/due", headers=auth_headers)
    assert due_resp.status_code == 200
    data = due_resp.json()
    assert data["total"] >= 1
    ids = [c["id"] for c in data["cards"]]
    assert card_id in ids


async def test_submit_review_good(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
):
    card = await client.post("/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers)
    card_id = card.json()["id"]

    resp = await client.post(
        "/api/v1/srs/review",
        json={"card_id": card_id, "rating": 3, "review_duration_ms": 4500},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_id"] == card_id
    assert data["new_state"] in ("learning", "review")
    assert data["new_interval_days"] >= 1


async def test_submit_review_again_lapses(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
):
    card = await client.post("/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers)
    card_id = card.json()["id"]

    resp = await client.post(
        "/api/v1/srs/review",
        json={"card_id": card_id, "rating": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_state"] == "learning"
    assert data["new_interval_days"] == 1


async def test_submit_review_card_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/srs/review",
        json={"card_id": 99999, "rating": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_get_stats_initial(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/srs/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cards"] == 0
    assert data["streak_days"] == 0
    assert data["reviews_today"] == 0


async def test_get_stats_after_review(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
):
    card = await client.post("/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers)
    card_id = card.json()["id"]

    await client.post(
        "/api/v1/srs/review",
        json={"card_id": card_id, "rating": 4},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/srs/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cards"] == 1
    assert data["reviews_today"] >= 1
    assert data["streak_days"] >= 1


async def test_delete_card(
    client: AsyncClient,
    auth_headers: dict,
    srs_card_payload: dict,
):
    card = await client.post("/api/v1/srs/cards", json=srs_card_payload, headers=auth_headers)
    card_id = card.json()["id"]

    del_resp = await client.delete(f"/api/v1/srs/cards/{card_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    due_resp = await client.get("/api/v1/srs/due", headers=auth_headers)
    ids = [c["id"] for c in due_resp.json()["cards"]]
    assert card_id not in ids


async def test_delete_card_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.delete("/api/v1/srs/cards/99999", headers=auth_headers)
    assert resp.status_code == 404
