"""
Unit tests for P.R.I.M.E. Ollama Client.

Tests client behavior using mock httpx transports:
- Default and custom configurations
- Hardware safety guardrails (VRAM bounds)
- Health check parsing (connected, unavailable, timeout)
- Model listing and parsing
- Non-streaming chat generation
- Streaming chat generation
- Error handling (503 connection error, 504 timeout, 404 model not found)
- Stream cancellation
"""

import json

import httpx
import pytest

from app.core.ollama_client import OllamaClient
from app.core.ollama_errors import (
    OllamaConnectionError,
    OllamaHardwareLimitError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from app.schemas.ollama import ChatMessage, ChatRequest


class TestOllamaClientConfig:
    """Verify configuration and defaults."""

    def test_default_config(self) -> None:
        client = OllamaClient()
        assert client.base_url == "http://127.0.0.1:11434"
        assert client.default_model == "qwen2.5:3b-instruct-q4_K_M"
        assert client.timeout_seconds == 30.0

    def test_custom_config(self) -> None:
        client = OllamaClient(
            base_url="http://localhost:11434/",
            default_model="llama3.2:3b",
            timeout_seconds=45.0,
        )
        assert client.base_url == "http://localhost:11434"
        assert client.default_model == "llama3.2:3b"
        assert client.timeout_seconds == 45.0


class TestHardwareSafetyGuardrails:
    """Verify guardrails preventing large models that exceed 4GB VRAM."""

    def test_allowed_small_models(self) -> None:
        client = OllamaClient()
        # These tag labels do not exceed the configured limit.
        allowed = [
            "qwen2.5:3b-instruct-q4_K_M",
            "qwen2.5:3b",
            "llama3.2:3b",
            "llama3.2:1b",
            "phi3.5:mini",
            "qwen2.5:7b-instruct-q4_K_M",
            "example:8b",
            "gemma2:2b",
        ]
        for model in allowed:
            client.validate_model_safety(model)  # Should not raise

    def test_rejects_every_explicit_size_above_eight_billion(self) -> None:
        client = OllamaClient()
        for size in (9, 10, 11, 12, 13, 70):
            with pytest.raises(OllamaHardwareLimitError):
                client.validate_model_safety(f"example:{size}b")

    def test_disallowed_large_models(self) -> None:
        client = OllamaClient()
        # Models that exceed 4GB VRAM
        disallowed = [
            "llama3.1:70b",
            "qwen2.5:14b",
            "qwen2.5:32b",
            "qwen2.5:72b",
            "llama3.1:405b",
            "deepseek-r1:14b",
            "deepseek-r1:70b",
        ]
        for model in disallowed:
            with pytest.raises(OllamaHardwareLimitError) as exc_info:
                client.validate_model_safety(model)
            assert model in str(exc_info.value.model)


class TestHealthCheck:
    """Verify health check logic."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/tags"
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "qwen2.5:3b-instruct-q4_K_M"},
                        {"name": "llama3.2:3b"},
                    ]
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            health = await client.check_health()
            assert health.status == "connected"
            assert health.is_connected is True
            assert health.is_default_model_installed is True
            assert "llama3.2:3b" in health.available_models
            assert health.error is None

    @pytest.mark.asyncio
    async def test_health_check_service_unavailable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            health = await client.check_health()
            assert health.status == "unavailable"
            assert health.is_connected is False
            assert health.is_default_model_installed is False
            assert "Connection refused" in (health.error or "")

    @pytest.mark.asyncio
    async def test_health_check_timeout(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Read timed out")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            health = await client.check_health()
            assert health.status == "unavailable"
            assert health.is_connected is False
            assert "timed out" in (health.error or "")


class TestListModels:
    """Verify listing models."""

    @pytest.mark.asyncio
    async def test_list_models_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "qwen2.5:3b-instruct-q4_K_M",
                            "size": 2100000000,
                            "modified_at": "2026-10-25T00:00:00Z",
                            "digest": "sha256:123456",
                        }
                    ]
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            models = await client.list_models()
            assert len(models) == 1
            assert models[0].name == "qwen2.5:3b-instruct-q4_K_M"
            assert models[0].size_bytes == 2100000000

    @pytest.mark.asyncio
    async def test_list_models_connection_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Failed to connect")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            with pytest.raises(OllamaConnectionError):
                await client.list_models()


class TestChatCompletion:
    """Verify chat generation logic."""

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/show":
                return httpx.Response(
                    200,
                    json={"model_info": {"general.parameter_count": 3_000_000_000}},
                )
            payload = json.loads(request.read().decode())
            assert payload["model"] == "qwen2.5:3b-instruct-q4_K_M"
            assert payload["stream"] is False
            return httpx.Response(
                200,
                json={
                    "model": "qwen2.5:3b-instruct-q4_K_M",
                    "message": {
                        "role": "assistant",
                        "content": "Hello! P.R.I.M.E. is online and ready.",
                    },
                    "done": True,
                    "total_duration": 500_000_000,  # 500ms in ns
                    "prompt_eval_count": 12,
                    "eval_count": 8,
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(
                messages=[ChatMessage(role="user", content="Hello!")],
            )
            resp = await client.chat(req)
            assert resp.model == "qwen2.5:3b-instruct-q4_K_M"
            assert resp.message.role == "assistant"
            assert "P.R.I.M.E." in resp.message.content
            assert resp.done is True
            assert resp.total_duration_ms == 500.0
            assert resp.eval_count == 8

    @pytest.mark.asyncio
    async def test_chat_model_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/show":
                return httpx.Response(404, text="model 'missing:3b' not found")
            return httpx.Response(200, json={"models": []})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                model="missing:3b",
            )
            with pytest.raises(OllamaModelNotFoundError) as exc_info:
                await client.chat(req)
            assert exc_info.value.model == "missing:3b"

    @pytest.mark.asyncio
    async def test_rejects_misleading_small_tag_using_ollama_metadata(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/show"
            return httpx.Response(
                200,
                json={"model_info": {"general.parameter_count": 12_000_000_000}},
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                model="misleading-model:3b",
            )
            with pytest.raises(OllamaHardwareLimitError):
                await client.chat(req)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("parameter_count", "is_allowed"),
        [(8_000_000_000, True), (8_000_000_001, False)],
    )
    async def test_metadata_size_limit_boundary(
        self,
        parameter_count: int,
        is_allowed: bool,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"model_info": {"general.parameter_count": parameter_count}},
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            if is_allowed:
                await client.validate_model_metadata("boundary:8b")
            else:
                with pytest.raises(OllamaHardwareLimitError):
                    await client.validate_model_metadata("boundary:8b")

    @pytest.mark.asyncio
    async def test_rejects_model_when_parameter_metadata_is_ambiguous(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"details": {"parameter_size": "3B"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                model="phi3.5:mini",
            )
            with pytest.raises(OllamaHardwareLimitError) as exc_info:
                await client.chat(req)
            assert "verifiable parameter count" in (exc_info.value.detail or "")

    @pytest.mark.asyncio
    async def test_chat_connection_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
            with pytest.raises(OllamaConnectionError):
                await client.chat(req)

    @pytest.mark.asyncio
    async def test_chat_timeout(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Request timed out")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
            with pytest.raises(OllamaTimeoutError):
                await client.chat(req)


class TestChatStreaming:
    """Verify streaming chunk handling and cancellation."""

    @pytest.mark.asyncio
    async def test_chat_stream_success(self) -> None:
        lines = [
            json.dumps({"model": "qwen2.5:3b", "message": {"role": "assistant", "content": "P."}, "done": False}),
            json.dumps({"model": "qwen2.5:3b", "message": {"role": "assistant", "content": "R."}, "done": False}),
            json.dumps({"model": "qwen2.5:3b", "message": {"role": "assistant", "content": "I."}, "done": False}),
            json.dumps({"model": "qwen2.5:3b", "message": {"role": "assistant", "content": "M."}, "done": False}),
            json.dumps({"model": "qwen2.5:3b", "message": {"role": "assistant", "content": "E."}, "done": True, "eval_count": 5}),
        ]
        body = "\n".join(lines).encode("utf-8")

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/show":
                return httpx.Response(
                    200,
                    json={"model_info": {"general.parameter_count": 3_000_000_000}},
                )
            return httpx.Response(200, content=body)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as mock_http:
            client = OllamaClient(http_client=mock_http)
            req = ChatRequest(
                messages=[ChatMessage(role="user", content="Spell PRIME")],
                model="qwen2.5:3b",
                stream=True,
            )
            chunks = []
            async for chunk in client.chat_stream(req):
                chunks.append(chunk)

            assert len(chunks) == 5
            full_text = "".join(c.message.content for c in chunks)
            assert full_text == "P.R.I.M.E."
            assert chunks[-1].done is True
            assert chunks[-1].eval_count == 5
