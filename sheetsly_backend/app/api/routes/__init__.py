"""API routes package."""

from .health import router as health_router
from .datasets import router as datasets_router
from .sheets import router as sheets_router
from .analytics import router as analytics_router
from .visualization import router as visualization_router

__all__ = ["health_router", "datasets_router", "sheets_router", "analytics_router", "visualization_router"]
