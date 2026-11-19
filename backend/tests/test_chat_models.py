from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import event, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User


async def _add_user(db: AsyncSession, email: str = "chat@example.com") -> User:
    user = User(email=email, name="Chatter", password_hash="hash")
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def fk_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_and_message_round_trip_with_citations(db_session: AsyncSession) -> None:
    user = await _add_user(db_session)

    message = ChatMessage(
        role="assistant",
        content="The root is ر ح م.",
        citations_json=[{"verse_id": 1, "reference": "1:1"}],
        retrieved_verse_ids=[1],
        model="gemini-2.0-flash",
        prompt_tokens=120,
        completion_tokens=30,
    )
    session = ChatSession(user_id=user.id, title="Roots", messages=[message])
    db_session.add(session)
    await db_session.commit()

    assert session.id is not None
    assert message.session_id == session.id
    assert session.messages == [message]
    assert message.session is session
    assert message.citations_json == [{"verse_id": 1, "reference": "1:1"}]
    assert message.retrieved_verse_ids == [1]
    assert message.prompt_tokens == 120
    assert message.completion_tokens == 30
    assert message.created_at is not None
    assert message.updated_at is not None


@pytest.mark.asyncio
async def test_new_session_and_message_get_safe_defaults(db_session: AsyncSession) -> None:
    user = await _add_user(db_session)
    session = ChatSession(user_id=user.id)
    db_session.add(session)
    await db_session.commit()

    message = ChatMessage(session_id=session.id, role="user", content="What is a root?")
    db_session.add(message)
    await db_session.commit()

    assert session.title == "New session"
    assert session.created_at is not None
    assert session.updated_at is not None
    assert message.citations_json is None
    assert message.retrieved_verse_ids is None
    assert message.model is None
    assert message.prompt_tokens is None
    assert message.completion_tokens is None
    assert message.incomplete is False


@pytest.mark.asyncio
async def test_incomplete_flag_round_trips(db_session: AsyncSession) -> None:
    user = await _add_user(db_session, email="incomplete@example.com")
    session = ChatSession(user_id=user.id)
    db_session.add(session)
    await db_session.commit()

    message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="The rule is",
        incomplete=True,
    )
    db_session.add(message)
    await db_session.commit()

    assert message.incomplete is True


@pytest.mark.asyncio
async def test_role_is_limited_to_user_assistant_or_system(db_session: AsyncSession) -> None:
    user = await _add_user(db_session)
    session = ChatSession(user_id=user.id, title="Roots")
    db_session.add(session)
    await db_session.commit()

    for role in ("user", "assistant", "system"):
        message = ChatMessage(session_id=session.id, role=role, content="valid")
        db_session.add(message)
        await db_session.flush()
        await db_session.commit()

    db_session.add(ChatMessage(session_id=session.id, role="mufti", content="nope"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_deleting_a_session_deletes_its_messages(db_session: AsyncSession) -> None:
    user = await _add_user(db_session)
    session = ChatSession(
        user_id=user.id,
        title="Roots",
        messages=[
            ChatMessage(role="user", content="question"),
            ChatMessage(role="assistant", content="answer"),
        ],
    )
    db_session.add(session)
    await db_session.commit()

    await db_session.delete(session)
    await db_session.commit()

    assert (
        await db_session.execute(select(func.count()).select_from(ChatMessage))
    ).scalar_one() == 0


@pytest.mark.asyncio
async def test_deleting_a_user_deletes_sessions_and_messages(fk_engine: AsyncEngine) -> None:
    factory = async_sessionmaker(fk_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(email="cascade@example.com", name="Cascade", password_hash="hash")
        db.add(user)
        await db.commit()

        session = ChatSession(user_id=user.id, title="Cascade")
        db.add(session)
        await db.commit()
        db.add(ChatMessage(session_id=session.id, role="user", content="question"))
        await db.commit()

        await db.delete(user)
        await db.commit()

        assert (
            await db.execute(select(func.count()).select_from(ChatSession))
        ).scalar_one() == 0
        assert (
            await db.execute(select(func.count()).select_from(ChatMessage))
        ).scalar_one() == 0


@pytest.mark.asyncio
async def test_schema_declares_cascades_and_ordered_message_index(
    fk_engine: AsyncEngine,
) -> None:
    async with fk_engine.connect() as conn:
        session_fks = (
            (await conn.exec_driver_sql("PRAGMA foreign_key_list('chat_sessions')"))
            .mappings()
            .all()
        )
        message_fks = (
            (await conn.exec_driver_sql("PRAGMA foreign_key_list('chat_messages')"))
            .mappings()
            .all()
        )
        indexes = await conn.run_sync(lambda c: inspect(c).get_indexes("chat_messages"))

    assert [(fk["table"], fk["on_delete"]) for fk in session_fks] == [("users", "CASCADE")]
    assert [(fk["table"], fk["on_delete"]) for fk in message_fks] == [
        ("chat_sessions", "CASCADE")
    ]
    assert any(
        index["column_names"] == ["session_id", "created_at"] for index in indexes
    )
