from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("db.session")

_settings = get_settings()

connect_args = {}
if _settings.is_sqlite:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,
    connect_args=connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    import app.models.quran  # noqa: F401
    import app.models.user  # noqa: F401 — register models
    from app.db.base import Base

    logger.info("Creating database tables (if not exist)")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")


async def close_db() -> None:
    logger.info("Disposing database engine")
    await engine.dispose()
