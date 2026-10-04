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


@pytest.mark.asyncio
async def test_analyze_word_camel_source_when_not_in_corpus(client: AsyncClient, monkeypatch):
    from app.services import camel_service

    fake_raw = {"root": "ك.ت.ب", "lex": "كَتَبَ", "pos": "verb", "pattern": "1َ2َ3َ"}
    monkeypatch.setattr(camel_service, "camel_available", lambda: True)
    monkeypatch.setattr(camel_service, "analyze_with_camel", lambda word: fake_raw)

    response = await client.post("/api/v1/morphology/analyze", json={"word": "كتب"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "camel"
    assert data["root"] == "كتب"
    assert data["lemma"] == "كَتَبَ"
    assert data["pos_tag"] == "verb"
    assert data["pattern"] == "1َ2َ3َ"
    assert data["is_quranic"] is False


@pytest.mark.asyncio
async def test_analyze_word_rules_fallback_when_camel_missing(client: AsyncClient, monkeypatch):
    from app.services import camel_service

    monkeypatch.setattr(camel_service, "camel_available", lambda: False)
    monkeypatch.setattr(camel_service, "analyze_with_camel", lambda word: None)

    response = await client.post("/api/v1/morphology/analyze", json={"word": "كتب"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "rules"
    assert data["is_quranic"] is False


@pytest.mark.asyncio
async def test_conjugate_sound_root_form_2(client: AsyncClient):
    response = await client.post("/api/v1/morphology/conjugate", json={"root": "كتب", "form": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is True
    assert data["past"] == "كَتَّبَ"
    assert data["present"] == "يُكَتِّبُ"
    assert data["imperative"] == "كَتِّبْ"  # diacritics per template


@pytest.mark.asyncio
async def test_conjugate_form1(client: AsyncClient):
    response = await client.post("/api/v1/morphology/conjugate", json={"root": "كتب", "form": 1})
    data = response.json()
    assert data["supported"] is True
    assert data["past"] == "كَتَبَ"
    assert data["present"] == "يَكْتَبُ"


@pytest.mark.asyncio
async def test_conjugate_rejects_weak_and_hamzated_and_doubled(client: AsyncClient):
    for root, reason in (
        ("سمو", "weak"),
        ("قال", "weak"),
        ("أخذ", "hamzated"),
        ("ردد", "doubled"),
    ):
        response = await client.post("/api/v1/morphology/conjugate", json={"root": root, "form": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["supported"] is False
        assert reason in data["unsupported_reason"]
        assert data["past"] is None


@pytest.mark.asyncio
async def test_conjugate_validates_form_range(client: AsyncClient):
    response = await client.post("/api/v1/morphology/conjugate", json={"root": "كتب", "form": 11})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_word_family_groups_by_pos(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/morphology/word-family/رحم")
    assert response.status_code == 200
    data = response.json()
    assert data["total_occurrences"] == 2
    lemmas = {g["lemma"] for g in data["groups"]}
    assert lemmas == {"رَحْمَن", "رَحِيم"}
    for g in data["groups"]:
        assert g["pos_tag"] == "ADJ"
        assert g["count"] == 1
        assert g["example"]["surah_number"] == 1
        assert g["example"]["word_text"]


@pytest.mark.asyncio
async def test_patterns_returns_verb_forms_and_noun_patterns(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/morphology/patterns")
    assert response.status_code == 200
    data = response.json()
    assert len(data["verb_forms"]) == 10
    assert data["verb_forms"][0]["form_number"] == 1
    assert len(data["noun_patterns"]) >= 5
    hamd = next(p for p in data["noun_patterns"] if p["pattern"] == "فَعْل")
    assert hamd["example"] is not None
    assert hamd["example"]["lemma"] == "حَمْد"
