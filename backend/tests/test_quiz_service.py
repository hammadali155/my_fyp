from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson
from app.models.quran import Verse, Word
from app.services.lesson_seed import seed_lessons
from app.services.quiz_service import QuizService

TINY_BANDS = {
    "beginner": (1, 2),
    "intermediate": (3, 3),
    "advanced": (4, 4),
}


async def _first_lesson(db: AsyncSession) -> Lesson:
    await seed_lessons(db, bands=TINY_BANDS, min_occurrences=1)
    await db.commit()
    return (
        await db.execute(select(Lesson).where(Lesson.root == "رحم"))
    ).scalar_one()


async def test_lesson_quiz_has_five_questions_and_four_options(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=1234
    )

    assert len(questions) == 5
    assert [q.type for q in questions] == [
        "root",
        "meaning",
        "fill_blank",
        "pos",
        "root",
    ]
    assert len(key) == 5
    assert [item["index"] for item in key] == [1, 2, 3, 4, 5]
    for question in questions:
        assert len(question.options) == 4
        assert len({option.id for option in question.options}) == 4
        assert all(isinstance(option.id, str) for option in question.options)
        assert all(option.text for option in question.options)


async def test_questions_do_not_leak_the_answer_key(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=99
    )

    for question, item in zip(questions, key, strict=True):
        dumped = question.model_dump()
        assert "correct_option_id" not in dumped
        assert "answer_key" not in dumped
        assert item["correct_option_id"] in {
            option.id for option in question.options
        }


async def test_builder_is_deterministic_for_one_seed(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    service = QuizService(db_session)
    first, first_key = await service.build_lesson_questions(lesson, seed=7)
    second, second_key = await service.build_lesson_questions(lesson, seed=7)

    assert [q.model_dump() for q in first] == [q.model_dump() for q in second]
    assert first_key == second_key


async def test_fill_blank_serves_the_stored_verse_verbatim(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, _ = await QuizService(db_session).build_lesson_questions(
        lesson, seed=5
    )
    fill = next(q for q in questions if q.type == "fill_blank")

    verse = (
        await db_session.execute(select(Verse).where(Verse.id == fill.verse_id))
    ).scalar_one()
    assert fill.verse_text_uthmani == verse.text_uthmani
    assert fill.hidden_position is not None
    assert 1 <= fill.hidden_position <= len(verse.text_uthmani.split())
    assert fill.word is None


async def test_root_and_meaning_options_come_from_the_corpus(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=11
    )

    root_question = questions[0]
    root_key = key[0]
    assert root_key["item_type"] == "root"
    stored_forms = (
        await db_session.execute(
            select(Word.text_uthmani).where(Word.root == "رحم")
        )
    ).scalars().all()
    assert root_question.word in stored_forms
    assert all(
        option.id == option.text for option in root_question.options
    )

    meaning_question = questions[1]
    assert meaning_question.word is not None
    assert all(option.id == option.text for option in meaning_question.options)


async def test_pos_options_use_readable_labels(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=3
    )
    pos_question = next(q for q in questions if q.type == "pos")
    pos_key = key[3]

    option_ids = {option.id for option in pos_question.options}
    assert pos_key["correct_option_id"] in option_ids
    assert all(option.text != option.id for option in pos_question.options)


async def test_every_question_has_exactly_one_correct_option_and_unique_options(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=31
    )

    for question, item in zip(questions, key, strict=True):
        option_ids = [option.id for option in question.options]
        option_texts = [option.text for option in question.options]
        assert len(option_ids) == len(set(option_ids)) == 4
        assert len(option_texts) == len(set(option_texts)) == 4
        assert option_ids.count(item["correct_option_id"]) == 1
        correct_text = next(
            option.text
            for option in question.options
            if option.id == item["correct_option_id"]
        )
        for option in question.options:
            if option.id != item["correct_option_id"]:
                assert option.text != correct_text


async def test_root_distractors_come_from_same_pos_words_of_similar_length(
    db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson = await _first_lesson(db_session)
    questions, key = await QuizService(db_session).build_lesson_questions(
        lesson, seed=44
    )

    for question, item in zip(questions, key, strict=True):
        if question.type != "root":
            continue
        anchor = (
            await db_session.execute(
                select(Word).where(Word.id == item["word_id"])
            )
        ).scalar_one()
        assert anchor.root is not None
        tolerance = max(2, len(anchor.root) // 2)
        for option in question.options:
            if option.id == item["correct_option_id"]:
                continue
            assert option.text != anchor.root
            assert abs(len(option.text) - len(anchor.root)) <= tolerance
            source = (
                await db_session.execute(
                    select(Word.id)
                    .where(
                        Word.pos_tag == anchor.pos_tag,
                        Word.root == option.text,
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
            assert source is not None


async def test_insufficient_distractors_returns_a_clear_409(
    db_session: AsyncSession, seed_quran_data: None
) -> None:
    await db_session.execute(
        delete(Word).where(Word.root.in_(["سمو", "اله"]))
    )
    await db_session.commit()
    lesson = await _first_lesson(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await QuizService(db_session).build_lesson_questions(lesson, seed=1)

    assert exc_info.value.status_code == 409
    assert "distractor" in str(exc_info.value.detail).lower()
