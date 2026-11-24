from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

MODULES = ("sarf", "nahw", "vocabulary")
LEVELS = ("beginner", "intermediate", "advanced")
LESSON_STATUSES = ("not_started", "in_progress", "completed")


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint(
            "module", "level", "sequence", name="uq_lessons_module_level_sequence"
        ),
        CheckConstraint(
            "module IN ('sarf', 'nahw', 'vocabulary')", name="ck_lessons_module"
        ),
        CheckConstraint(
            "level IN ('beginner', 'intermediate', 'advanced')", name="ck_lessons_level"
        ),
        Index("ix_lessons_level_sequence", "level", "sequence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    est_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    root: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} root={self.root!r} level={self.level!r}>"


class LessonPrerequisite(Base):
    __tablename__ = "lesson_prerequisites"
    __table_args__ = (
        CheckConstraint(
            "lesson_id != requires_lesson_id", name="ck_lesson_prereq_not_self"
        ),
    )

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    requires_lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )


class LessonWord(TimestampMixin, Base):
    __tablename__ = "lesson_words"
    __table_args__ = (
        UniqueConstraint(
            "lesson_id", "word_id", "kind", name="uq_lesson_words_lesson_word_kind"
        ),
        Index("ix_lesson_words_lesson", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    word_id: Mapped[int] = mapped_column(
        ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="form")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserLesson(TimestampMixin, Base):
    __tablename__ = "user_lessons"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lessons_user_lesson"),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_user_lessons_status",
        ),
        Index("ix_user_lessons_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class QuizAttempt(TimestampMixin, Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('lesson', 'assessment')", name="ck_quiz_attempts_kind"
        ),
        CheckConstraint(
            "status IN ('open', 'submitted')", name="ck_quiz_attempts_status"
        ),
        Index("ix_quiz_attempts_user", "user_id"),
        Index("ix_quiz_attempts_lesson", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[int | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="lesson")
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    questions_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    answer_key_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class QuizAnswer(TimestampMixin, Base):
    __tablename__ = "quiz_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id", "question_index", name="uq_quiz_answers_attempt_question"
        ),
        Index("ix_quiz_answers_attempt", "attempt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    option_id: Mapped[str] = mapped_column(String(200), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint(
            "placed_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_assessment_placed_level",
        ),
        Index("ix_assessment_attempts_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    placed_level: Mapped[str] = mapped_column(String(20), nullable=False)
    answers_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
