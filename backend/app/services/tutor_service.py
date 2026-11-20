from __future__ import annotations

import asyncio
import math
import re
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any, Literal, cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chat import ChatMessage, ChatSession
from app.models.quran import Surah, Verse
from app.models.user import User
from app.schemas.tutor import (
    TutorChatRequest,
    TutorChatResponse,
    TutorCitationOut,
    TutorSessionList,
    TutorSessionSummary,
    TutorUsage,
)
from app.services.llm_client import ChatMessage as LLMChatMessage
from app.services.llm_client import (
    GenerationSettings,
    LLMClient,
    LLMError,
    LLMNotConfiguredError,
    LLMResult,
    MessageRole,
)
from app.services.nahw_explain_service import LANGUAGE_NAMES, normalize_language
from app.services.tutor_context import ContextReference, TutorContext, TutorContextService
from app.services.tutor_prompts import build_tutor_system_prompt

logger = get_logger("services.tutor")

CITATION_PATTERN = re.compile(r"\b([1-9]\d{0,2})\s*[:：]\s*([1-9]\d{0,2})\b")
MAX_SURAH_NUMBER = 114

NOT_CONFIGURED_DETAIL = "Tutor is not configured (GEMINI_API_KEY is missing)"
UNAVAILABLE_DETAIL = "Tutor is unavailable; try again later"
EMPTY_RESPONSE_DETAIL = "Tutor returned an empty response"


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def select_history(
    messages: Sequence[LLMChatMessage], max_tokens: int
) -> list[LLMChatMessage]:
    """Keeps the newest messages that fit the budget; always keeps the newest one."""
    if not messages:
        return []
    selected = [messages[-1]]
    used = estimate_tokens(messages[-1].content)
    for message in reversed(messages[:-1]):
        cost = estimate_tokens(message.content)
        if used + cost > max_tokens:
            break
        selected.append(message)
        used += cost
    selected.reverse()
    return selected


def extract_cited_pairs(text: str) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for match in CITATION_PATTERN.finditer(text):
        pair = (int(match.group(1)), int(match.group(2)))
        if pair[0] > MAX_SURAH_NUMBER:
            continue
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)
    return pairs


def build_user_prompt(question: str, context_text: str) -> str:
    return (
        "Retrieved context (verbatim from the database):\n"
        f"{context_text}\n\n"
        "Learner question:\n"
        f"{question}"
    )


@dataclass
class PreparedChat:
    session: ChatSession
    context: TutorContext
    messages: list[LLMChatMessage]
    level: str
    language: str


@dataclass(frozen=True)
class TutorStreamEvent:
    event: Literal["token", "done", "error"]
    data: dict[str, Any]


