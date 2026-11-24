from __future__ import annotations

import pytest

from app.services.quiz_service import (
    PROMPTS,
    QuizAnchor,
    QuizCandidate,
    QuizGenerationError,
    QuizReference,
    QuizSlot,
    generate_quiz,
)


def _candidate(
    value: str,
    pos_tag: str,
    root: str,
    word_id: int,
    verse_id: int = 1,
) -> QuizCandidate:
    return QuizCandidate(
        value=value,
        pos_tag=pos_tag,
        root=root,
        word_id=word_id,
        verse_id=verse_id,
    )


ANCHOR = QuizAnchor(
    word_id=1,
    verse_id=1,
    text_uthmani="عِلْمٌ",
    root="علم",
    pos_tag="N",
    gloss="knowledge",
    surah_number=1,
    ayah_number=1,
)

ROOT_CANDIDATES = [
    _candidate("علم", "N", "علم", 2),
    _candidate("حكم", "N", "حكم", 3),
    _candidate("كتب", "N", "كتب", 4),
    _candidate("قلم", "N", "قلم", 5),
    _candidate("عظيم", "ADJ", "عظم", 6),
    _candidate("استكبر", "N", "استكبر", 7),
]

GLOSS_CANDIDATES = [
    _candidate("knowledge", "N", "علم", 2),
    _candidate("knowledge of", "N", "علم", 3),
    _candidate("understanding", "N", "فهم", 4),
    _candidate("a study", "N", "درس", 5),
    _candidate("wisdom", "N", "حكم", 6),
    _candidate("a very long gloss", "N", "طول", 7),
    _candidate("knowing", "ADJ", "علم", 8),
]

FILL_ANCHOR = QuizAnchor(
    word_id=10,
    verse_id=2,
    text_uthmani="نُورٌ",
    root="نور",
    pos_tag="N",
    gloss="light",
    surah_number=2,
    ayah_number=255,
    hidden_position=2,
    verse_text_uthmani="عِلْمٌ نُورٌ",
)

FILL_CANDIDATES = [
    _candidate("نُورٌ", "N", "نور", 11),
    _candidate("قَلَمٌ", "N", "قلم", 12),
    _candidate("كِتَابٌ", "N", "كتب", 13),
    _candidate("بَابٌ", "N", "بوب", 14),
    _candidate("عَظِيمٌ", "ADJ", "عظم", 15),
]


def _one_question(
    qtype: str,
    anchor: QuizAnchor,
    *,
    seed: int = 42,
    roots: list[QuizCandidate] | None = None,
    glosses: list[QuizCandidate] | None = None,
    word_texts: list[QuizCandidate] | None = None,
):
    questions = generate_quiz(
        [QuizSlot(type=qtype, anchor=anchor)],
        roots=roots or [],
        glosses=glosses or [],
        word_texts=word_texts or [],
        seed=seed,
    )
    assert len(questions) == 1
    return questions[0]


def test_root_question_has_one_correct_option_and_no_duplicate_options() -> None:
    question = _one_question("root", ANCHOR, roots=ROOT_CANDIDATES)

    assert question.id
    assert question.type == "root"
    assert question.prompt == PROMPTS["root"]
    assert len(question.options) == 4
    assert len({option.id for option in question.options}) == 4
    assert len({option.text for option in question.options}) == 4
    assert question.options[question.correct_index].id == "علم"
    assert sum(option.id == "علم" for option in question.options) == 1
    assert {option.id for option in question.options} == {
        "علم",
        "حكم",
        "كتب",
        "قلم",
    }
    assert question.reference == QuizReference(
        surah_number=1, ayah_number=1, word_id=1
    )
    assert question.explanation


def test_root_distractors_share_pos_and_similar_length_and_never_repeat_root() -> None:
    question = _one_question("root", ANCHOR, roots=ROOT_CANDIDATES)
    texts = {option.text for option in question.options}

    assert "عظيم" not in texts
    assert "استكبر" not in texts
    assert "علم" in texts


def test_meaning_distractors_differ_from_the_answer_and_its_root() -> None:
    question = _one_question("meaning", ANCHOR, glosses=GLOSS_CANDIDATES)
    texts = {option.text for option in question.options}

    assert question.options[question.correct_index].text == "knowledge"
    assert sum(option.text == "knowledge" for option in question.options) == 1
    assert "knowledge of" not in texts
    assert "knowing" not in texts
    assert "a very long gloss" not in texts
    assert len(texts) == 4
    assert question.reference.word_id == 1
    assert question.explanation


