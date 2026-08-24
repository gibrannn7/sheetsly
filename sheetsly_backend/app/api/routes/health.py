"""Health and service diagnostic endpoints."""

from fastapi import APIRouter
from app.core.config import settings
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Returns application health status, version, and operational engine details."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
        engine={
            "python_analytical_engine": "active",
            "deterministic_parser": "openpyxl+pandas",
            "data_profiler": "active",
            "quality_engine": "active",
            "ai_integration": "disabled_for_phase_2",
            "database": "disabled",
        },
    )