class TutorService:
    def __init__(self, db: AsyncSession, client: LLMClient | None = None) -> None:
        self.db = db
        self.client = client

    async def prepare(self, *, user: User, req: TutorChatRequest) -> PreparedChat:
        settings = get_settings()
        await self._enforce_daily_limit(user.id, settings.tutor_daily_message_limit)

        session = await self._load_or_create_session(user.id, req.session_id)
        history = await self._load_history(session.id)

        language = normalize_language(user.ui_lang)
        reference = (
            ContextReference(
                surah_number=req.reference.surah_number,
                ayah_number=req.reference.ayah_number,
                word_id=req.reference.word_id,
            )
            if req.reference is not None
            else None
        )
        context = await TutorContextService(self.db).build(
            message=req.message,
            languages=(language,),
            reference=reference,
        )

        messages = select_history(
            [
                *history,
                LLMChatMessage(
                    role="user",
                    content=build_user_prompt(req.message, context.text),
                ),
            ],
            settings.tutor_history_max_tokens,
        )
        return PreparedChat(
            session=session,
            context=context,
            messages=messages,
            level=user.level,
            language=language,
        )

    async def chat(self, *, user: User, req: TutorChatRequest) -> TutorChatResponse:
        prepared = await self.prepare(user=user, req=req)
        result = await self._generate(
            prepared.level, prepared.language, prepared.messages
        )

        reply = result.text.strip()
        if not reply:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=EMPTY_RESPONSE_DETAIL,
            )

        citations = await self._verified_citations(reply, prepared.context)
        model = get_settings().gemini_model
        await self._store_exchange(
            session=prepared.session,
            question=req.message,
            reply=reply,
            citations=citations,
            context=prepared.context,
            model=model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            incomplete=False,
        )

        logger.info(
            "Tutor reply session_id=%s citations=%d context_verses=%d",
            prepared.session.id,
            len(citations),
            len(prepared.context.verse_ids),
        )
        return self._response(
            prepared,
            reply=reply,
            citations=citations,
            model=model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            incomplete=False,
        )

    async def stream(
        self, *, prepared: PreparedChat, question: str
    ) -> AsyncIterator[TutorStreamEvent]:
        chunks: list[str] = []
        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        model = get_settings().gemini_model
        try:
            if self.client is None:
                raise LLMNotConfiguredError("LLM client is missing")
            async for event in self.client.stream(
                system_prompt=build_tutor_system_prompt(
                    level=prepared.level,
                    language=LANGUAGE_NAMES.get(prepared.language, "English"),
                ),
                messages=prepared.messages,
                settings=GenerationSettings(temperature=0.3, max_output_tokens=600),
            ):
                if event.prompt_tokens is not None:
                    prompt_tokens = event.prompt_tokens
                if event.completion_tokens is not None:
                    completion_tokens = event.completion_tokens
                if event.text:
                    chunks.append(event.text)
                    yield TutorStreamEvent(event="token", data={"text": event.text})

            reply = "".join(chunks).strip()
            if not reply:
                raise LLMError("Gemini returned an empty streaming response")

            citations = await self._verified_citations(reply, prepared.context)
            await self._store_exchange(
                session=prepared.session,
                question=question,
                reply=reply,
                citations=citations,
                context=prepared.context,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                incomplete=False,
            )
            response = self._response(
                prepared,
                reply=reply,
                citations=citations,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                incomplete=False,
            )
            yield TutorStreamEvent(
                event="done", data=response.model_dump(mode="json")
            )
        except LLMNotConfiguredError:
            await self._store_incomplete(
                prepared, question, "".join(chunks), model
            )
            yield TutorStreamEvent(
                event="error",
                data={"detail": NOT_CONFIGURED_DETAIL, "incomplete": True},
            )
        except LLMError:
            await self._store_incomplete(
                prepared, question, "".join(chunks), model
            )
            yield TutorStreamEvent(
                event="error",
                data={"detail": UNAVAILABLE_DETAIL, "incomplete": True},
            )
        except asyncio.CancelledError:
            await self._store_incomplete(
                prepared, question, "".join(chunks), model
            )
            raise

    async def list_sessions(self, *, user_id: int) -> TutorSessionList:
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        )
        sessions = result.scalars().all()
        return TutorSessionList(
            sessions=[
                TutorSessionSummary(
                    id=session.id,
                    title=session.title,
                    message_count=len(session.messages),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
                for session in sessions
            ]
        )

    async def delete_session(self, *, user_id: int, session_id: int) -> None:
        session = await self._get_owned_session(user_id, session_id)
        await self.db.delete(session)
        await self.db.commit()
        logger.info("Deleted tutor session id=%s", session_id)

    async def _enforce_daily_limit(self, user_id: int, limit: int) -> None:
        since = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
        count = (
            await self.db.execute(
                select(func.count(ChatMessage.id))
                .select_from(ChatMessage)
                .join(ChatSession, ChatMessage.session_id == ChatSession.id)
                .where(
                    ChatSession.user_id == user_id,
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= since,
                )
            )
        ).scalar_one()
        if count >= limit:
            logger.info("Daily tutor limit reached user_id=%s limit=%d", user_id, limit)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Daily tutor message limit reached ({limit} messages per day). "
                    "Try again tomorrow."
                ),
            )

    async def _load_or_create_session(
        self, user_id: int, session_id: int | None
    ) -> ChatSession:
        if session_id is None:
            session = ChatSession(user_id=user_id)
            self.db.add(session)
            await self.db.flush()
            return session
        return await self._get_owned_session(user_id, session_id)

    async def _get_owned_session(self, user_id: int, session_id: int) -> ChatSession:
        session = (
            await self.db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor session {session_id} not found",
            )
        return session

    async def _load_history(self, session_id: int) -> list[LLMChatMessage]:
        rows = (
            (
                await self.db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
                )
            )
            .scalars()
            .all()
        )
        return [
            LLMChatMessage(role=cast(MessageRole, row.role), content=row.content)
            for row in rows
            if row.role in ("user", "assistant")
        ]

    async def _generate(
        self, level: str, language: str, messages: list[LLMChatMessage]
    ) -> LLMResult:
        if self.client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=NOT_CONFIGURED_DETAIL,
            )
        try:
            return await self.client.generate(
                system_prompt=build_tutor_system_prompt(
                    level=level,
                    language=LANGUAGE_NAMES.get(language, "English"),
                ),
                messages=messages,
                settings=GenerationSettings(temperature=0.3, max_output_tokens=600),
            )
        except LLMNotConfiguredError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=NOT_CONFIGURED_DETAIL,
            ) from exc
        except LLMError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=UNAVAILABLE_DETAIL,
            ) from exc

    async def _verified_citations(
        self, reply: str, context: TutorContext
    ) -> list[TutorCitationOut]:
        allowed = {(citation.surah, citation.ayah) for citation in context.citations}
        citations: list[TutorCitationOut] = []
        for surah_number, ayah_number in extract_cited_pairs(reply):
            if (surah_number, ayah_number) not in allowed:
                logger.info(
                    "Dropped citation not present in context: %d:%d",
                    surah_number,
                    ayah_number,
                )
                continue
            exists = (
                await self.db.execute(
                    select(Verse.id)
                    .join(Surah, Verse.surah_id == Surah.id)
                    .where(
                        Surah.number == surah_number,
                        Verse.ayah_number == ayah_number,
                    )
                    .limit(1)
                )
            ).first()
            if exists is None:
                continue
            citations.append(TutorCitationOut(surah=surah_number, ayah=ayah_number))
        return citations

    def _response(
        self,
        prepared: PreparedChat,
        *,
        reply: str,
        citations: list[TutorCitationOut],
        model: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        incomplete: bool,
    ) -> TutorChatResponse:
        return TutorChatResponse(
            session_id=prepared.session.id,
            reply=reply,
            citations=citations,
            model=model,
            usage=TutorUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
            truncated_context=prepared.context.truncated,
            unresolved_references=prepared.context.unresolved_references,
            incomplete=incomplete,
        )

    async def _store_incomplete(
        self,
        prepared: PreparedChat,
        question: str,
        partial: str,
        model: str,
    ) -> None:
        try:
            await self._store_exchange(
                session=prepared.session,
                question=question,
                reply=partial,
                citations=[],
                context=prepared.context,
                model=model,
                prompt_tokens=None,
                completion_tokens=None,
                incomplete=True,
            )
        except Exception:
            logger.exception(
                "Failed to store incomplete tutor message session_id=%s",
                prepared.session.id,
            )

    async def _store_exchange(
        self,
        *,
        session: ChatSession,
        question: str,
        reply: str,
        citations: list[TutorCitationOut],
        context: TutorContext,
        model: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        incomplete: bool,
    ) -> None:
        self.db.add(
            ChatMessage(
                session_id=session.id,
                role="user",
                content=question,
                retrieved_verse_ids=context.verse_ids,
            )
        )
        self.db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=reply,
                citations_json=[citation.model_dump() for citation in citations],
                retrieved_verse_ids=context.verse_ids,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                incomplete=incomplete,
            )
        )
        session.updated_at = datetime.now(UTC)
        await self.db.commit()
