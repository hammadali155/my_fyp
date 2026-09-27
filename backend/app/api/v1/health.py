from __future__ import annotations

import platform
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.logging import get_logger

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger("api.health")

_APP_START_TIME = time.time()


class ComponentHealth(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    timestamp: str
    environment: str
    python_version: str
    platform: str
    database: ComponentHealth


class SimpleProbeResponse(BaseModel):
    status: str


@router.get("", response_model=HealthResponse)
async def full_health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    now_iso = datetime.now(UTC).isoformat()
    uptime = round(time.time() - _APP_START_TIME, 2)

    db_health = ComponentHealth(status="down")
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_health.status = "up"
        db_health.latency_ms = round((time.perf_counter() - db_start) * 1000, 2)
    except Exception as exc:
        db_health.error = str(exc)
        logger.error("Health check failed database ping: %s", exc)

    overall_status = "healthy" if db_health.status == "up" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        uptime_seconds=uptime,
        timestamp=now_iso,
        environment="development" if settings.debug else "production",
        python_version=platform.python_version(),
        platform=platform.platform(),
        database=db_health,
    )


@router.get("/ready", response_model=SimpleProbeResponse)
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> SimpleProbeResponse:
    try:
        await db.execute(text("SELECT 1"))
        return SimpleProbeResponse(status="ready")
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {exc}",
        ) from exc


@router.get("/live", response_model=SimpleProbeResponse)
async def liveness_probe() -> SimpleProbeResponse:
    return SimpleProbeResponse(status="alive")
