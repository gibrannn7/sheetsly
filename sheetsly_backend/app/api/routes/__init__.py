"""API routes package exports."""

from app.api.routes.agent import router as agent_router
from app.api.routes.ai import router as ai_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.health import router as health_router
from app.api.routes.sheets import router as sheets_router
from app.api.routes.visualization import router as visualization_router

__all__ = [
    "agent_router",
    "ai_router",
    "analytics_router",
    "datasets_router",
    "health_router",
    "sheets_router",
    "visualization_router",
]
