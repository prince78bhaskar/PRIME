"""
P.R.I.M.E. Health Check Endpoint.

Provides a lightweight liveness and readiness probe for the application.
Reports application status, version, database connectivity, and uptime.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Application Health Check",
    description="Returns application liveness status, version, database state, and uptime.",
    response_model=dict[str, Any],
)
async def health_check(request: Request) -> dict[str, Any]:
    """Return application health status.

    Checks:
    - Application is running (liveness)
    - Database connection is active (readiness)
    - Uptime since application start
    """
    app = request.app

    # Database status
    db_status = "disconnected"
    db_manager = getattr(app.state, "db", None)
    if db_manager is not None and db_manager.is_connected:
        try:
            db_manager.get_connection().execute("SELECT 1")
            db_status = "connected"
        except Exception:
            db_status = "error"

    # Calculate uptime
    start_time = getattr(app.state, "start_time", None)
    uptime_seconds = round(time.time() - start_time, 2) if start_time else None

    settings = getattr(app.state, "settings", None)

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.app_version if settings else "unknown",
        "environment": settings.environment if settings else "unknown",
        "database": db_status,
        "uptime_seconds": uptime_seconds,
    }
