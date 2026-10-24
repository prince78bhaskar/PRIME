"""
P.R.I.M.E. Ollama Data Models & Schemas.

Pydantic models for chat requests, streaming chunks, health telemetry,
and error responses for local Ollama interactions.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message in a conversation turn."""

    role: Literal["system", "user", "assistant"] = Field(
        ...,
        description="Role of the message author",
    )
    content: str = Field(
        ...,
        description="Text content of the message",
    )


class ChatRequest(BaseModel):
    """Request payload for chat generation."""

    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="List of conversation turns",
    )
    model: str | None = Field(
        default=None,
        description="Target model name. If omitted, uses server default model.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=4096,
        description="Maximum tokens to generate (capped at 4096 to prevent VRAM overflow)",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream response chunks via Server-Sent Events",
    )


class ChatResponse(BaseModel):
    """Complete response payload for non-streaming chat generation."""

    model: str = Field(..., description="Model name used for generation")
    message: ChatMessage = Field(..., description="Assistant reply message")
    done: bool = Field(default=True, description="Generation completion flag")
    total_duration_ms: float | None = Field(
        default=None,
        description="Total processing duration in milliseconds",
    )
    eval_count: int | None = Field(
        default=None,
        description="Number of tokens generated in response",
    )
    prompt_eval_count: int | None = Field(
        default=None,
        description="Number of tokens in prompt",
    )


class ChatStreamChunk(BaseModel):
    """Individual streamed delta token/chunk from Ollama."""

    model: str = Field(..., description="Model name")
    message: ChatMessage = Field(..., description="Message delta")
    done: bool = Field(default=False, description="Whether this is the terminal chunk")
    total_duration_ms: float | None = Field(default=None, description="Elapsed duration when done")
    eval_count: int | None = Field(default=None, description="Total tokens generated when done")


class OllamaHealthResponse(BaseModel):
    """Health check status report for the local Ollama daemon."""

    status: Literal["connected", "unavailable", "degraded"] = Field(
        ...,
        description="Ollama connection state",
    )
    base_url: str = Field(..., description="Target Ollama service base URL")
    default_model: str = Field(..., description="Configured default model tag")
    is_connected: bool = Field(..., description="Whether ping to Ollama succeeded")
    is_default_model_installed: bool = Field(
        default=False,
        description="Whether default model is downloaded locally",
    )
    available_models: list[str] = Field(
        default_factory=list,
        description="List of model tags installed in local Ollama",
    )
    error: str | None = Field(
        default=None,
        description="Error message if Ollama is unreachable",
    )


class OllamaModelInfo(BaseModel):
    """Metadata describing an installed local model."""

    name: str = Field(..., description="Model tag (e.g. qwen2.5:3b-instruct-q4_K_M)")
    size_bytes: int | None = Field(default=None, description="Size on disk in bytes")
    modified_at: str | None = Field(default=None, description="Last modification timestamp")
    digest: str | None = Field(default=None, description="SHA256 model digest")


class OllamaModelsListResponse(BaseModel):
    """List of all installed models in local Ollama."""

    models: list[OllamaModelInfo] = Field(
        default_factory=list,
        description="Installed local models",
    )
    count: int = Field(default=0, description="Count of installed models")


class ErrorResponse(BaseModel):
    """Standardized error payload returned across all API endpoints."""

    error: str = Field(..., description="Error category code")
    message: str = Field(..., description="Human-readable error summary")
    detail: str | None = Field(default=None, description="Detailed diagnosis or resolution step")
