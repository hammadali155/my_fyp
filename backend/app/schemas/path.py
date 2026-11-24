from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.srs import SRSStatsResponse

LessonStatus = Literal["locked", "available", "in_progress", "completed"]
QuizType = Literal["root", "meaning", "fill_blank", "pos"]


class LessonCard(BaseModel):
    id: int
    title: str
    module: str
    level: str
    sequence: int
    root: str | None = None
    status: LessonStatus
    score: float | None = None
    est_minutes: int


class PathCounts(BaseModel):
    total: int
    completed: int
    available: int
    locked: int


class PathNextItem(BaseModel):
    lesson_id: int
    lesson_title: str
    word_id: int
    text_uthmani: str
    root: str | None
    kind: str


class PathPlanResponse(BaseModel):
    level: str
    lessons: list[LessonCard]
    counts: PathCounts
    next_lesson_id: int | None
    next_items: list[PathNextItem] = Field(default_factory=list)


class PathProgressCounts(PathCounts):
    percent: float


class ModuleProgress(BaseModel):
    module: str
    total: int
    completed: int


class RecentQuiz(BaseModel):
    attempt_id: int
    lesson_id: int | None
    score: int
    total: int
    passed: bool
    completed_at: datetime | None = None


class PathProgressResponse(BaseModel):
    level: str
    counts: PathProgressCounts
    modules: list[ModuleProgress]
    xp: int
    streak_days: int
    last_activity_date: date | None = None
    next_lesson: LessonCard | None = None
    recent_quizzes: list[RecentQuiz] = Field(default_factory=list)
    words_learned: int = 0
    roots_learned: int = 0
    quiz_scores_over_time: list[RecentQuiz] = Field(default_factory=list)
    srs: SRSStatsResponse


class LessonListResponse(BaseModel):
    lessons: list[LessonCard]
    total: int


class LessonCompleteResponse(BaseModel):
    lesson_id: int
    status: LessonStatus
    score: float | None = None
    unlocked: list[int]
    xp_awarded: int
    streak_days: int


class LessonDetailResponse(BaseModel):
    id: int
    title: str
    module: str
    level: str
    sequence: int
    root: str | None
    est_minutes: int
    content: dict[str, Any]
    status: LessonStatus


class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    index: int
    type: QuizType
    prompt: str
    options: list[QuizOption]
    word: str | None = None
    word_id: int | None = None
    verse_id: int | None = None
    verse_text_uthmani: str | None = None
    hidden_position: int | None = None


class QuizStartResponse(BaseModel):
    attempt_id: int
    lesson_id: int
    total: int
    questions: list[QuizQuestion]


class QuizAnswerRequest(BaseModel):
    index: int = Field(..., ge=1)
    option_id: str = Field(..., min_length=1, max_length=200)


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerRequest] = Field(default_factory=list)


class QuizResultItem(BaseModel):
    index: int
    question_type: QuizType
    chosen_option_id: str | None
    correct_option_id: str
    correct: bool
    explanation: str


class QuizSubmitResponse(BaseModel):
    attempt_id: int
    lesson_id: int | None
    score: int
    correct: int
    total: int
    passed: bool
    xp_awarded: int
    results: list[QuizResultItem]
    srs_card_ids: list[int]


class AssessmentResponse(BaseModel):
    total: int
    questions: list[QuizQuestion]


class AssessmentSubmitRequest(BaseModel):
    answers: list[QuizAnswerRequest] = Field(default_factory=list)


class AssessmentResultResponse(BaseModel):
    score: int
    total: int
    correct: int
    placed_level: str
    previous_level: str
