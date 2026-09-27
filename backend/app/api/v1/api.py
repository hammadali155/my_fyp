from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.morphology import router as morphology_router
from app.api.v1.quran import router as quran_router
from app.api.v1.srs import router as srs_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(quran_router)
api_router.include_router(morphology_router)
api_router.include_router(srs_router)
