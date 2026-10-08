from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create(client: AsyncClient, headers: dict, verse_id: int = 1, note: str | None = None, collection: str | None = None):
    payload: dict = {"verse_id": verse_id}
    if note is not None:
        payload["note"] = note
    if collection is not None:
        payload["collection"] = collection
    return await client.post("/api/v1/bookmarks", json=payload, headers=headers)


@pytest.mark.asyncio
async def test_create_and_list_bookmark(client: AsyncClient, auth_headers, seed_quran_data):
    r = await _create(client, auth_headers, verse_id=1, note="study", collection="favs")
    assert r.status_code == 200
    body = r.json()
    assert body["verse_id"] == 1
    assert body["note"] == "study"
    assert body["collection"] == "favs"
    assert body["surah_number"] == 1
    assert body["ayah_number"] == 1

    r = await client.get("/api/v1/bookmarks", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/bookmarks?collection=favs", headers=auth_headers)
    assert r.json()["total"] == 1
    r = await client.get("/api/v1/bookmarks?collection=other", headers=auth_headers)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_or_update_is_idempotent_per_verse(client: AsyncClient, auth_headers, seed_quran_data):
    await _create(client, auth_headers, verse_id=1, note="a", collection="c1")
    r = await _create(client, auth_headers, verse_id=1, note="b", collection="c2")
    assert r.status_code == 200
    r = await client.get("/api/v1/bookmarks", headers=auth_headers)
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["note"] == "b"
    assert data["items"][0]["collection"] == "c2"


@pytest.mark.asyncio
async def test_delete_bookmark(client: AsyncClient, auth_headers, seed_quran_data):
    r = await _create(client, auth_headers, verse_id=1)
    bid = r.json()["id"]
    r = await client.delete(f"/api/v1/bookmarks/{bid}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get("/api/v1/bookmarks", headers=auth_headers)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_cannot_touch_other_users_bookmarks(client: AsyncClient, auth_headers, seed_quran_data):
    r = await _create(client, auth_headers, verse_id=1, note="mine")
    bid = r.json()["id"]

    other = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "name": "Other User", "password": "SecurePassword123!", "native_lang": "en", "ui_lang": "en", "level": "beginner"},
    )
    token = other.json()["tokens"]["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/api/v1/bookmarks", headers=other_headers)
    assert r.json()["total"] == 0

    r = await client.delete(f"/api/v1/bookmarks/{bid}", headers=other_headers)
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/bookmarks/{bid}", headers=auth_headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_bookmark_requires_auth_and_existing_verse(client: AsyncClient, auth_headers, seed_quran_data):
    r = await client.get("/api/v1/bookmarks")
    assert r.status_code == 401
    r = await _create(client, auth_headers, verse_id=9999)
    assert r.status_code == 404
