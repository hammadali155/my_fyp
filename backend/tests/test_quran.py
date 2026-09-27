from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_surahs(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/surahs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    surah = data["items"][0]
    assert surah["number"] == 1
    assert surah["name_arabic"] == "الفاتحة"
    assert surah["name_english"] == "The Opener"


@pytest.mark.asyncio
async def test_get_surah_detail(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/surahs/1")
    assert response.status_code == 200
    surah = response.json()
    assert surah["number"] == 1
    assert surah["verse_count"] == 7


@pytest.mark.asyncio
async def test_get_surah_not_found(client: AsyncClient):
    response = await client.get("/api/v1/quran/surahs/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_verses_with_surah_filter(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/verses?surah_id=1&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    verse = data["items"][0]
    assert verse["ayah_number"] == 1
    assert "بِسْمِ" in verse["text_uthmani"]
    assert len(verse["words"]) == 4
    assert verse["words"][0]["text_uthmani"] == "بِسْمِ"
    assert verse["words"][0]["root"] == "سمو"


@pytest.mark.asyncio
async def test_get_single_verse_with_words(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/verses/1")
    assert response.status_code == 200
    verse = response.json()
    assert verse["id"] == 1
    assert verse["ayah_number"] == 1
    assert len(verse["words"]) == 4
    assert verse["words"][1]["text_uthmani"] == "ٱللَّهِ"


@pytest.mark.asyncio
async def test_search_quran_arabic(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/search?q=الرحمن")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["surah_number"] == 1


@pytest.mark.asyncio
async def test_search_quran_english(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/search?q=Merciful")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["ayah_number"] == 1
