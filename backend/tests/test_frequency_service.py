from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import Word
from app.services.frequency_service import FrequencyService


def _word(
    *,
    verse_id: int,
    position: int,
    text: str,
    root: str | None,
    lemma: str | None,
) -> Word:
    return Word(
        verse_id=verse_id,
        position=position,
        text_uthmani=text,
        root=root,
        lemma=lemma,
        pos_tag="N",
    )


async def _add_extra_words(db: AsyncSession) -> None:
    db.add_all(
        [
            _word(verse_id=1, position=5, text="رُحْم", root="رحم", lemma="رَحْمَة"),
            _word(verse_id=1, position=6, text="ـ", root="ـ", lemma="ـ"),
            _word(verse_id=1, position=7, text="بلا", root=None, lemma=None),
            _word(verse_id=1, position=8, text="رحيم", root="رحم", lemma="رَحِيم"),
        ]
    )
    await db.commit()


async def test_root_frequencies_rank_hand_made_words(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await _add_extra_words(db_session)

    rows = await FrequencyService(db_session).root_frequencies()

    assert rows == [
        ("رحم", 4),
        ("اله", 1),
        ("حمد", 1),
        ("سمو", 1),
    ]


async def test_root_frequencies_apply_min_count_and_limit(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await _add_extra_words(db_session)
    service = FrequencyService(db_session)

    assert await service.root_frequencies(min_count=2) == [("رحم", 4)]
    assert await service.root_frequencies(limit=2) == [("رحم", 4), ("اله", 1)]


async def test_lemma_frequencies_count_real_lemmas_only(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await _add_extra_words(db_session)

    rows = await FrequencyService(db_session).lemma_frequencies()

    assert rows[0] == ("رَحِيم", 2)
    assert ("ـ", 1) not in rows
    assert sum(count for _, count in rows) == 7


async def test_empty_corpus_returns_no_frequencies(db_session: AsyncSession) -> None:
    service = FrequencyService(db_session)

    assert await service.root_frequencies() == []
    assert await service.lemma_frequencies() == []
