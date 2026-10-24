"""
P.R.I.M.E. FastAPI Application Entry Point.

Configures the application lifespan (startup/shutdown), middleware,
error handlers, and API route registration.
"""

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.ollama import router as ollama_router
from app.api.voice import router as voice_router
from app.core.config import Settings, get_settings
from app.core.database import DatabaseManager
from app.core.logging import setup_logging
from app.core.ollama_client import OllamaClient
from app.core.voice_service import VoiceService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup initialization and graceful shutdown:
    - Startup: logging, configuration, database connection and schema init.
    - Shutdown: database disconnection, resource cleanup.
    """
    # ── Startup ──────────────────────────────────────────────────
    settings: Settings = app.state.settings
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_dir=settings.log_dir,
    )

    logger.info(
        "Starting P.R.I.M.E. backend",
        extra={
            "version": settings.app_version,
            "environment": settings.environment,
            "host": settings.host,
            "port": settings.port,
        },
    )

    # Database initialization
    db = DatabaseManager(db_path=settings.db_path)
    db.connect()
    db.initialize_schema()
    app.state.db = db

    # Ollama client initialization (if not already injected by test harness)
    if getattr(app.state, "ollama_client", None) is None:
        ollama_client = OllamaClient(
            base_url=settings.ollama_base_url,
            default_model=settings.ollama_model,
            timeout_seconds=float(settings.ollama_timeout_seconds),
        )
        app.state.ollama_client = ollama_client

    if getattr(app.state, "voice_service", None) is None:
        app.state.voice_service = VoiceService(settings)

    # Record startup time for uptime tracking
    app.state.start_time = time.time()

    logger.info("P.R.I.M.E. backend startup complete")

    yield  # ── Application is running ────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────
    logger.info("Shutting down P.R.I.M.E. backend")
    if hasattr(app.state, "ollama_client") and app.state.ollama_client is not None:
        await app.state.ollama_client.close()
    if hasattr(app.state, "db") and app.state.db is not None:
        app.state.db.close()
    logger.info("P.R.I.M.E. backend shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory.

    Creates and configures a FastAPI application instance.

    Args:
        settings: Optional Settings override (used in testing).
                  If None, settings are loaded from environment.

    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "P.R.I.M.E. — Personal Responsive Intelligent Multi-Agent Environment. "
            "A sovereign, offline-first local AI assistant backend."
        ),
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Store settings on app state for access in routes and lifespan
    app.state.settings = settings

    # ── Middleware ────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Error Handlers ───────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all error handler ensuring structured JSON error responses."""
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"path": str(request.url)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
                "detail": str(exc) if settings.debug else None,
            },
        )

    # ── Routes ───────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(ollama_router)
    app.include_router(voice_router)

    return app


# Default application instance for uvicorn
app = create_app()
