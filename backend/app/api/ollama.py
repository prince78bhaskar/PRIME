"""
P.R.I.M.E. Ollama Local Runtime API Endpoints.

Provides REST and SSE streaming endpoints for interacting with local Ollama models.
Strictly routes all inference to the local daemon — no cloud fallbacks or external keys.
"""

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import Settings, get_settings
from app.core.ollama_client import OllamaClient
from app.core.ollama_errors import (
    OllamaConnectionError,
    OllamaError,
    OllamaHardwareLimitError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from app.schemas.ollama import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    OllamaHealthResponse,
    OllamaModelInfo,
    OllamaModelsListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ollama", tags=["ollama"])


def get_ollama_client(request: Request) -> OllamaClient:
    """Dependency provider for OllamaClient instance stored on app.state."""
    client = getattr(request.app.state, "ollama_client", None)
    if client is None:
        settings: Settings = getattr(request.app.state, "settings", get_settings())
        client = OllamaClient(
            base_url=settings.ollama_base_url,
            default_model=settings.ollama_model,
            timeout_seconds=float(settings.ollama_timeout_seconds),
        )
        request.app.state.ollama_client = client
    return client


@router.get(
    "/health",
    summary="Local Ollama Service Health Check",
    description="Inspects local Ollama daemon connectivity, version, and model availability.",
    response_model=OllamaHealthResponse,
)
async def check_ollama_health(
    client: OllamaClient = Depends(get_ollama_client),
) -> OllamaHealthResponse:
    """Check connectivity to local Ollama daemon."""
    return await client.check_health()


@router.get(
    "/models",
    summary="List Installed Local Models",
    description="Retrieves inventory of models currently downloaded in the local Ollama instance.",
    response_model=OllamaModelsListResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Ollama service unavailable"},
        504: {"model": ErrorResponse, "description": "Request timed out"},
    },
)
async def list_local_models(
    client: OllamaClient = Depends(get_ollama_client),
) -> OllamaModelsListResponse:
    """List installed models in local Ollama."""
    try:
        models = await client.list_models()
        return OllamaModelsListResponse(models=models, count=len(models))
    except OllamaConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "service_unavailable", "message": exc.message, "detail": exc.detail},
        ) from exc
    except OllamaTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "gateway_timeout", "message": exc.message, "detail": exc.detail},
        ) from exc


@router.post(
    "/chat",
    summary="Execute Local Chat Completion",
    description=(
        "Sends conversation turns to local Ollama. Supports both single-turn "
        "and streamed responses (Server-Sent Events) with hardware guardrails."
    ),
    response_model=ChatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Model not installed"},
        422: {"model": ErrorResponse, "description": "Model exceeds hardware bounds"},
        503: {"model": ErrorResponse, "description": "Ollama service unavailable"},
        504: {"model": ErrorResponse, "description": "Inference timed out"},
    },
)
async def chat_completion(
    chat_req: ChatRequest,
    client: OllamaClient = Depends(get_ollama_client),
):
    """Handle chat completion request to local Ollama."""
    if chat_req.stream:
        return _handle_chat_stream(chat_req, client)

    try:
        return await client.chat(chat_req)
    except OllamaHardwareLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "hardware_limit_exceeded", "message": exc.message, "detail": exc.detail},
        ) from exc
    except OllamaModelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "model_not_installed", "message": exc.message, "detail": exc.detail},
        ) from exc
    except OllamaConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "service_unavailable", "message": exc.message, "detail": exc.detail},
        ) from exc
    except OllamaTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "gateway_timeout", "message": exc.message, "detail": exc.detail},
        ) from exc
    except OllamaError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "inference_error", "message": exc.message, "detail": exc.detail},
        ) from exc


def _handle_chat_stream(
    chat_req: ChatRequest,
    client: OllamaClient,
) -> StreamingResponse:
    """Format streamed tokens as Server-Sent Events (SSE)."""

    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for chunk in client.chat_stream(chat_req):
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
        except OllamaHardwareLimitError as exc:
            error_payload = {
                "error": "hardware_limit_exceeded",
                "message": exc.message,
                "detail": exc.detail,
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
        except OllamaModelNotFoundError as exc:
            error_payload = {
                "error": "model_not_installed",
                "message": exc.message,
                "detail": exc.detail,
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
        except OllamaConnectionError as exc:
            error_payload = {
                "error": "service_unavailable",
                "message": exc.message,
                "detail": exc.detail,
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
        except OllamaTimeoutError as exc:
            error_payload = {
                "error": "gateway_timeout",
                "message": exc.message,
                "detail": exc.detail,
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
        except Exception as exc:
            logger.error("Unhandled error in chat SSE stream", exc_info=exc)
            error_payload = {
                "error": "stream_error",
                "message": "Stream interrupted unexpectedly",
                "detail": str(exc),
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
