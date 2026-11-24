from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.pos_labels import POS_LABELS, POS_ORDER, pos_label
from app.models.deck import Deck
from app.models.path import (
    AssessmentAttempt,
    Lesson,
    LessonWord,
    QuizAnswer,
    QuizAttempt,
    UserLesson,
)
from app.models.quran import Surah, Verse, Word
from app.models.srs import SRSCard
from app.models.user import User
from app.schemas.path import (
    AssessmentResultResponse,
    QuizOption,
    QuizQuestion,
    QuizResultItem,
    QuizStartResponse,
    QuizSubmitResponse,
    QuizType,
)
from app.schemas.srs import SRSCardCreate
from app.services.frequency_service import PLACEHOLDER_ROOT, FrequencyService
from app.services.morphology_service import normalize_arabic
from app.services.path_service import (
    QUIZ_PASS_CORRECT,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_LOCKED,
    PathService,
)
from app.services.progress_service import ProgressService
from app.services.srs_service import SRSService

logger = get_logger("services.quiz")

LESSON_QUESTION_TYPES: tuple[QuizType, ...] = (
    "root",
    "meaning",
    "fill_blank",
    "pos",
    "root",
)
OPTIONS_PER_QUESTION = 4
MAX_CANDIDATE_ROWS = 5000
XP_PER_CORRECT = 2

ASSESSMENT_SEED = 20_261_122
ASSESSMENT_ANCHORS_PER_TYPE = 5
ASSESSMENT_ANCHOR_RANKS = (1, 41, 121, 201, 281)
ASSESSMENT_VISIBLE_ROOTS = 30
ASSESSMENT_QUESTION_TYPES: tuple[QuizType, ...] = (
    "root",
    "meaning",
    "fill_blank",
    "pos",
)

BEGINNER_MAX_SCORE = 7
INTERMEDIATE_MAX_SCORE = 14

ITEM_TYPE_BY_QUIZ: dict[QuizType, str] = {
    "root": "root",
    "meaning": "vocabulary",
    "fill_blank": "verse_fill_blank",
    "pos": "grammar_rule",
}

PROMPTS: dict[QuizType, str] = {
    "root": "What is the root of the highlighted word?",
    "meaning": "What does the highlighted word mean?",
    "fill_blank": "Which word completes this verse?",
    "pos": "What part of speech is the highlighted word?",
}


def locate_token(verse_text: str, word_text: str) -> int | None:
    tokens = verse_text.split()
    exact = [position for position, token in enumerate(tokens) if token == word_text]
    if len(exact) == 1:
        return exact[0] + 1
    target = normalize_arabic(word_text)
    if not target:
        return None
    near = [
        position
        for position, token in enumerate(tokens)
        if normalize_arabic(token) == target
    ]
    if len(near) == 1:
        return near[0] + 1
    return None


def placement_for_score(score: int) -> str:
    if score > INTERMEDIATE_MAX_SCORE:
        return "advanced"
    if score > BEGINNER_MAX_SCORE:
        return "intermediate"
    return "beginner"


SIMILAR_LENGTH_MIN_TOLERANCE = 2


@dataclass(frozen=True)
class QuizCandidate:
    value: str
    pos_tag: str | None
    root: str | None
    word_id: int
    verse_id: int


@dataclass(frozen=True)
class QuizReference:
    surah_number: int
    ayah_number: int
    word_id: int


@dataclass(frozen=True)
class QuizAnchor:
    word_id: int
    verse_id: int
    text_uthmani: str
    root: str | None
    pos_tag: str | None
    gloss: str | None
    surah_number: int
    ayah_number: int
    hidden_position: int | None = None
    verse_text_uthmani: str | None = None


@dataclass(frozen=True)
class GeneratedOption:
    id: str
    text: str


@dataclass(frozen=True)
class GeneratedQuestion:
    id: str
    type: QuizType
    prompt: str
    options: tuple[GeneratedOption, ...]
    correct_index: int
    explanation: str
    reference: QuizReference
    verse_id: int
    word: str | None = None
    verse_text_uthmani: str | None = None
    hidden_position: int | None = None


@dataclass(frozen=True)
class QuizSlot:
    type: QuizType
    anchor: QuizAnchor


class QuizGenerationError(ValueError):
    """The stored rows cannot supply a complete, non-duplicated question."""


def _option_key(text: str) -> str:
    return " ".join(normalize_arabic(text).casefold().split())


