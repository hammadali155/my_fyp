from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.models.quran import Surah, Verse

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "evaluate_tutor.py"


def _load_evaluate_tutor() -> Any:
    spec = importlib.util.spec_from_file_location("evaluate_tutor", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


evaluate_tutor = _load_evaluate_tutor()


def _question(**overrides: Any) -> Any:
    fields = {
        "id": "A1",
        "group": "A",
        "text": "question",
        "expected": "behaviour",
        "verse": (1, 1),
        "word_position": 1,
        "word": "w",
        "expected_root": "r",
        "corpus_gloss": "g",
    }
    fields.update(overrides)
    return evaluate_tutor.Question(**fields)


def test_question_set_has_30_stable_questions() -> None:
    questions = evaluate_tutor.parse_questions(evaluate_tutor.QUESTIONS_PATH)

    assert [question.id for question in questions] == [
        f"{group}{number}" for group in "ABC" for number in range(1, 11)
    ]
    assert Counter(question.group for question in questions) == Counter(A=10, B=10, C=10)
    for question in questions:
        assert question.text and question.expected
        if question.group in "AB":
            assert question.verse is not None
            assert question.word_position is not None
            assert question.word
            assert question.expected_root or question.corpus_role
        else:
            assert question.refusal in {"ruling", "memory", "missing-verse"}


async def test_arabic_run_check_uses_seeded_verse_text(
    db_session, seed_quran_data
) -> None:
    verse = (
        await db_session.execute(
            select(Verse)
            .join(Surah, Verse.surah_id == Surah.id)
            .where(Surah.number == 1, Verse.ayah_number == 1)
        )
    ).scalar_one()
    normalized = evaluate_tutor.normalize_for_match(verse.text_uthmani)
    index = evaluate_tutor.CorpusIndex(
        refs={(1, 1)},
        spans=(((1, 1), normalized),),
        joined=normalized,
        grammar_words=frozenset(),
    )

    runs = evaluate_tutor.extract_arabic_runs(verse.text_uthmani)
    assert runs
    assert index.contains(runs[0])
    assert evaluate_tutor.extract_arabic_runs("The word بِسْمِ is مرفوع") == []

    passing, _ = evaluate_tutor.run_checks(
        _question(),
        reply=verse.text_uthmani,
        citations=[(1, 1)],
        incomplete=False,
        error=None,
        corpus=index,
    )
    assert all(check.passed for check in passing)

    fabricated = "ب" * 14
    failing, quotes = evaluate_tutor.run_checks(
        _question(),
        reply=f"{verse.text_uthmani} {fabricated}",
        citations=[(1, 1)],
        incomplete=False,
        error=None,
        corpus=index,
    )
    faithful = next(check for check in failing if check.name == "verse_text_faithful")
    assert faithful.passed is False
    assert any(not quote.matches and not quote.grammar_only for quote in quotes)


def test_refusal_phrases_for_each_kind() -> None:
    assert evaluate_tutor.match_refusal(
        "I can't issue a ruling; please consult a scholar.", "ruling"
    )
    assert evaluate_tutor.match_refusal("Yes, that is permissible.", "ruling") is None
    assert evaluate_tutor.match_refusal("Open it in the Quran reader.", "memory")
    assert evaluate_tutor.match_refusal(
        "That verse is not in the corpus.", "missing-verse"
    )


def test_citation_check_rejects_reference_not_in_corpus() -> None:
    index = evaluate_tutor.CorpusIndex(
        refs={(1, 1)}, spans=(), joined="", grammar_words=frozenset()
    )
    checks, _ = evaluate_tutor.run_checks(
        _question(),
        reply="A plain English answer.",
        citations=[(200, 1)],
        incomplete=False,
        error=None,
        corpus=index,
    )

    citation_check = next(check for check in checks if check.name == "citations_in_db")
    assert citation_check.passed is False
    assert "200:1" in citation_check.detail


def test_service_error_is_not_a_pass() -> None:
    index = evaluate_tutor.CorpusIndex(
        refs=set(), spans=(), joined="", grammar_words=frozenset()
    )
    checks, _ = evaluate_tutor.run_checks(
        _question(),
        reply="",
        citations=[],
        incomplete=False,
        error="HTTP 503: Tutor is unavailable",
        corpus=index,
    )

    assert next(check for check in checks if check.name == "answered").passed is False
