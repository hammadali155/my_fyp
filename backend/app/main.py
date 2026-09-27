from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.db.session import close_db, init_db

settings = get_settings()
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing %s v%s", settings.app_name, settings.app_version)
    await init_db()
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down %s", settings.app_name)
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Jawhar (جوهر) — AI-Powered Classical Arabic & Quranic Learning Platform Backend API",
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging and profiling middleware
app.add_middleware(RequestLoggingMiddleware)

# Root level health endpoint (for cloud orchestrators / load balancers)
app.include_router(health_router, prefix="")

# Mount versioned API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"], summary="API Root Status")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs_url": "/docs",
            "api_prefix": "/api/v1",
        }
    )
