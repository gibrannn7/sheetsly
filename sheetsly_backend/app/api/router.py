"""API router aggregator."""

from fastapi import APIRouter
from app.api.routes import (
    analytics_router,
    datasets_router,
    health_router,
    sheets_router,
    visualization_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(datasets_router)
api_router.include_router(sheets_router)
api_router.include_router(analytics_router)
api_router.include_router(visualization_router)
