from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import NahwAnnotation, Verse, Word
from app.services.tutor_context import (
    ContextReference,
    TutorContextService,
)


@pytest.fixture
def service(db_session: AsyncSession) -> TutorContextService:
    return TutorContextService(db_session)


async def seeded_verse(db_session: AsyncSession, ayah_number: int) -> Verse:
    return (
        await db_session.execute(
            select(Verse).where(Verse.surah_id == 1, Verse.ayah_number == ayah_number)
        )
    ).scalar_one()


async def test_verse_reference_pulls_verse_text_translation_and_words(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 2)

    result = await service.build(message="What does 1:2 mean?", languages=("en", "ur"))

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 2)]
    assert verse.text_uthmani in result.text
    assert verse.text_imlaei in result.text
    assert verse.translation_en in result.text
    assert verse.translation_ur in result.text
    assert "root حمد" in result.text
    assert "lemma حَمْد" in result.text
    assert "pos N" in result.text
    assert result.truncated is False
    assert result.unresolved_references == []
    assert result.verse_ids == [verse.id]


async def test_verse_without_nahw_annotations_says_so(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(message="Explain 1:2")

    assert "Nahw: not available in corpus" in result.text


async def test_nahw_annotations_are_rendered_when_present(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    word = (
        await db_session.execute(
            select(Word).where(Word.verse_id == 1, Word.position == 1)
        )
    ).scalar_one()
    db_session.add(
        NahwAnnotation(
            verse_id=1,
            word_id=word.id,
            token_index=1,
            role="مبتدأ",
            dep_type="SBJ",
            head_index=-1,
            irab="مرفوع",
            sentence_index=1,
        )
    )
    await db_session.commit()

    result = await service.build(message="Parse 1:1 for me")

    assert "مبتدأ" in result.text
    assert "SBJ" in result.text
    assert "مرفوع" in result.text


async def test_surah_name_reference_resolves_to_first_ayah(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 1)

    result = await service.build(message="Explain Surah Al-Fatihah")

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 1)]
    assert "Al-Fatihah" in result.text
    assert verse.text_uthmani in result.text
    assert result.unresolved_references == []


async def test_arabic_surah_name_reference_resolves(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(message="اشرح سورة الفاتحة")

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 1)]


async def test_unknown_verse_reference_is_reported_not_guessed(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(message="Tell me about 2:255")

    assert result.citations == []
    assert result.unresolved_references == ["2:255"]
    assert "2:255" in result.text
    assert "not found in the corpus" in result.text


async def test_unknown_surah_name_is_reported_not_guessed(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(message="What is Surah Al-Kahf about?")

    assert result.citations == []
    assert result.unresolved_references == ["Al-Kahf"]
    assert "not found in the corpus" in result.text


async def test_message_without_reference_returns_no_verse_context(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(message="How do I conjugate a Form I verb?")

    assert result.citations == []
    assert result.unresolved_references == []
    assert "No Quranic reference" in result.text
    assert result.truncated is False


async def test_length_cap_keeps_referenced_verse_first(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 2)

    result = await service.build(message="Explain 1:2", max_chars=220)

    assert len(result.text) <= 220
    assert result.truncated is True
    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 2)]
    assert verse.text_uthmani in result.text


async def test_explicit_reference_wins_over_message_text(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 2)

    result = await service.build(
        message="What does this mean?",
        reference=ContextReference(surah_number=1, ayah_number=2),
    )

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 2)]
    assert verse.text_uthmani in result.text


async def test_explicit_surah_only_reference_uses_first_ayah(
    service: TutorContextService, seed_quran_data
) -> None:
    result = await service.build(
        message="What does this mean?",
        reference=ContextReference(surah_number=1),
    )

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 1)]


async def test_word_reference_resolves_its_verse_and_marks_the_word(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    word = (
        await db_session.execute(
            select(Word).where(Word.verse_id == 2, Word.position == 1)
        )
    ).scalar_one()

    result = await service.build(
        message="Explain this word",
        reference=ContextReference(word_id=word.id),
    )

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 2)]
    assert "referenced word" in result.text


async def test_unsupported_language_is_marked_unavailable(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 2)

    result = await service.build(message="Explain 1:2", languages=("fr", "en"))

    assert "Translation (fr): not available in corpus" in result.text
    assert verse.translation_en in result.text


async def test_missing_translation_is_not_invented(
    service: TutorContextService, db_session: AsyncSession, seed_quran_data
) -> None:
    verse = await seeded_verse(db_session, 2)
    verse.translation_en = None
    verse.text_imlaei = None
    await db_session.commit()

    result = await service.build(message="Explain 1:2")

    assert [(c.surah, c.ayah) for c in result.citations] == [(1, 2)]
    assert "Translation (en): not available in corpus" in result.text
    assert "Imlaei: not available in corpus" in result.text
