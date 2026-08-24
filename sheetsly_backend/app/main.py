"""FastAPI application main entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import SheetslyError, generic_exception_handler, sheetsly_exception_handler
from app.core.logging import logger
from app.storage.file_manager import file_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    logger.info(f"Allowed CORS origins: {settings.CORS_ORIGINS}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")
    file_manager.cleanup_all()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Assisted Spreadsheet Intelligence Workspace Backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(SheetslyError, sheetsly_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Routers
app.include_router(api_router)


@app.get("/")
async def root_redirect():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "api_v1": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
