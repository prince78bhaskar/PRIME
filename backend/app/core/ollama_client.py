"""
P.R.I.M.E. Local Ollama Client.

Provides an asynchronous HTTP client interface to the local Ollama runtime,
implementing chat completion, streaming tokens, health diagnostics, model checks,
and hardware safety bounds to preserve the 4GB VRAM ceiling.
"""

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.ollama_errors import (
    OllamaConnectionError,
    OllamaError,
    OllamaHardwareLimitError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from app.schemas.ollama import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    OllamaHealthResponse,
    OllamaModelInfo,
)

logger = logging.getLogger(__name__)

# Pattern detecting models that exceed the 4GB VRAM / 16GB RAM budget.
# Models with >= 13B, 14B, 30B, 32B, 70B, 72B, 405B parameters are rejected.
_DISALLOWED_MODEL_PATTERN = re.compile(
    r"\b(1[3-9]b|[2-9]\d+b|\d{3,}b)\b",
    re.IGNORECASE,
)


class OllamaClient:
    """Async client for interacting with the local Ollama service.

    Attributes:
        base_url: Ollama daemon base URL (e.g. 'http://127.0.0.1:11434').
        default_model: Default model tag to use if none is provided in the request.
        timeout_seconds: Default request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        default_model: str = "qwen2.5:3b-instruct-q4_K_M",
        timeout_seconds: float = 30.0,
        max_allowed_param_billions: float = 8.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.max_allowed_param_billions = max_allowed_param_billions
        self._custom_client = http_client
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Return or lazily create the underlying httpx AsyncClient."""
        if self._custom_client is not None:
            return self._custom_client
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seconds, connect=5.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def validate_model_safety(self, model: str) -> None:
        """Ensure the requested model conforms to local 4GB VRAM constraints.

        Raises:
            OllamaHardwareLimitError: If model exceeds hardware capacity.
        """
        if _DISALLOWED_MODEL_PATTERN.search(model):
            raise OllamaHardwareLimitError(
                model=model,
                reason=(
                    f"Model '{model}' indicates parameter size exceeding {self.max_allowed_param_billions}B, "
                    "which exceeds the 4GB GPU VRAM allocation limit."
                ),
            )

    async def check_health(self) -> OllamaHealthResponse:
        """Inspect the local Ollama daemon connectivity and model inventory.

        Returns:
            OllamaHealthResponse detailing connection state and available models.
        """
        client = await self.get_client()
        try:
            response = await client.get("/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                is_default_installed = any(
                    self.default_model in m or m in self.default_model
                    for m in models
                )
                return OllamaHealthResponse(
                    status="connected",
                    base_url=self.base_url,
                    default_model=self.default_model,
                    is_connected=True,
                    is_default_model_installed=is_default_installed,
                    available_models=models,
                    error=None,
                )
            else:
                return OllamaHealthResponse(
                    status="degraded",
                    base_url=self.base_url,
                    default_model=self.default_model,
                    is_connected=False,
                    available_models=[],
                    error=f"Ollama returned HTTP status {response.status_code}",
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.warning("Ollama service unreachable", extra={"base_url": self.base_url})
            return OllamaHealthResponse(
                status="unavailable",
                base_url=self.base_url,
                default_model=self.default_model,
                is_connected=False,
                available_models=[],
                error=f"Connection refused at {self.base_url}. Ensure Ollama is running locally.",
            )
        except httpx.TimeoutException:
            logger.warning("Ollama health check timed out", extra={"base_url": self.base_url})
            return OllamaHealthResponse(
                status="unavailable",
                base_url=self.base_url,
                default_model=self.default_model,
                is_connected=False,
                available_models=[],
                error=f"Health check timed out after 5.0s at {self.base_url}.",
            )
        except Exception as exc:
            logger.error("Unexpected error checking Ollama health", exc_info=exc)
            return OllamaHealthResponse(
                status="unavailable",
                base_url=self.base_url,
                default_model=self.default_model,
                is_connected=False,
                available_models=[],
                error=str(exc),
            )

    async def list_models(self) -> list[OllamaModelInfo]:
        """Fetch all installed models in the local Ollama instance.

        Raises:
            OllamaConnectionError: If Ollama service is unreachable.
            OllamaTimeoutError: If the request times out.
        """
        client = await self.get_client()
        try:
            response = await client.get("/api/tags")
            if response.status_code != 200:
                raise OllamaError(f"Failed to list models: HTTP {response.status_code}")
            data = response.json()
            results = []
            for item in data.get("models", []):
                results.append(
                    OllamaModelInfo(
                        name=item.get("name", ""),
                        size_bytes=item.get("size"),
                        modified_at=item.get("modified_at"),
                        digest=item.get("digest"),
                    )
                )
            return results
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaConnectionError(base_url=self.base_url) from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(timeout_seconds=self.timeout_seconds) from exc

    async def chat(
        self,
        request: ChatRequest,
        timeout: float | None = None,
    ) -> ChatResponse:
        """Execute a non-streaming chat completion with local Ollama.

        Args:
            request: ChatRequest containing messages, model, and generation options.
            timeout: Optional per-request timeout override.

        Returns:
            ChatResponse with full message and token metrics.

        Raises:
            OllamaHardwareLimitError: If model exceeds 4GB VRAM safety ceiling.
            OllamaConnectionError: If Ollama is unreachable.
            OllamaTimeoutError: If generation times out.
            OllamaModelNotFoundError: If requested model is not installed.
        """
        target_model = request.model or self.default_model
        self.validate_model_safety(target_model)

        req_timeout = timeout or self.timeout_seconds
        client = await self.get_client()

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": [m.model_dump() for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            response = await client.post(
                "/api/chat",
                json=payload,
                timeout=req_timeout,
            )

            if response.status_code == 404:
                # Model not found in Ollama
                available_models = [m.name for m in (await self._safe_list_models())]
                raise OllamaModelNotFoundError(
                    model=target_model,
                    available_models=available_models,
                )
            elif response.status_code != 200:
                raise OllamaError(
                    message=f"Ollama chat error (HTTP {response.status_code})",
                    detail=response.text,
                )

            data = response.json()
            raw_msg = data.get("message", {})
            total_duration_ns = data.get("total_duration")
            total_duration_ms = (
                round(total_duration_ns / 1_000_000, 2)
                if total_duration_ns is not None
                else None
            )

            return ChatResponse(
                model=data.get("model", target_model),
                message=ChatMessage(
                    role=raw_msg.get("role", "assistant"),
                    content=raw_msg.get("content", ""),
                ),
                done=data.get("done", True),
                total_duration_ms=total_duration_ms,
                eval_count=data.get("eval_count"),
                prompt_eval_count=data.get("prompt_eval_count"),
            )

        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaConnectionError(base_url=self.base_url) from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(timeout_seconds=req_timeout) from exc

    async def chat_stream(
        self,
        request: ChatRequest,
        timeout: float | None = None,
    ) -> AsyncIterator[ChatStreamChunk]:
        """Stream chat completion chunks from local Ollama via NDJSON / SSE.

        Yields:
            ChatStreamChunk objects containing incremental delta text.

        Raises:
            OllamaHardwareLimitError: If model exceeds 4GB VRAM safety ceiling.
            OllamaConnectionError: If Ollama is unreachable.
            OllamaTimeoutError: If connection or first chunk times out.
            OllamaModelNotFoundError: If requested model is not installed.
        """
        target_model = request.model or self.default_model
        self.validate_model_safety(target_model)

        req_timeout = timeout or self.timeout_seconds
        client = await self.get_client()

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": [m.model_dump() for m in request.messages],
            "stream": True,
            "options": {
                "temperature": request.temperature,
            },
        }
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
                timeout=httpx.Timeout(req_timeout, connect=5.0),
            ) as response:
                if response.status_code == 404:
                    available = [m.name for m in (await self._safe_list_models())]
                    raise OllamaModelNotFoundError(model=target_model, available_models=available)
                elif response.status_code != 200:
                    error_text = await response.aread()
                    raise OllamaError(
                        message=f"Ollama stream error (HTTP {response.status_code})",
                        detail=error_text.decode("utf-8", errors="replace"),
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk_data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    raw_msg = chunk_data.get("message", {})
                    total_ns = chunk_data.get("total_duration")
                    total_ms = round(total_ns / 1_000_000, 2) if total_ns else None

                    yield ChatStreamChunk(
                        model=chunk_data.get("model", target_model),
                        message=ChatMessage(
                            role=raw_msg.get("role", "assistant"),
                            content=raw_msg.get("content", ""),
                        ),
                        done=chunk_data.get("done", False),
                        total_duration_ms=total_ms,
                        eval_count=chunk_data.get("eval_count"),
                    )

        except asyncio.CancelledError:
            logger.info("Chat stream was cancelled by client/caller")
            raise
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaConnectionError(base_url=self.base_url) from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(timeout_seconds=req_timeout) from exc

    async def _safe_list_models(self) -> list[OllamaModelInfo]:
        """Internal helper to fetch models without raising, for diagnostic context."""
        try:
            return await self.list_models()
        except Exception:
            return []
