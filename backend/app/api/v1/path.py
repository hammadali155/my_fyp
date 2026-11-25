from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.path import (
    AssessmentResponse,
    AssessmentResultResponse,
    AssessmentSubmitRequest,
    LessonCompleteResponse,
    LessonDetailResponse,
    LessonListResponse,
    LessonStatus,
    PathPlanResponse,
    PathProgressResponse,
    QuizStartResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.path_service import PathService
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/path", tags=["Learning Path"])
logger = get_logger("api.path")


@router.get(
    "/plan",
    response_model=PathPlanResponse,
    summary="Get the current user's personalized learning path",
)
async def get_plan(db: DbSession, current_user: CurrentUser) -> PathPlanResponse:
    return await PathService(db).get_plan(current_user)


@router.get(
    "/progress",
    response_model=PathProgressResponse,
    summary="Get learning-path counts, streak and recent quiz results",
)
async def get_progress(db: DbSession, current_user: CurrentUser) -> PathProgressResponse:
    return await PathService(db).get_progress(current_user)


@router.get(
    "/lessons",
    response_model=LessonListResponse,
    summary="List lessons in the user's level band with derived lock state",
)
async def list_lessons(
    db: DbSession,
    current_user: CurrentUser,
    module: str | None = Query(default=None, description="Filter by module"),
    status: LessonStatus | None = Query(default=None, description="Filter by state"),
) -> LessonListResponse:
    return await PathService(db).list_lessons(
        current_user, module=module, status_value=status
    )


@router.post(
    "/lessons/{lesson_id}/quiz",
    response_model=QuizStartResponse,
    summary="Start a five-question lesson quiz; answers are graded server-side",
)
async def start_lesson_quiz(
    lesson_id: int, db: DbSession, current_user: CurrentUser
) -> QuizStartResponse:
    return await QuizService(db).start_lesson_quiz(current_user, lesson_id)


@router.post(
    "/quiz/{attempt_id}/submit",
    response_model=QuizSubmitResponse,
    summary="Grade a lesson quiz attempt and award XP",
)
async def submit_quiz(
    attempt_id: int,
    req: QuizSubmitRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> QuizSubmitResponse:
    return await QuizService(db).submit_quiz(
        current_user, attempt_id, req.answers
    )


@router.get(
    "/assess",
    response_model=AssessmentResponse,
    summary="Get the fixed twenty-question placement assessment",
)
async def get_assessment(
    db: DbSession, current_user: CurrentUser
) -> AssessmentResponse:
    questions, _ = await QuizService(db).build_assessment()
    return AssessmentResponse(total=len(questions), questions=questions)


@router.post(
    "/assess",
    response_model=AssessmentResultResponse,
    summary="Grade the placement assessment and set the user's level",
)
async def submit_assessment(
    req: AssessmentSubmitRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> AssessmentResultResponse:
    return await QuizService(db).submit_assessment(current_user, req.answers)


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonCompleteResponse,
    summary="Mark a lesson complete, award XP and unlock dependants",
)
async def complete_lesson(
    lesson_id: int, db: DbSession, current_user: CurrentUser
) -> LessonCompleteResponse:
    return await PathService(db).complete_lesson(current_user, lesson_id)


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
    summary="Get one lesson's content; 409 when locked",
)
async def get_lesson(
    lesson_id: int, db: DbSession, current_user: CurrentUser
) -> LessonDetailResponse:
    return await PathService(db).get_lesson(current_user, lesson_id)
