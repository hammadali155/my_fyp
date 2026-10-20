from __future__ import annotations

from collections import OrderedDict
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.services.morphology_service import (
    is_rootless_gold,
    normalize_arabic,
    score_root_prediction,
    strip_tashkeel,
)


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
async def test_analyze_word_prefers_exact_match_over_stem_collision(client: AsyncClient, seed_quran_data: None, db_session):
    from app.models.quran import Verse, Word

    verse = Verse(
        id=3,
        surah_id=1,
        ayah_number=3,
        text_uthmani="بدْعًا لُبْدًا",
        text_imlaei="بدعا لبدا",
        translation_en="",
        translation_ur="",
        juz_number=1,
        hizb_number=1,
        page_number=1,
    )
    db_session.add(verse)
    await db_session.flush()
    db_session.add_all(
        [
            Word(
                verse_id=3,
                position=1,
                text_uthmani="دَعَا",
                text_imlaei="دعا",
                translation_en="",
                transliteration="",
                root="دعو",
                lemma="دَعَا",
                pos_tag="V",
            ),
            Word(
                verse_id=3,
                position=2,
                text_uthmani="بدْعًا",
                text_imlaei="بدْعًا",
                translation_en="",
                transliteration="",
                root="بدع",
                lemma="بِدْع",
                pos_tag="N",
            ),
            Word(
                verse_id=3,
                position=3,
                text_uthmani="بَدَا",
                text_imlaei="بدا",
                translation_en="",
                transliteration="",
                root="بدو",
                lemma="بَدَا",
                pos_tag="V",
            ),
            Word(
                verse_id=3,
                position=4,
                text_uthmani="لُبْدًا",
                text_imlaei="لُبدًا",
                translation_en="",
                transliteration="",
                root="لبد",
                lemma="لِبْد",
                pos_tag="ADJ",
            ),
        ]
    )
    await db_session.commit()

    resp = await client.post("/api/v1/morphology/analyze", json={"word": "بدْعًا"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["root"] == "بدع"
    assert data["source"] == "corpus"

    resp = await client.post("/api/v1/morphology/analyze", json={"word": "لُبدًا"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["root"] == "لبد"
    assert data["source"] == "corpus"


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


def test_score_root_prediction_real_roots_and_weak_wildcard():
    assert score_root_prediction("كتب", "كتب") == (True, False)
    assert score_root_prediction("قول", "قول") == (True, False)
    assert score_root_prediction("قول", "ق.و.ل") == (True, False)
    assert score_root_prediction("قول", "ق#ل") == (True, True)
    assert score_root_prediction("خير", "خ#ر") == (True, True)
    assert score_root_prediction("ليل", "ل#ل") == (True, True)
    assert score_root_prediction("وفي", "#ف#") == (True, True)
    assert score_root_prediction("كتب", "ك#ب") == (False, False)
    assert score_root_prediction("شقق", "ش#ق") == (False, False)
    assert score_root_prediction("كتب", "كتبب") == (False, False)
    assert score_root_prediction("كتب", "حمد") == (False, False)
    assert score_root_prediction("كتب", "") == (False, False)
    assert score_root_prediction("كتب", None) == (False, False)


def test_score_root_prediction_rootless_gold_needs_empty_prediction():
    assert is_rootless_gold("ـ")
    assert is_rootless_gold("ـ ")
    assert is_rootless_gold("")
    assert is_rootless_gold(None)
    assert not is_rootless_gold("كتب")

    assert score_root_prediction("ـ", "") == (True, False)
    assert score_root_prediction("ـ", None) == (True, False)
    assert score_root_prediction("ـ", "ـ") == (False, False)
    assert score_root_prediction("ـ", "علي") == (False, False)
    assert score_root_prediction(None, "") == (True, False)
    assert score_root_prediction(None, "كتب") == (False, False)


def test_convert_weak_placeholders_fills_weak_radicals_from_lemma():
    from app.services.camel_service import convert_weak_placeholders

    # roots verified against the installed camel_tools builtin DB:
    # قول -> ق.#.ل (lex قَوْل), خير -> خ.#.ر, ليل -> ل.#.ل, وجد -> #.ج.د
    assert convert_weak_placeholders("ق.#.ل", "قَوْل") == "ق.و.ل"
    assert convert_weak_placeholders("خ.#.ر", "خَيْر") == "خ.ي.ر"
    assert convert_weak_placeholders("ل.#.ل", "لَيْل") == "ل.ي.ل"
    assert convert_weak_placeholders("#.ج.د", "وَجَد") == "و.ج.د"
    # defective verb: رمى -> ر.م.# (lex رَمَى, normalised رمي)
    assert convert_weak_placeholders("ر.م.#", "رَمَى") == "ر.م.ي"
    # dot-removed input keeps dot-removed output
    assert convert_weak_placeholders("ق#ل", "قَوْل") == "قول"
    # gap mismatch keeps '#': أوفى -> #.ف.#; the leading gap has two letters
    # (ا + و augment) for one slot, so slot 0 stays '#' for the wildcard path
    assert convert_weak_placeholders("#.ف.#", "أَوْفَى") == "#.ف.ي"
    # nothing to resolve, nothing to align with, empty input
    assert convert_weak_placeholders("ق.و.ل", "قَوْل") == "ق.و.ل"
    assert convert_weak_placeholders("ق.#.ل", None) == "ق.#.ل"
    assert convert_weak_placeholders(None, "قَوْل") is None
    assert convert_weak_placeholders("", "قَوْل") == ""

    # composition: a resolved prediction needs no wildcard any more
    assert score_root_prediction("قول", convert_weak_placeholders("ق.#.ل", "قَوْل")) == (True, False)


def test_analyze_with_camel_skips_placeholder_roots(monkeypatch):
    from app.services import camel_service

    analyses = [
        {"root": "O", "lex": "يوف", "pos": "noun_prop"},
        {"root": "و.ف.#", "lex": "وَفَى", "pos": "verb"},
    ]
    fake_analyzer = SimpleNamespace(analyze=lambda word: analyses)
    monkeypatch.setattr(camel_service, "camel_available", lambda: True)
    monkeypatch.setattr(camel_service, "_get_analyzer", lambda: fake_analyzer)
    monkeypatch.setattr(camel_service, "_cache", OrderedDict())
    monkeypatch.setattr(camel_service, "_get_lexicon", lambda: (frozenset(), frozenset(), {}))

    result = camel_service.analyze_with_camel("يعسيا")
    assert result is not None
    assert result["root"] == "و.ف.#"


def test_analyze_with_bert_falls_back_to_plain_analyzer_on_oov(monkeypatch):
    from app.services import camel_service

    oov_analysis = {"root": "O", "lex": "يسعى", "pos": "noun_prop"}
    fake_disambig = SimpleNamespace(
        disambiguate=lambda words: [SimpleNamespace(analyses=[SimpleNamespace(score=1.0, analysis=oov_analysis)])]
    )
    plain_good = {"root": "س.ع.و", "lex": "سَعِيَ", "pos": "verb"}
    monkeypatch.setattr(camel_service, "bert_available", lambda: True)
    monkeypatch.setattr(camel_service, "_get_bert_disambig", lambda: fake_disambig)
    monkeypatch.setattr(camel_service, "analyze_with_camel", lambda word, rank=True: plain_good)

    result = camel_service.analyze_with_bert("يسعى")
    assert result == plain_good


def test_disambiguate_verse_with_bert_single_call(monkeypatch):
    from app.services import camel_service

    a_bis = {"root": "س.ب.ح", "lex": "سَبَحَ", "pos": "verb"}
    a_allah = {"root": "ل.ه.و", "lex": "اللَّهُ", "pos": "noun_prop"}
    calls: list[list[str]] = []

    def fake_disambiguate(tokens):
        calls.append(list(tokens))
        return [
            SimpleNamespace(analyses=[SimpleNamespace(score=1.0, analysis=a_bis)]),
            SimpleNamespace(analyses=[SimpleNamespace(score=0.5, analysis=a_allah)]),
            SimpleNamespace(analyses=[]),
        ]

    monkeypatch.setattr(camel_service, "bert_available", lambda: True)
    monkeypatch.setattr(
        camel_service, "_get_bert_disambig", lambda: SimpleNamespace(disambiguate=fake_disambiguate)
    )

    result = camel_service.disambiguate_verse_with_bert("بِسْمِ اللَّهِ الرَّحْمَٰنِ")

    assert calls == [["بِسْمِ", "اللَّهِ", "الرَّحْمَٰنِ"]]
    assert result is not None
    assert result[1] is a_bis
    assert result[2] is a_allah
    assert 3 in result and result[3] is None


def test_disambiguate_verse_with_bert_handles_failure(monkeypatch):
    from app.services import camel_service

    monkeypatch.setattr(camel_service, "bert_available", lambda: False)
    assert camel_service.disambiguate_verse_with_bert("بِسْمِ اللَّهِ") is None
    assert camel_service.disambiguate_verse_with_bert("   ") is None

    def boom(tokens):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(camel_service, "bert_available", lambda: True)
    monkeypatch.setattr(camel_service, "_get_bert_disambig", lambda: SimpleNamespace(disambiguate=boom))
    assert camel_service.disambiguate_verse_with_bert("بِسْمِ اللَّهِ") is None


def test_spelling_variants_cover_quranic_imlaei_quirks():
    from app.services.camel_service import _spelling_variants

    assert "امن" in _spelling_variants("ءامن")
    assert "صلحت" in _spelling_variants("الصلحت")
    assert "صلحت" in _spelling_variants("فالصلحت")
    assert "شهدة" in _spelling_variants("للشهدة")
    assert "مؤمنة" in _spelling_variants("مؤمنت")
    assert "المليكة" in _spelling_variants("الملئكة")
    for word in ("ءامن", "كتب", "الصلحت"):
        assert word not in _spelling_variants(word)
        assert "" not in _spelling_variants(word)


def test_analyze_with_camel_retries_spelling_variants(monkeypatch):
    from app.services import camel_service

    good = {"root": "ص.ل.ح", "lex": "صَلَحَ", "pos": "verb"}

    class FakeAnalyzer:
        def analyze(self, w: str):
            return [good] if w == "صلحت" else []

    monkeypatch.setattr(camel_service, "camel_available", lambda: True)
    monkeypatch.setattr(camel_service, "_get_analyzer", lambda: FakeAnalyzer())
    monkeypatch.setattr(camel_service, "_cache", OrderedDict())
    monkeypatch.setattr(camel_service, "_get_lexicon", lambda: (frozenset(), frozenset(), {}))

    result = camel_service.analyze_with_camel("الصلحت")
    assert result == good


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
