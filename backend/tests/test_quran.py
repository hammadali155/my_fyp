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


@pytest.mark.asyncio
async def test_word_response_includes_optional_morphology_fields(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/verses/1")
    assert response.status_code == 200
    word = response.json()["words"][0]
    for field in ("pattern", "tense", "voice", "gender", "number", "person", "features_json"):
        assert field in word
        assert word[field] is None


@pytest.mark.asyncio
async def test_get_verse_by_surah_and_ayah(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/surahs/1/verses/1")
    assert response.status_code == 200
    verse = response.json()
    assert verse["ayah_number"] == 1
    assert len(verse["words"]) == 4
    word = verse["words"][0]
    for field in ("pattern", "tense", "voice", "gender", "number", "person", "features_json"):
        assert field in word


@pytest.mark.asyncio
async def test_get_verse_by_surah_and_ayah_not_found(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/surahs/1/verses/99")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_verses_filter_by_juz_and_page_number(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/verses?juz_number=1&page_number=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    response = await client.get("/api/v1/quran/verses?juz_number=30")
    assert response.json()["total"] == 0
    response = await client.get("/api/v1/quran/verses?page_number=2")
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_ignores_arabic_diacritics_and_reports_field(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/search?q=الرَّحْمَٰنِ")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["matched_field"] == "text_imlaei"


@pytest.mark.asyncio
async def test_search_english_matches_translation_and_reports_field(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/search?q=praise")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["matched_field"] == "translation_en"


@pytest.mark.asyncio
async def test_search_pagination_max_50(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/search?q=Allah&page_size=51")
    assert response.status_code == 422
    response = await client.get("/api/v1/quran/search?q=Allah&page=1&page_size=1")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_roots_ranked_with_filters(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/quran/roots")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    counts = [i["occurrence_count"] for i in data["items"]]
    assert counts == sorted(counts, reverse=True)
    roots = {i["root"]: i["occurrence_count"] for i in data["items"]}
    assert roots["رحم"] == 2
    assert roots["سمو"] == 1

    response = await client.get("/api/v1/quran/roots?min_count=2")
    assert response.json()["total"] == 1

    response = await client.get("/api/v1/quran/roots?pos_tag=PN")
    assert all(i["root"] == "اله" for i in response.json()["items"])

    response = await client.get("/api/v1/quran/roots?surah_number=1&min_count=2")
    assert response.json()["total"] == 1

    response = await client.get("/api/v1/quran/roots?limit=501")
    assert response.status_code == 422

    response = await client.get("/api/v1/quran/roots?limit=1")
    assert response.json()["total"] == 1