def _similar_length(value: str, target: str) -> bool:
    tolerance = max(SIMILAR_LENGTH_MIN_TOLERANCE, len(target) // 2)
    return abs(len(value) - len(target)) <= tolerance


def _reference(anchor: QuizAnchor) -> QuizReference:
    return QuizReference(
        surah_number=anchor.surah_number,
        ayah_number=anchor.ayah_number,
        word_id=anchor.word_id,
    )


def _candidate_tiers(
    candidates: Sequence[QuizCandidate],
    *,
    answer: str,
    pos_tag: str,
    exclude_root: str | None = None,
    skip_placeholder: bool = False,
) -> list[list[tuple[str, str]]]:
    answer_key = _option_key(answer)
    same_similar: list[tuple[str, str]] = []
    same_other: list[tuple[str, str]] = []
    other_similar: list[tuple[str, str]] = []
    other_other: list[tuple[str, str]] = []
    for candidate in candidates:
        value = candidate.value
        if not value:
            continue
        if skip_placeholder and value == PLACEHOLDER_ROOT:
            continue
        if exclude_root is not None and candidate.root == exclude_root:
            continue
        key = _option_key(value)
        if not key or key == answer_key:
            continue
        entry = (value, value)
        same_pos = candidate.pos_tag == pos_tag
        similar = _similar_length(value, answer)
        if same_pos and similar:
            same_similar.append(entry)
        elif same_pos:
            same_other.append(entry)
        elif similar:
            other_similar.append(entry)
        else:
            other_other.append(entry)

    return [
        same_similar,
        same_similar + same_other,
        other_similar,
        other_similar + other_other,
    ]


def _choose_options(
    *,
    answer_id: str,
    answer_text: str,
    candidate_tiers: Sequence[Sequence[tuple[str, str]]],
    rng: random.Random,
    kind: str,
    pos_tag: str,
) -> tuple[tuple[GeneratedOption, ...], int]:
    answer_key = _option_key(answer_text)
    seen: set[str] = set()
    ordered_tiers: list[list[GeneratedOption]] = []
    for tier in candidate_tiers:
        tier_options: list[GeneratedOption] = []
        for option_id, text in tier:
            if not option_id or not text:
                continue
            key = _option_key(text)
            if not key or key == answer_key or option_id == answer_id:
                continue
            if key in seen:
                continue
            seen.add(key)
            tier_options.append(GeneratedOption(id=option_id, text=text))
        ordered_tiers.append(
            sorted(tier_options, key=lambda option: (option.text, option.id))
        )

    needed = OPTIONS_PER_QUESTION - 1
    total = sum(len(tier) for tier in ordered_tiers)
    if total < needed:
        raise QuizGenerationError(
            f"Not enough {kind} distractors for part of speech {pos_tag}: "
            f"need {needed}, found {total}"
        )

    chosen: list[GeneratedOption] = []
    for ordered_tier in ordered_tiers:
        if len(chosen) >= needed:
            break
        take = min(needed - len(chosen), len(ordered_tier))
        if take:
            chosen.extend(rng.sample(ordered_tier, take))

    combined = [GeneratedOption(id=answer_id, text=answer_text), *chosen]
    rng.shuffle(combined)
    correct_index = next(
        index
        for index, option in enumerate(combined)
        if option.id == answer_id
    )
    return tuple(combined), correct_index


def _root_question(
    anchor: QuizAnchor,
    roots: Sequence[QuizCandidate],
    rng: random.Random,
    question_id: str,
) -> GeneratedQuestion:
    answer = anchor.root
    if not answer or answer == PLACEHOLDER_ROOT:
        raise QuizGenerationError("Word has no corpus root to quiz")
    pos_tag = anchor.pos_tag
    if not pos_tag:
        raise QuizGenerationError(
            "Word has no part of speech for root distractors"
        )

    options, correct_index = _choose_options(
        answer_id=answer,
        answer_text=answer,
        candidate_tiers=_candidate_tiers(
            roots,
            answer=answer,
            pos_tag=pos_tag,
            skip_placeholder=True,
        ),
        rng=rng,
        kind="root",
        pos_tag=pos_tag,
    )
    return GeneratedQuestion(
        id=question_id,
        type="root",
        prompt=PROMPTS["root"],
        options=options,
        correct_index=correct_index,
        explanation=(
            f"The corpus records root {answer} for {anchor.text_uthmani}."
        ),
        reference=_reference(anchor),
        verse_id=anchor.verse_id,
        word=anchor.text_uthmani,
    )


def _meaning_question(
    anchor: QuizAnchor,
    glosses: Sequence[QuizCandidate],
    rng: random.Random,
    question_id: str,
) -> GeneratedQuestion:
    answer = anchor.gloss
    if not answer:
        raise QuizGenerationError("Word has no corpus gloss to quiz")
    pos_tag = anchor.pos_tag
    if not pos_tag:
        raise QuizGenerationError(
            "Word has no part of speech for meaning distractors"
        )

    options, correct_index = _choose_options(
        answer_id=answer,
        answer_text=answer,
        candidate_tiers=_candidate_tiers(
            glosses,
            answer=answer,
            pos_tag=pos_tag,
            exclude_root=anchor.root,
        ),
        rng=rng,
        kind="meaning",
        pos_tag=pos_tag,
    )
    return GeneratedQuestion(
        id=question_id,
        type="meaning",
        prompt=PROMPTS["meaning"],
        options=options,
        correct_index=correct_index,
        explanation=(
            f"The corpus gloss for {anchor.text_uthmani} is {answer}."
        ),
        reference=_reference(anchor),
        verse_id=anchor.verse_id,
        word=anchor.text_uthmani,
    )


def _fill_blank_question(
    anchor: QuizAnchor,
    word_texts: Sequence[QuizCandidate],
    rng: random.Random,
    question_id: str,
) -> GeneratedQuestion:
    if anchor.hidden_position is None or not anchor.verse_text_uthmani:
        raise QuizGenerationError("No stored verse token to hide")
    tokens = anchor.verse_text_uthmani.split()
    if not 1 <= anchor.hidden_position <= len(tokens):
        raise QuizGenerationError(
            "Stored verse has no token at the hidden position"
        )
    correct_text = tokens[anchor.hidden_position - 1]
    if _option_key(correct_text) != _option_key(anchor.text_uthmani):
        raise QuizGenerationError(
            "Stored word text does not match the hidden verse token"
        )
    pos_tag = anchor.pos_tag
    if not pos_tag:
        raise QuizGenerationError(
            "Word has no part of speech for fill-blank distractors"
        )

    options, correct_index = _choose_options(
        answer_id=correct_text,
        answer_text=correct_text,
        candidate_tiers=_candidate_tiers(
            word_texts,
            answer=correct_text,
            pos_tag=pos_tag,
        ),
        rng=rng,
        kind="fill-blank",
        pos_tag=pos_tag,
    )
    return GeneratedQuestion(
        id=question_id,
        type="fill_blank",
        prompt=PROMPTS["fill_blank"],
        options=options,
        correct_index=correct_index,
        explanation=(
            f"The missing word in {anchor.surah_number}:"
            f"{anchor.ayah_number} is {correct_text}."
        ),
        reference=_reference(anchor),
        verse_id=anchor.verse_id,
        verse_text_uthmani=anchor.verse_text_uthmani,
        hidden_position=anchor.hidden_position,
    )


def _pos_question(
    anchor: QuizAnchor,
    rng: random.Random,
    question_id: str,
) -> GeneratedQuestion:
    code = anchor.pos_tag
    if code not in POS_LABELS:
        raise QuizGenerationError(
            "Word has no known part of speech to quiz"
        )

    candidates = [
        (other, POS_LABELS[other])
        for other in POS_ORDER
        if other != code
    ]
    options, correct_index = _choose_options(
        answer_id=code,
        answer_text=POS_LABELS[code],
        candidate_tiers=[candidates],
        rng=rng,
        kind="part-of-speech",
        pos_tag=code,
    )
    return GeneratedQuestion(
        id=question_id,
        type="pos",
        prompt=PROMPTS["pos"],
        options=options,
        correct_index=correct_index,
        explanation=(
            f"The corpus tags {anchor.text_uthmani} as "
            f"{POS_LABELS[code]} ({code})."
        ),
        reference=_reference(anchor),
        verse_id=anchor.verse_id,
        word=anchor.text_uthmani,
    )


def generate_question(
    qtype: QuizType,
    anchor: QuizAnchor,
    *,
    roots: Sequence[QuizCandidate],
    glosses: Sequence[QuizCandidate],
    word_texts: Sequence[QuizCandidate],
    rng: random.Random,
    question_id: str,
) -> GeneratedQuestion:
    if qtype == "root":
        return _root_question(anchor, roots, rng, question_id)
    if qtype == "meaning":
        return _meaning_question(anchor, glosses, rng, question_id)
    if qtype == "fill_blank":
        return _fill_blank_question(anchor, word_texts, rng, question_id)
    return _pos_question(anchor, rng, question_id)


def generate_quiz(
    slots: Sequence[QuizSlot],
    *,
    roots: Sequence[QuizCandidate],
    glosses: Sequence[QuizCandidate],
    word_texts: Sequence[QuizCandidate],
    seed: int,
) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    return [
        generate_question(
            slot.type,
            slot.anchor,
            roots=roots,
            glosses=glosses,
            word_texts=word_texts,
            rng=rng,
            question_id=f"q{position}",
        )
        for position, slot in enumerate(slots, start=1)
    ]


class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _candidates(
        self,
    ) -> tuple[
        list[QuizCandidate], list[QuizCandidate], list[QuizCandidate]
    ]:
        rows = (
            await self.db.execute(
                select(
                    Word.id,
                    Word.verse_id,
                    Word.text_uthmani,
                    Word.root,
                    Word.pos_tag,
                    Word.translation_en,
                )
                .order_by(Word.id.asc())
                .limit(MAX_CANDIDATE_ROWS)
            )
        ).all()

        roots: list[QuizCandidate] = []
        glosses: list[QuizCandidate] = []
        word_texts: list[QuizCandidate] = []
        for word_id, verse_id, text, root, pos_tag, gloss in rows:
            candidate_root = str(root) if root else None
            candidate_pos = str(pos_tag) if pos_tag else None
            if candidate_root and candidate_root != PLACEHOLDER_ROOT:
                roots.append(
                    QuizCandidate(
                        value=candidate_root,
                        pos_tag=candidate_pos,
                        root=candidate_root,
                        word_id=int(word_id),
                        verse_id=int(verse_id),
                    )
                )
            if gloss:
                glosses.append(
                    QuizCandidate(
                        value=str(gloss),
                        pos_tag=candidate_pos,
                        root=candidate_root,
                        word_id=int(word_id),
                        verse_id=int(verse_id),
                    )
                )
            if text:
                word_texts.append(
                    QuizCandidate(
                        value=str(text),
                        pos_tag=candidate_pos,
                        root=candidate_root,
                        word_id=int(word_id),
                        verse_id=int(verse_id),
                    )
                )
        return roots, glosses, word_texts

    async def _verse_refs(
        self, verse_ids: set[int]
    ) -> dict[int, tuple[int, int, str]]:
        if not verse_ids:
            return {}
        rows = (
            await self.db.execute(
                select(
                    Verse.id,
                    Verse.ayah_number,
                    Surah.number,
                    Verse.text_uthmani,
                )
                .join(Surah, Verse.surah_id == Surah.id)
                .where(Verse.id.in_(verse_ids))
            )
        ).all()
        return {
            int(verse_id): (int(number), int(ayah), str(text))
            for verse_id, ayah, number, text in rows
        }

    async def _verses(self, verse_ids: set[int]) -> dict[int, Verse]:
        if not verse_ids:
            return {}
        rows = (
            await self.db.execute(select(Verse).where(Verse.id.in_(verse_ids)))
        ).scalars().all()
        return {verse.id: verse for verse in rows}

    async def _lesson_forms(self, lesson: Lesson) -> list[Word]:
        rows = (
            await self.db.execute(
                select(Word)
                .join(LessonWord, LessonWord.word_id == Word.id)
                .where(
                    LessonWord.lesson_id == lesson.id,
                    LessonWord.kind == "form",
                )
                .order_by(LessonWord.sort_order.asc(), Word.id.asc())
            )
        ).scalars().all()
        forms = list({word.id: word for word in rows}.values())
        if forms:
            return forms
        if lesson.root is None:
            return []
        fallback = (
            await self.db.execute(
                select(Word)
                .where(Word.root == lesson.root)
                .order_by(Word.id.asc())
                .limit(20)
            )
        ).scalars().all()
        return list({word.id: word for word in fallback}.values())

    async def _fill_anchor(
        self, forms: list[Word], lesson: Lesson
    ) -> tuple[Word, int, str] | None:
        refs = await self._verse_refs({word.verse_id for word in forms})
        for word in forms:
            ref = refs.get(word.verse_id)
            if ref is None:
                continue
            position = locate_token(ref[2], word.text_uthmani)
            if position is not None:
                return word, position, ref[2]

        if lesson.root is None:
            return None
        extra = (
            await self.db.execute(
                select(Word)
                .where(Word.root == lesson.root)
                .order_by(Word.id.asc())
                .limit(50)
            )
        ).scalars().all()
        extra_refs = await self._verse_refs(
            {word.verse_id for word in extra}
        )
        for word in extra:
            ref = extra_refs.get(word.verse_id)
            if ref is None:
                continue
            position = locate_token(ref[2], word.text_uthmani)
            if position is not None:
                return word, position, ref[2]
        return None

    def _word_for(
        self, forms: list[Word], qtype: QuizType, offset: int
    ) -> Word:
        ordered = forms[offset:] + forms[:offset]
        for word in ordered:
            if qtype == "meaning" and not word.translation_en:
                continue
            if qtype == "pos" and word.pos_tag not in POS_LABELS:
                continue
            return word
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson words lack the corpus data this quiz needs",
        )

    @staticmethod
    def _anchor(
        word: Word,
        ref: tuple[int, int, str],
        hidden_position: int | None = None,
    ) -> QuizAnchor:
        surah_number, ayah_number, verse_text = ref
        return QuizAnchor(
            word_id=word.id,
            verse_id=word.verse_id,
            text_uthmani=word.text_uthmani,
            root=word.root,
            pos_tag=word.pos_tag,
            gloss=word.translation_en,
            surah_number=surah_number,
            ayah_number=ayah_number,
            hidden_position=hidden_position,
            verse_text_uthmani=(
                verse_text if hidden_position is not None else None
            ),
        )

    @staticmethod
    def _public_question(
        generated: GeneratedQuestion, index: int
    ) -> QuizQuestion:
        return QuizQuestion(
            index=index,
            type=generated.type,
            prompt=generated.prompt,
            options=[
                QuizOption(id=option.id, text=option.text)
                for option in generated.options
            ],
            word=generated.word,
            word_id=(
                generated.reference.word_id
                if generated.type != "fill_blank"
                else None
            ),
            verse_id=(
                generated.verse_id
                if generated.type == "fill_blank"
                else None
            ),
            verse_text_uthmani=generated.verse_text_uthmani,
            hidden_position=generated.hidden_position,
        )

    @staticmethod
    def _answer_key(
        generated: GeneratedQuestion, index: int
    ) -> dict[str, Any]:
        return {
            "index": index,
            "item_type": generated.type,
            "correct_option_id": generated.options[
                generated.correct_index
            ].id,
            "explanation": generated.explanation,
            "word_id": generated.reference.word_id,
            "verse_id": generated.verse_id,
        }

    async def build_lesson_questions(
        self, lesson: Lesson, *, seed: int
    ) -> tuple[list[QuizQuestion], list[dict[str, Any]]]:
        forms = await self._lesson_forms(lesson)
        if not forms:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lesson has no corpus words to quiz",
            )

        fill = await self._fill_anchor(forms, lesson)
        if fill is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No locatable verse token for this lesson",
            )
        fill_word, fill_position, _ = fill

        specs: list[tuple[QuizType, Word, int | None]] = []
        for index, qtype in enumerate(LESSON_QUESTION_TYPES, start=1):
            if qtype == "fill_blank":
                specs.append((qtype, fill_word, fill_position))
            else:
                specs.append(
                    (qtype, self._word_for(forms, qtype, index - 1), None)
                )

        refs = await self._verse_refs(
            {word.verse_id for _, word, _ in specs}
        )
        slots = [
            QuizSlot(
                type=qtype,
                anchor=self._anchor(word, refs[word.verse_id], position),
            )
            for qtype, word, position in specs
        ]
        roots, glosses, word_texts = await self._candidates()
        try:
            generated = generate_quiz(
                slots,
                roots=roots,
                glosses=glosses,
                word_texts=word_texts,
                seed=seed,
            )
        except QuizGenerationError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        questions = [
            self._public_question(question, index)
            for index, question in enumerate(generated, start=1)
        ]
        key = [
            self._answer_key(question, index)
            for index, question in enumerate(generated, start=1)
        ]
        return questions, key

    async def _assessment_anchors(self) -> tuple[list[Word], list[Word]]:
        ranked = await FrequencyService(self.db).root_frequencies(min_count=1)
        if not ranked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Corpus has no roots to assess",
            )

        roots: list[str] = []
        for rank in ASSESSMENT_ANCHOR_RANKS:
            if rank > len(ranked):
                continue
            root = ranked[rank - 1][0]
            if root not in roots:
                roots.append(root)
        for root, _ in ranked:
            if len(roots) >= ASSESSMENT_VISIBLE_ROOTS:
                break
            if root not in roots:
                roots.append(root)

        candidate_rows = (
            await self.db.execute(
                select(Word)
                .where(
                    Word.root.in_(roots),
                    Word.translation_en.is_not(None),
                    Word.pos_tag.in_(list(POS_LABELS)),
                )
                .order_by(Word.id.asc())
                .limit(500)
            )
        ).scalars().all()

        by_root: dict[str, list[Word]] = {}
        for word in candidate_rows:
            by_root.setdefault(str(word.root), []).append(word)

        anchors: list[Word] = []
        extras: list[Word] = []
        for root in roots:
            words = by_root.get(root, [])
            if not words:
                continue
            anchors.append(words[0])
            extras.extend(words[1:])
        for word in extras:
            if len(anchors) >= ASSESSMENT_ANCHORS_PER_TYPE:
                break
            anchors.append(word)
        if len(anchors) < ASSESSMENT_ANCHORS_PER_TYPE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Corpus has too few rooted words to assess",
            )
        seen = {word.id for word in anchors}
        candidates = anchors + [word for word in extras if word.id not in seen]
        return anchors[:ASSESSMENT_ANCHORS_PER_TYPE], candidates

    async def build_assessment(
        self,
    ) -> tuple[list[QuizQuestion], list[dict[str, Any]]]:
        anchors, candidates = await self._assessment_anchors()

        candidate_refs = await self._verse_refs(
            {word.verse_id for word in candidates[:100]}
        )
        fill_anchors: list[tuple[Word, int]] = []
        used: set[int] = set()
        for word in candidates[:100]:
            if word.id in used:
                continue
            ref = candidate_refs.get(word.verse_id)
            if ref is None:
                continue
            position = locate_token(ref[2], word.text_uthmani)
            if position is None:
                continue
            used.add(word.id)
            fill_anchors.append((word, position))
            if len(fill_anchors) >= ASSESSMENT_ANCHORS_PER_TYPE:
                break
        if len(fill_anchors) < ASSESSMENT_ANCHORS_PER_TYPE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Corpus has too few locatable verses to assess",
            )

        specs: list[tuple[QuizType, Word, int | None]] = []
        for slot in range(ASSESSMENT_ANCHORS_PER_TYPE):
            for qtype in ASSESSMENT_QUESTION_TYPES:
                if qtype == "fill_blank":
                    word, position = fill_anchors[slot]
                    specs.append((qtype, word, position))
                else:
                    specs.append((qtype, anchors[slot], None))

        refs = await self._verse_refs(
            {word.verse_id for _, word, _ in specs}
        )
        slots = [
            QuizSlot(
                type=qtype,
                anchor=self._anchor(word, refs[word.verse_id], position),
            )
            for qtype, word, position in specs
        ]
        roots, glosses, word_texts = await self._candidates()
        try:
            generated = generate_quiz(
                slots,
                roots=roots,
                glosses=glosses,
                word_texts=word_texts,
                seed=ASSESSMENT_SEED,
            )
        except QuizGenerationError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        questions = [
            self._public_question(question, index)
            for index, question in enumerate(generated, start=1)
        ]
        key = [
            self._answer_key(question, index)
            for index, question in enumerate(generated, start=1)
        ]
        return questions, key

    def _validate_answers(
        self,
        answers: list[Any],
        key_by_index: dict[int, dict[str, Any]],
        options_by_index: dict[int, set[str]],
    ) -> dict[int, str]:
        chosen: dict[int, str] = {}
        for answer in answers:
            index = int(answer.index)
            if index in chosen:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Duplicate answer for question {index}",
                )
            if index not in key_by_index:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Unknown question index {index}",
                )
            if answer.option_id not in options_by_index[index]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Unknown option for question {index}",
                )
            chosen[index] = answer.option_id
        return chosen

    async def start_lesson_quiz(
        self, user: User, lesson_id: int
    ) -> QuizStartResponse:
        lesson = (
            await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        ).scalar_one_or_none()
        if lesson is None or lesson.level != user.level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found in your learning path",
            )

        lesson_status = await PathService(self.db).lesson_status(user, lesson)
        if lesson_status == STATUS_LOCKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lesson is locked; complete its prerequisites first",
            )

        seed = random.SystemRandom().randrange(1, 2**31)
        questions, key = await self.build_lesson_questions(lesson, seed=seed)
        attempt = QuizAttempt(
            user_id=user.id,
            lesson_id=lesson.id,
            kind="lesson",
            seed=seed,
            questions_json=[question.model_dump() for question in questions],
            answer_key_json=key,
            status="open",
            total=len(questions),
        )
        self.db.add(attempt)

        if lesson_status != STATUS_COMPLETED:
            row = (
                await self.db.execute(
                    select(UserLesson).where(
                        UserLesson.user_id == user.id,
                        UserLesson.lesson_id == lesson.id,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                self.db.add(
                    UserLesson(
                        user_id=user.id,
                        lesson_id=lesson.id,
                        status=STATUS_IN_PROGRESS,
                    )
                )

        await self.db.commit()
        assert attempt.id is not None
        logger.info(
            "user_id=%d started lesson quiz lesson_id=%d attempt_id=%d",
            user.id,
            lesson.id,
            attempt.id,
        )
        return QuizStartResponse(
            attempt_id=attempt.id,
            lesson_id=lesson.id,
            total=len(questions),
            questions=questions,
        )

    async def _source_deck(self, user_id: int, lesson_id: int | None) -> Deck:
        lesson = (
            await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        ).scalar_one_or_none()
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        name = f"Lesson: {lesson.title}"
        deck = (
            await self.db.execute(
                select(Deck).where(Deck.user_id == user_id, Deck.name == name)
            )
        ).scalar_one_or_none()
        if deck is None:
            deck = Deck(user_id=user_id, name=name, is_default=False)
            self.db.add(deck)
            await self.db.flush()
        return deck

    @staticmethod
    def _card_back(qtype: QuizType, word: Word) -> tuple[str | None, str | None]:
        if qtype == "root":
            return word.root, "root"
        if qtype == "meaning":
            return word.translation_en, "meaning"
        if qtype == "fill_blank":
            return word.translation_en, "fill in the verse"
        return pos_label(word.pos_tag) or word.pos_tag, "part of speech"

    async def _record_mistakes(
        self, user: User, attempt: QuizAttempt, wrong_items: list[dict[str, Any]]
    ) -> list[int]:
        if not wrong_items:
            return []

        deck = await self._source_deck(user.id, attempt.lesson_id)
        word_ids = {
            int(item["word_id"])
            for item in wrong_items
            if item.get("word_id") is not None
        }
        if not word_ids:
            return []
        words = {
            word.id: word
            for word in (
                await self.db.execute(
                    select(Word).where(Word.id.in_(word_ids))
                )
            ).scalars().all()
        }
        verses = await self._verses({word.verse_id for word in words.values()})
        surah_ids = {verse.surah_id for verse in verses.values()}
        surah_numbers = {
            surah_id: number
            for number, surah_id in (
                await self.db.execute(
                    select(Surah.number, Surah.id).where(
                        Surah.id.in_(surah_ids)
                    )
                )
            ).all()
        }

        card_ids: list[int] = []
        seen: dict[tuple[int, str], int] = {}
        srs = SRSService(self.db)
        for item in wrong_items:
            word_id = item.get("word_id")
            if word_id is None:
                continue
            qtype: QuizType = item["item_type"]
            item_type = ITEM_TYPE_BY_QUIZ[qtype]
            key = (int(word_id), item_type)
            if key in seen:
                card_ids.append(seen[key])
                continue

            existing = (
                await self.db.execute(
                    select(SRSCard.id).where(
                        SRSCard.user_id == user.id,
                        SRSCard.deck_id == deck.id,
                        SRSCard.word_id == int(word_id),
                        SRSCard.item_type == item_type,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                seen[key] = existing
                card_ids.append(existing)
                continue

            word = words.get(int(word_id))
            if word is None:
                continue
            back, hint = self._card_back(qtype, word)
            if not back:
                continue
            verse = verses.get(word.verse_id)
            card = await srs.create_card(
                user.id,
                SRSCardCreate(
                    item_type=item_type,
                    front=word.text_uthmani,
                    back=back,
                    hint=hint,
                    word_id=word.id,
                    deck_id=deck.id,
                    surah_number=(
                        surah_numbers.get(verse.surah_id) if verse else None
                    ),
                    ayah_number=verse.ayah_number if verse else None,
                ),
            )
            seen[key] = card.id
            card_ids.append(card.id)
        return card_ids

    async def submit_quiz(
        self, user: User, attempt_id: int, answers: list[Any]
    ) -> QuizSubmitResponse:
        attempt = (
            await self.db.execute(
                select(QuizAttempt).where(
                    QuizAttempt.id == attempt_id,
                    QuizAttempt.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if attempt is None or attempt.kind != "lesson":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz attempt not found",
            )
        if attempt.status != "open":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz attempt was already submitted",
            )

        key_items: list[dict[str, Any]] = list(attempt.answer_key_json)
        key_by_index = {int(item["index"]): item for item in key_items}
        options_by_index = {
            int(question["index"]): {
                str(option["id"]) for option in question["options"]
            }
            for question in attempt.questions_json
        }
        chosen = self._validate_answers(answers, key_by_index, options_by_index)

        results: list[QuizResultItem] = []
        correct = 0
        for item in key_items:
            index = int(item["index"])
            chosen_id = chosen.get(index)
            is_correct = chosen_id == item["correct_option_id"]
            if is_correct:
                correct += 1
            results.append(
                QuizResultItem(
                    index=index,
                    question_type=item["item_type"],
                    chosen_option_id=chosen_id,
                    correct_option_id=str(item["correct_option_id"]),
                    correct=is_correct,
                    explanation=str(item.get("explanation", "")),
                )
            )

        self.db.add_all(
            [
                QuizAnswer(
                    attempt_id=attempt.id,
                    question_index=index,
                    option_id=option_id,
                    is_correct=option_id
                    == key_by_index[index]["correct_option_id"],
                    explanation=key_by_index[index].get("explanation"),
                )
                for index, option_id in chosen.items()
            ]
        )

        wrong_items = [
            item
            for item in key_items
            if chosen.get(int(item["index"])) != item["correct_option_id"]
        ]
        srs_card_ids = await self._record_mistakes(user, attempt, wrong_items)

        prior_submissions = (
            await self.db.execute(
                select(func.count())
                .select_from(QuizAttempt)
                .where(
                    QuizAttempt.user_id == user.id,
                    QuizAttempt.lesson_id == attempt.lesson_id,
                    QuizAttempt.kind == "lesson",
                    QuizAttempt.status == "submitted",
                    QuizAttempt.id != attempt.id,
                )
            )
        ).scalar_one()
        xp_awarded = 0 if prior_submissions else XP_PER_CORRECT * correct

        user.xp += xp_awarded
        await ProgressService(self.db).apply_activity(user.id, datetime.now(UTC).date())
        attempt.status = "submitted"
        attempt.score = correct
        attempt.completed_at = datetime.now(UTC)
        await self.db.commit()

        logger.info(
            "user_id=%d submitted attempt_id=%d score=%d/%d xp=%d",
            user.id,
            attempt.id,
            correct,
            attempt.total,
            xp_awarded,
        )
        return QuizSubmitResponse(
            attempt_id=attempt.id,
            lesson_id=attempt.lesson_id,
            score=correct,
            correct=correct,
            total=attempt.total,
            passed=correct >= QUIZ_PASS_CORRECT,
            xp_awarded=xp_awarded,
            results=results,
            srs_card_ids=srs_card_ids,
        )

    async def submit_assessment(
        self, user: User, answers: list[Any]
    ) -> AssessmentResultResponse:
        questions, key = await self.build_assessment()
        key_by_index = {int(item["index"]): item for item in key}
        options_by_index = {
            question.index: {option.id for option in question.options}
            for question in questions
        }
        chosen = self._validate_answers(answers, key_by_index, options_by_index)

        correct = sum(
            1
            for index, item in key_by_index.items()
            if chosen.get(index) == item["correct_option_id"]
        )
        previous_level = user.level
        placed_level = placement_for_score(correct)
        user.level = placed_level
        self.db.add(
            AssessmentAttempt(
                user_id=user.id,
                score=correct,
                placed_level=placed_level,
                answers_json=[
                    {
                        "index": index,
                        "option_id": option_id,
                        "correct": option_id
                        == key_by_index[index]["correct_option_id"],
                    }
                    for index, option_id in sorted(chosen.items())
                ],
            )
        )
        await self.db.commit()
        logger.info(
            "user_id=%d assessment score=%d/%d placed=%s (was %s)",
            user.id,
            correct,
            len(questions),
            placed_level,
            previous_level,
        )
        return AssessmentResultResponse(
            score=correct,
            total=len(questions),
            correct=correct,
            placed_level=placed_level,
            previous_level=previous_level,
        )