def test_fill_blank_uses_the_stored_verse_text_and_hides_by_position() -> None:
    question = _one_question(
        "fill_blank", FILL_ANCHOR, word_texts=FILL_CANDIDATES
    )

    assert question.verse_text_uthmani == FILL_ANCHOR.verse_text_uthmani
    assert question.hidden_position == 2
    assert question.word is None
    assert question.options[question.correct_index].text == "نُورٌ"
    assert sum(option.text == "نُورٌ" for option in question.options) == 1
    assert {option.text for option in question.options} == {
        "نُورٌ",
        "قَلَمٌ",
        "كِتَابٌ",
        "بَابٌ",
    }
    assert question.reference == QuizReference(
        surah_number=2, ayah_number=255, word_id=10
    )


def test_pos_question_uses_readable_labels() -> None:
    question = _one_question("pos", ANCHOR)

    assert question.options[question.correct_index].id == "N"
    assert question.options[question.correct_index].text == "Noun"
    assert len(question.options) == 4
    assert len({option.id for option in question.options}) == 4
    assert all(option.id != option.text for option in question.options)


def test_same_seed_produces_the_same_questions() -> None:
    slots = [
        QuizSlot(type="root", anchor=ANCHOR),
        QuizSlot(type="meaning", anchor=ANCHOR),
        QuizSlot(type="fill_blank", anchor=FILL_ANCHOR),
        QuizSlot(type="pos", anchor=ANCHOR),
        QuizSlot(type="root", anchor=ANCHOR),
    ]

    first = generate_quiz(
        slots,
        roots=ROOT_CANDIDATES,
        glosses=GLOSS_CANDIDATES,
        word_texts=FILL_CANDIDATES,
        seed=2026,
    )
    second = generate_quiz(
        slots,
        roots=ROOT_CANDIDATES,
        glosses=GLOSS_CANDIDATES,
        word_texts=FILL_CANDIDATES,
        seed=2026,
    )

    assert first == second
    assert [question.id for question in first] == [
        "q1",
        "q2",
        "q3",
        "q4",
        "q5",
    ]


def test_insufficient_distractors_raises_a_clear_error() -> None:
    candidates = [
        _candidate("علم", "N", "علم", 2),
        _candidate("عظيم", "ADJ", "عظم", 3),
    ]

    with pytest.raises(QuizGenerationError, match="distractor"):
        generate_quiz(
            [QuizSlot(type="root", anchor=ANCHOR)],
            roots=candidates,
            glosses=[],
            word_texts=[],
            seed=1,
        )


def test_generator_falls_back_to_other_pos_when_same_pos_is_short() -> None:
    anchor = QuizAnchor(
        word_id=20,
        verse_id=3,
        text_uthmani="أَنَّىٰ",
        root="اني",
        pos_tag="INTG",
        gloss="how",
        surah_number=2,
        ayah_number=223,
    )
    roots = [
        _candidate("اني", "INTG", "اني", 21),
        _candidate("اين", "INTG", "اين", 22),
        _candidate("علم", "N", "علم", 23),
        _candidate("كتب", "N", "كتب", 24),
        _candidate("قلم", "N", "قلم", 25),
    ]

    question = _one_question("root", anchor, roots=roots)

    assert question.options[question.correct_index].id == "اني"
    assert len(question.options) == 4
    assert len({option.id for option in question.options}) == 4
    assert sum(option.id == "اني" for option in question.options) == 1


def test_fill_blank_rejects_a_verse_token_that_does_not_match_the_word() -> None:
    anchor = QuizAnchor(
        word_id=10,
        verse_id=2,
        text_uthmani="خَاطِئٌ",
        root="خطا",
        pos_tag="N",
        gloss="wrong",
        surah_number=2,
        ayah_number=255,
        hidden_position=2,
        verse_text_uthmani="عِلْمٌ نُورٌ",
    )

    with pytest.raises(QuizGenerationError, match="[Ss]tored word"):
        generate_quiz(
            [QuizSlot(type="fill_blank", anchor=anchor)],
            roots=[],
            glosses=[],
            word_texts=FILL_CANDIDATES,
            seed=1,
        )
