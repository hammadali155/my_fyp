from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.path import (
    Lesson,
    LessonPrerequisite,
    LessonWord,
    QuizAnswer,
    QuizAttempt,
    UserLesson,
)
from app.models.quran import Word
from app.models.srs import SRSCard
from app.models.user import User
from app.schemas.path import (
    LessonCard,
    LessonCompleteResponse,
    LessonDetailResponse,
    LessonListResponse,
    LessonStatus,
    ModuleProgress,
    PathCounts,
    PathNextItem,
    PathPlanResponse,
    PathProgressCounts,
    PathProgressResponse,
    RecentQuiz,
)
from app.services.frequency_service import PLACEHOLDER_ROOT
from app.services.progress_service import ProgressService
from app.services.srs_service import SRSService

logger = get_logger("services.path")

LESSON_COMPLETE_XP = 20
QUIZ_PASS_CORRECT = 4

STATUS_COMPLETED: LessonStatus = "completed"
STATUS_IN_PROGRESS: LessonStatus = "in_progress"
STATUS_AVAILABLE: LessonStatus = "available"
STATUS_LOCKED: LessonStatus = "locked"

UNLOCKED = (STATUS_AVAILABLE, STATUS_IN_PROGRESS)


class PathService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _band_lessons(self, level: str) -> list[Lesson]:
        rows = (
            await self.db.execute(
                select(Lesson)
                .where(Lesson.level == level)
                .order_by(Lesson.sequence.asc(), Lesson.id.asc())
            )
        ).scalars().all()
        return list(rows)

    async def _user_lessons(self, user_id: int) -> dict[int, UserLesson]:
        rows = (
            await self.db.execute(
                select(UserLesson).where(UserLesson.user_id == user_id)
            )
        ).scalars().all()
        return {row.lesson_id: row for row in rows}

    async def _prerequisites(self, lesson_ids: list[int]) -> dict[int, list[int]]:
        if not lesson_ids:
            return {}
        rows = (
            await self.db.execute(
                select(
                    LessonPrerequisite.lesson_id,
                    LessonPrerequisite.requires_lesson_id,
                ).where(LessonPrerequisite.lesson_id.in_(lesson_ids))
            )
        ).all()
        out: dict[int, list[int]] = defaultdict(list)
        for lesson_id, requires_id in rows:
            out[lesson_id].append(requires_id)
        return out

    async def _statuses(
        self, lessons: list[Lesson], user_id: int
    ) -> tuple[dict[int, LessonStatus], dict[int, UserLesson]]:
        user_lessons = await self._user_lessons(user_id)
        completed = {
            lesson_id
            for lesson_id, row in user_lessons.items()
            if row.status == STATUS_COMPLETED
        }
        prerequisites = await self._prerequisites([lesson.id for lesson in lessons])

        statuses: dict[int, LessonStatus] = {}
        for lesson in lessons:
            row = user_lessons.get(lesson.id)
            if lesson.id in completed:
                statuses[lesson.id] = STATUS_COMPLETED
                continue
            requires = prerequisites.get(lesson.id, [])
            if all(required in completed for required in requires):
                statuses[lesson.id] = (
                    STATUS_IN_PROGRESS
                    if row is not None and row.status == STATUS_IN_PROGRESS
                    else STATUS_AVAILABLE
                )
            else:
                statuses[lesson.id] = STATUS_LOCKED
        return statuses, user_lessons

    async def _correct_word_ids(self, user_id: int) -> set[int]:
        rows = (
            await self.db.execute(
                select(QuizAnswer.question_index, QuizAttempt.answer_key_json)
                .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
                .where(
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.kind == "lesson",
                    QuizAttempt.status == "submitted",
                    QuizAnswer.is_correct.is_(True),
                )
            )
        ).all()
        word_ids: set[int] = set()
        for index, key in rows:
            for item in key:
                if int(item.get("index", -1)) != int(index):
                    continue
                word_id = item.get("word_id")
                if word_id is not None:
                    word_ids.add(int(word_id))
        return word_ids

    async def _studied_word_ids(self, user_id: int) -> set[int]:
        rows = (
            await self.db.execute(
                select(SRSCard.word_id).where(
                    SRSCard.user_id == user_id,
                    SRSCard.word_id.is_not(None),
                )
            )
        ).scalars().all()
        return {int(word_id) for word_id in rows if word_id is not None}

    async def _next_items(
        self, user: User, cards: list[LessonCard]
    ) -> list[PathNextItem]:
        candidates = [card for card in cards if card.status in UNLOCKED]
        if not candidates:
            return []
        excluded = await self._correct_word_ids(user.id)
        excluded.update(await self._studied_word_ids(user.id))
        rows = (
            await self.db.execute(
                select(Lesson, LessonWord, Word)
                .join(Lesson, LessonWord.lesson_id == Lesson.id)
                .join(Word, LessonWord.word_id == Word.id)
                .where(
                    Lesson.id.in_([card.id for card in candidates]),
                    Lesson.level == user.level,
                )
                .order_by(
                    Lesson.sequence.asc(),
                    Lesson.id.asc(),
                    LessonWord.sort_order.asc(),
                    Word.id.asc(),
                )
            )
        ).all()
        return [
            PathNextItem(
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                word_id=word.id,
                text_uthmani=word.text_uthmani,
                root=word.root,
                kind=link.kind,
            )
            for lesson, link, word in rows
            if word.id not in excluded
        ]

    async def _learned_counts(self, word_ids: set[int]) -> tuple[int, int]:
        if not word_ids:
            return 0, 0
        roots = (
            await self.db.execute(
                select(Word.root).where(
                    Word.id.in_(word_ids),
                    Word.root.is_not(None),
                    Word.root != PLACEHOLDER_ROOT,
                )
            )
        ).scalars().all()
        return len(word_ids), len(set(roots))

    @staticmethod
    def _card(
        lesson: Lesson,
        status_value: LessonStatus,
        user_lessons: dict[int, UserLesson],
    ) -> LessonCard:
        row = user_lessons.get(lesson.id)
        return LessonCard(
            id=lesson.id,
            title=lesson.title,
            module=lesson.module,
            level=lesson.level,
            sequence=lesson.sequence,
            root=lesson.root,
            status=status_value,
            score=row.score if row is not None else None,
            est_minutes=lesson.est_minutes,
        )

    async def get_plan(self, user: User) -> PathPlanResponse:
        lessons = await self._band_lessons(user.level)
        statuses, user_lessons = await self._statuses(lessons, user.id)
        cards = [
            self._card(lesson, statuses[lesson.id], user_lessons)
            for lesson in lessons
        ]
        counts = PathCounts(
            total=len(cards),
            completed=sum(1 for card in cards if card.status == STATUS_COMPLETED),
            available=sum(1 for card in cards if card.status in UNLOCKED),
            locked=sum(1 for card in cards if card.status == STATUS_LOCKED),
        )
        next_lesson_id = next(
            (card.id for card in cards if card.status in UNLOCKED), None
        )
        return PathPlanResponse(
            level=user.level,
            lessons=cards,
            counts=counts,
            next_lesson_id=next_lesson_id,
            next_items=await self._next_items(user, cards),
        )

    async def get_progress(self, user: User) -> PathProgressResponse:
        plan = await self.get_plan(user)
        cards = plan.lessons
        total = len(cards)
        completed = plan.counts.completed
        counts = PathProgressCounts(
            total=total,
            completed=completed,
            available=plan.counts.available,
            locked=plan.counts.locked,
            percent=round(completed * 100 / total, 1) if total else 0.0,
        )

        modules_by_name: dict[str, ModuleProgress] = {}
        for card in cards:
            module = modules_by_name.get(card.module)
            if module is None:
                module = ModuleProgress(module=card.module, total=0, completed=0)
                modules_by_name[card.module] = module
            module.total += 1
            if card.status == STATUS_COMPLETED:
                module.completed += 1

        attempts = (
            await self.db.execute(
                select(QuizAttempt)
                .where(
                    QuizAttempt.user_id == user.id,
                    QuizAttempt.kind == "lesson",
                    QuizAttempt.status == "submitted",
                )
                .order_by(QuizAttempt.completed_at.asc(), QuizAttempt.id.asc())
            )
        ).scalars().all()
        score_points = [
            RecentQuiz(
                attempt_id=attempt.id,
                lesson_id=attempt.lesson_id,
                score=attempt.score or 0,
                total=attempt.total,
                passed=(attempt.score or 0) >= QUIZ_PASS_CORRECT,
                completed_at=attempt.completed_at,
            )
            for attempt in attempts
        ]
        correct_word_ids = await self._correct_word_ids(user.id)
        words_learned, roots_learned = await self._learned_counts(correct_word_ids)
        srs = await SRSService(self.db).get_stats(user.id)

        return PathProgressResponse(
            level=user.level,
            counts=counts,
            modules=list(modules_by_name.values()),
            xp=user.xp,
            streak_days=srs.streak_days,
            last_activity_date=user.last_activity_date,
            next_lesson=next((card for card in cards if card.status in UNLOCKED), None),
            recent_quizzes=list(reversed(score_points))[:10],
            words_learned=words_learned,
            roots_learned=roots_learned,
            quiz_scores_over_time=score_points,
            srs=srs,
        )

    async def list_lessons(
        self,
        user: User,
        *,
        module: str | None = None,
        status_value: LessonStatus | None = None,
    ) -> LessonListResponse:
        lessons = await self._band_lessons(user.level)
        if module is not None:
            lessons = [lesson for lesson in lessons if lesson.module == module]
        statuses, user_lessons = await self._statuses(lessons, user.id)
        cards = [
            self._card(lesson, statuses[lesson.id], user_lessons)
            for lesson in lessons
        ]
        if status_value is not None:
            cards = [card for card in cards if card.status == status_value]
        return LessonListResponse(lessons=cards, total=len(cards))

    async def lesson_status(self, user: User, lesson: Lesson) -> LessonStatus:
        statuses, _ = await self._statuses([lesson], user.id)
        return statuses[lesson.id]

    async def complete_lesson(
        self, user: User, lesson_id: int
    ) -> LessonCompleteResponse:
        now = datetime.now(UTC)
        lessons = await self._band_lessons(user.level)
        lesson = next((item for item in lessons if item.id == lesson_id), None)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found in your learning path",
            )

        before, user_lessons = await self._statuses(lessons, user.id)
        row = user_lessons.get(lesson.id)
        current = before[lesson.id]

        if current == STATUS_COMPLETED:
            return LessonCompleteResponse(
                lesson_id=lesson.id,
                status=STATUS_COMPLETED,
                score=row.score if row is not None else None,
                unlocked=[],
                xp_awarded=0,
                streak_days=user.streak_days,
            )
        if current == STATUS_LOCKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lesson is locked; complete its prerequisites first",
            )

        if row is None:
            row = UserLesson(user_id=user.id, lesson_id=lesson.id)
            self.db.add(row)
        row.status = STATUS_COMPLETED
        row.completed_at = now
        user.xp += LESSON_COMPLETE_XP
        await ProgressService(self.db).apply_activity(user.id, now.date())

        after, _ = await self._statuses(lessons, user.id)
        unlocked = [
            item.id
            for item in lessons
            if before[item.id] == STATUS_LOCKED and after[item.id] != STATUS_LOCKED
        ]
        await self.db.commit()
        logger.info(
            "user_id=%d completed lesson_id=%d, xp=%d, streak=%d",
            user.id,
            lesson.id,
            user.xp,
            user.streak_days,
        )
        return LessonCompleteResponse(
            lesson_id=lesson.id,
            status=STATUS_COMPLETED,
            score=row.score,
            unlocked=unlocked,
            xp_awarded=LESSON_COMPLETE_XP,
            streak_days=user.streak_days,
        )

    async def get_lesson(self, user: User, lesson_id: int) -> LessonDetailResponse:
        lesson = (
            await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        ).scalar_one_or_none()
        if lesson is None or lesson.level != user.level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found in your learning path",
            )

        statuses, _ = await self._statuses([lesson], user.id)
        lesson_status = statuses[lesson.id]
        if lesson_status == STATUS_LOCKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lesson is locked; complete its prerequisites first",
            )

        return LessonDetailResponse(
            id=lesson.id,
            title=lesson.title,
            module=lesson.module,
            level=lesson.level,
            sequence=lesson.sequence,
            root=lesson.root,
            est_minutes=lesson.est_minutes,
            content=lesson.content_json,
            status=lesson_status,
        )
