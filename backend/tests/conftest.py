from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.quran import Surah, Verse, Word
from app.models.user import User  # noqa: F401

# In-memory async SQLite engine for fast, isolated tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def override_settings():
    settings = get_settings()
    settings.debug = True
    settings.jwt_secret = "test-jwt-secret-key-32-chars-minimum-xxx"
    return settings


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    payload = {
        "email": "talib@example.com",
        "name": "Talib Ilm",
        "password": "SecurePassword123!",
        "native_lang": "en",
        "ui_lang": "en",
        "level": "beginner",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(registered_user: dict) -> dict[str, str]:
    token = registered_user["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_quran_data(db_session: AsyncSession):
    """Seed Surah Al-Fatiha (1) with Ayah 1 & 2 for testing."""
    fatiha = Surah(
        id=1,
        number=1,
        name_arabic="الفاتحة",
        name_transliteration="Al-Fatihah",
        name_english="The Opener",
        revelation_place="Makkah",
        verse_count=7,
    )
    db_session.add(fatiha)
    await db_session.flush()

    v1 = Verse(
        id=1,
        surah_id=1,
        ayah_number=1,
        text_uthmani="بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        text_imlaei="بسم الله الرحمن الرحيم",
        translation_en="In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        translation_ur="شروع اللہ کا نام لے کر جو بڑا مہربان نہایت رحم والا ہے",
        juz_number=1,
        hizb_number=1,
        page_number=1,
    )
    db_session.add(v1)
    await db_session.flush()

    w1 = Word(
        verse_id=1,
        position=1,
        text_uthmani="بِسْمِ",
        text_imlaei="بسم",
        translation_en="In (the) name",
        transliteration="bis'mi",
        root="سمو",
        lemma="اسْم",
        pos_tag="N",
    )
    w2 = Word(
        verse_id=1,
        position=2,
        text_uthmani="ٱللَّهِ",
        text_imlaei="الله",
        translation_en="(of) Allah",
        transliteration="l-lahi",
        root="اله",
        lemma="اللَّه",
        pos_tag="PN",
    )
    w3 = Word(
        verse_id=1,
        position=3,
        text_uthmani="ٱلرَّحْمَـٰنِ",
        text_imlaei="الرحمن",
        translation_en="the Entirely Merciful",
        transliteration="l-rahmani",
        root="رحم",
        lemma="رَحْمَن",
        pos_tag="ADJ",
    )
    w4 = Word(
        verse_id=1,
        position=4,
        text_uthmani="ٱلرَّحِيمِ",
        text_imlaei="الرحيم",
        translation_en="the Especially Merciful",
        transliteration="l-rahimi",
        root="رحم",
        lemma="رَحِيم",
        pos_tag="ADJ",
    )
    v2 = Verse(
        id=2,
        surah_id=1,
        ayah_number=2,
        text_uthmani="ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
        text_imlaei="الحمد لله رب العالمين",
        translation_en="[All] praise is [due] to Allah, Lord of the worlds -",
        translation_ur="سب طرح کی تعریف خدا ہی کو سزاوار ہے",
        juz_number=1,
        hizb_number=1,
        page_number=1,
    )
    db_session.add(v2)
    await db_session.flush()

    w5 = Word(
        verse_id=2,
        position=1,
        text_uthmani="ٱلْحَمْدُ",
        text_imlaei="الحمد",
        translation_en="[All] praise",
        transliteration="al-hamdu",
        root="حمد",
        lemma="حَمْد",
        pos_tag="N",
    )
    db_session.add_all([w1, w2, w3, w4, w5])
    await db_session.commit()
