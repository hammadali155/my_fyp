from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.morphology_service import normalize_arabic, strip_tashkeel


def test_arabic_normalization():
    # Test tashkeel removal
    raw = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
    stripped = strip_tashkeel(raw)
    assert "ِ" not in stripped
    assert "َ" not in stripped
    assert "ّ" not in stripped

    # Test alef normalization
    assert normalize_arabic("أَنْعَمْتَ") == "انعمت"
    assert normalize_arabic("إِيَّاكَ") == "اياك"
    assert normalize_arabic("ٱهْدِنَا") == "اهدنا"


@pytest.mark.asyncio
async def test_clitic_segmentation_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/morphology/segment", params={"word": "والحمد"})
    assert response.status_code == 200
    data = response.json()
    assert data["prefix"]["clitic"] == "وال"
    assert data["stem"] == "حمد"


@pytest.mark.asyncio
async def test_list_verb_forms(client: AsyncClient):
    response = await client.get("/api/v1/morphology/forms")
    assert response.status_code == 200
    forms = response.json()
    assert len(forms) == 10
    assert forms[0]["form_number"] == 1
    assert forms[9]["form_number"] == 10
    assert forms[9]["name"].startswith("Form X")


@pytest.mark.asyncio
async def test_analyze_word_quranic(client: AsyncClient, seed_quran_data: None):
    # Analyze Quranic word 'الرحمن'
    response = await client.post("/api/v1/morphology/analyze", json={"word": "ٱلرَّحْمَـٰنِ"})
    assert response.status_code == 200
    data = response.json()
    assert data["root"] == "رحم"
    assert data["is_quranic"] is True
    assert data["lemma"] == "رَحْمَن"


@pytest.mark.asyncio
async def test_root_concordance(client: AsyncClient, seed_quran_data: None):
    # Query concordance for root 'حمد'
    response = await client.get("/api/v1/morphology/roots/حمد")
    assert response.status_code == 200
    data = response.json()
    assert data["root"] == "حمد"
    assert data["total_occurrences"] >= 1
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["surah_number"] == 1
