"""
Integration tests for P.R.I.M.E. Ollama API endpoints.

Covers:
- GET /api/v1/ollama/health
- GET /api/v1/ollama/models
- POST /api/v1/ollama/chat (non-streaming & streaming)
- Error handling (503 Service Unavailable, 404 Model Not Found, 422 Hardware Limit, 504 Timeout)
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.ollama import get_ollama_client
from app.core.config import Settings
from app.core.ollama_client import OllamaClient
from app.core.ollama_errors import (
    OllamaConnectionError,
    OllamaHardwareLimitError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from app.main import create_app
from app.schemas.ollama import (
    ChatMessage,
    ChatResponse,
    ChatStreamChunk,
    OllamaHealthResponse,
    OllamaModelInfo,
)


@pytest.fixture
def mock_ollama_client() -> AsyncMock:
    """Fixture providing a mocked OllamaClient."""
    client = AsyncMock(spec=OllamaClient)
    client.base_url = "http://127.0.0.1:11434"
    client.default_model = "qwen2.5:3b-instruct-q4_K_M"
    client.timeout_seconds = 30.0
    return client


@pytest.fixture
def app_with_mock_client(test_settings: Settings, mock_ollama_client: AsyncMock):
    """Create test FastAPI application with mocked OllamaClient."""
    app = create_app(settings=test_settings)
    app.state.ollama_client = mock_ollama_client
    app.dependency_overrides[get_ollama_client] = lambda: mock_ollama_client
    return app


class TestOllamaHealthAPI:
    """Tests for GET /api/v1/ollama/health."""

    def test_health_connected(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.check_health.return_value = OllamaHealthResponse(
            status="connected",
            base_url="http://127.0.0.1:11434",
            default_model="qwen2.5:3b-instruct-q4_K_M",
            is_connected=True,
            is_default_model_installed=True,
            available_models=["qwen2.5:3b-instruct-q4_K_M"],
            error=None,
        )

        with TestClient(app_with_mock_client) as client:
            resp = client.get("/api/v1/ollama/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "connected"
            assert data["is_connected"] is True
            assert data["is_default_model_installed"] is True
            assert "qwen2.5:3b-instruct-q4_K_M" in data["available_models"]

    def test_health_unavailable(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.check_health.return_value = OllamaHealthResponse(
            status="unavailable",
            base_url="http://127.0.0.1:11434",
            default_model="qwen2.5:3b-instruct-q4_K_M",
            is_connected=False,
            is_default_model_installed=False,
            available_models=[],
            error="Connection refused at http://127.0.0.1:11434",
        )

        with TestClient(app_with_mock_client) as client:
            resp = client.get("/api/v1/ollama/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "unavailable"
            assert data["is_connected"] is False
            assert "Connection refused" in data["error"]


class TestOllamaModelsAPI:
    """Tests for GET /api/v1/ollama/models."""

    def test_list_models_success(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.list_models.return_value = [
            OllamaModelInfo(
                name="qwen2.5:3b-instruct-q4_K_M",
                size_bytes=2100000000,
                modified_at="2026-10-25T00:00:00Z",
                digest="sha256:abc",
            )
        ]

        with TestClient(app_with_mock_client) as client:
            resp = client.get("/api/v1/ollama/models")
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 1
            assert data["models"][0]["name"] == "qwen2.5:3b-instruct-q4_K_M"

    def test_list_models_service_unavailable(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.list_models.side_effect = OllamaConnectionError(
            base_url="http://127.0.0.1:11434"
        )

        with TestClient(app_with_mock_client) as client:
            resp = client.get("/api/v1/ollama/models")
            assert resp.status_code == 503
            data = resp.json()
            assert data["detail"]["error"] == "service_unavailable"


class TestOllamaChatAPI:
    """Tests for POST /api/v1/ollama/chat."""

    def test_chat_non_streaming_success(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.chat.return_value = ChatResponse(
            model="qwen2.5:3b-instruct-q4_K_M",
            message=ChatMessage(
                role="assistant",
                content="P.R.I.M.E. is operational and running locally.",
            ),
            done=True,
            total_duration_ms=450.0,
            eval_count=9,
            prompt_eval_count=5,
        )

        payload = {
            "messages": [{"role": "user", "content": "Status report"}],
            "stream": False,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["model"] == "qwen2.5:3b-instruct-q4_K_M"
            assert data["message"]["role"] == "assistant"
            assert "P.R.I.M.E. is operational" in data["message"]["content"]
            assert data["eval_count"] == 9

    def test_chat_streaming_success(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        async def mock_stream_gen(chat_req):
            yield ChatStreamChunk(
                model="qwen2.5:3b",
                message=ChatMessage(role="assistant", content="Hello "),
                done=False,
            )
            yield ChatStreamChunk(
                model="qwen2.5:3b",
                message=ChatMessage(role="assistant", content="User!"),
                done=True,
                eval_count=2,
            )

        mock_ollama_client.chat_stream.side_effect = mock_stream_gen

        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            text = resp.text
            assert "data: " in text
            assert "[DONE]" in text
            assert "Hello " in text
            assert "User!" in text

    def test_chat_model_not_installed_returns_404(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.chat.side_effect = OllamaModelNotFoundError(
            model="nonexistent:3b",
            available_models=["qwen2.5:3b"],
        )

        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "nonexistent:3b",
            "stream": False,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 404
            data = resp.json()
            assert data["detail"]["error"] == "model_not_installed"
            assert "nonexistent:3b" in data["detail"]["detail"]

    def test_chat_oversized_model_returns_422(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.chat.side_effect = OllamaHardwareLimitError(
            model="llama3.1:70b",
            reason="Exceeds 4GB VRAM ceiling",
        )

        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "llama3.1:70b",
            "stream": False,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 422
            data = resp.json()
            assert data["detail"]["error"] == "hardware_limit_exceeded"

    def test_chat_service_unavailable_returns_503(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.chat.side_effect = OllamaConnectionError(
            base_url="http://127.0.0.1:11434"
        )

        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 503
            data = resp.json()
            assert data["detail"]["error"] == "service_unavailable"

    def test_chat_timeout_returns_504(
        self,
        app_with_mock_client,
        mock_ollama_client: AsyncMock,
    ) -> None:
        mock_ollama_client.chat.side_effect = OllamaTimeoutError(
            timeout_seconds=30.0
        )

        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": False,
        }

        with TestClient(app_with_mock_client) as client:
            resp = client.post("/api/v1/ollama/chat", json=payload)
            assert resp.status_code == 504
            data = resp.json()
            assert data["detail"]["error"] == "gateway_timeout"
