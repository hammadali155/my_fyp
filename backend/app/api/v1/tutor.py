from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.tutor import TutorChatRequest, TutorChatResponse, TutorSessionList
from app.services.llm_client import LLMClientDep
from app.services.tutor_service import PreparedChat, TutorService, TutorStreamEvent

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])
logger = get_logger("api.tutor")

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def format_sse_event(event: TutorStreamEvent) -> str:
    payload = json.dumps(event.data, ensure_ascii=False)
    return f"event: {event.event}\ndata: {payload}\n\n"


async def _sse_body(
    service: TutorService, prepared: PreparedChat, question: str
) -> AsyncIterator[str]:
    async for event in service.stream(prepared=prepared, question=question):
        yield format_sse_event(event)


@router.post(
    "/chat",
    response_model=TutorChatResponse,
    summary="Send a message to the AI Tutor and store the exchange",
)
async def chat(
    req: TutorChatRequest,
    db: DbSession,
    current_user: CurrentUser,
    client: LLMClientDep,
) -> TutorChatResponse:
    service = TutorService(db, client)
    return await service.chat(user=current_user, req=req)


@router.post(
    "/chat/stream",
    response_model=None,
    response_class=StreamingResponse,
    summary="Send a message to the AI Tutor and stream the reply over server-sent events",
)
async def chat_stream(
    req: TutorChatRequest,
    db: DbSession,
    current_user: CurrentUser,
    client: LLMClientDep,
) -> StreamingResponse:
    service = TutorService(db, client)
    prepared = await service.prepare(user=current_user, req=req)
    return StreamingResponse(
        _sse_body(service, prepared, req.message),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get(
    "/sessions",
    response_model=TutorSessionList,
    summary="List the authenticated user's tutor conversations",
)
async def list_sessions(db: DbSession, current_user: CurrentUser) -> TutorSessionList:
    service = TutorService(db)
    return await service.list_sessions(user_id=current_user.id)


@router.delete(
    "/sessions/{session_id}",
    status_code=204,
    summary="Delete one of the authenticated user's tutor conversations",
)
async def delete_session(
    session_id: int, db: DbSession, current_user: CurrentUser
) -> None:
    service = TutorService(db)
    await service.delete_session(user_id=current_user.id, session_id=session_id)
