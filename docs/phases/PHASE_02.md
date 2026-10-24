# Phase 02: Local AI Runtime Integration

**Status**: **COMPLETED**  
**Phase Date**: 2026-10-25  
**Deliverable**: Local Ollama Model Runtime Integration with FastAPI Backend, Streaming Support, Hardware Guardrails, and Offline Verification.

---

## 1. Executive Summary

Phase 02 connects the P.R.I.M.E. FastAPI backend to the sovereign local model runner (**Ollama**) residing at `http://127.0.0.1:11434`. 

Model inference is restricted **100% to the local machine**. No third-party cloud APIs (OpenAI, Anthropic, Google Cloud) or external API keys are used, ensuring total data sovereignty and air-gapped capability.

To respect the target hardware bounds (**16 GB System RAM, NVIDIA GPU with 4 GB VRAM**), model parameter checks explicitly reject large models (>8B parameters) with `HTTP 422 Unprocessable Content` before any inference attempt can trigger an Out-of-Memory (OOM) crash.

---

## 2. Architecture & Subsystems

```
                                +---------------------------+
                                |  FastAPI Client Request   |
                                +-------------+-------------+
                                              |
                                              v
                                +---------------------------+
                                |  /api/v1/ollama/chat      |
                                |  /api/v1/ollama/health    |
                                |  /api/v1/ollama/models    |
                                +-------------+-------------+
                                              |
                                              v
+---------------------------------------------------------------------------------------+
| OllamaClient (app/core/ollama_client.py)                                              |
|                                                                                       |
|   1. Hardware Guardrail: Check model against parameter budget (reject >=13B/14B/70B)  |
|   2. Timeout Enforcement: Per-request or global configurable timeout                  |
|   3. Cancellation Handling: Graceful exit on client disconnect                        |
|   4. Error Translation: httpx exceptions -> typed OllamaError domains                 |
+---------------------------------------------+-----------------------------------------+
                                              |
                                              v (HTTP async over 127.0.0.1:11434)
                                +---------------------------+
                                |   Local Ollama Service    |
                                | (qwen2.5:3b / llama3.2:3b)|
                                +---------------------------+
```

---

## 3. Endpoints Implemented

### 1. `GET /api/v1/ollama/health`
* **Purpose**: Inspects connectivity to local Ollama daemon and checks whether the default model is downloaded.
* **Response**:
  ```json
  {
    "status": "connected",
    "base_url": "http://127.0.0.1:11434",
    "default_model": "qwen2.5:3b-instruct-q4_K_M",
    "is_connected": true,
    "is_default_model_installed": false,
    "available_models": [],
    "error": null
  }
  ```
* **Offline / Unavailable Behavior**: Returns `status="unavailable"`, `is_connected=false`, with a clear diagnostic message guiding the user to start `ollama serve`. Never raises an unhandled 500 error.

### 2. `GET /api/v1/ollama/models`
* **Purpose**: Retrieves inventory of all models downloaded in the local Ollama instance.
* **Error**: Returns `503 Service Unavailable` if Ollama is not running.

### 3. `POST /api/v1/ollama/chat`
* **Purpose**: Executes chat generation. Supports both standard JSON responses and Server-Sent Events (SSE) streaming.
* **Streaming Protocol**: When `stream=true`, responses are delivered with `media_type="text/event-stream"` using format:
  ```
  data: {"model":"qwen2.5:3b","message":{"role":"assistant","content":"token"},"done":false}

  data: [DONE]
  ```

---

## 4. Error Handling & Security Matrix

| Failure Mode | Internal Exception | HTTP Status | Response Payload |
| :--- | :--- | :---: | :--- |
| **Ollama Service Offline** | `OllamaConnectionError` | `503` | `{"error": "service_unavailable", "message": "Local Ollama service is unreachable"}` |
| **Request Timeout** | `OllamaTimeoutError` | `504` | `{"error": "gateway_timeout", "message": "Inference request exceeded timeout"}` |
| **Model Not Downloaded** | `OllamaModelNotFoundError` | `404` | `{"error": "model_not_installed", "message": "Model '...' is not installed"}` |
| **Model Exceeds 4GB VRAM** | `OllamaHardwareLimitError`| `422` | `{"error": "hardware_limit_exceeded", "message": "Model violates hardware safety constraints"}` |
| **Client Disconnect** | `asyncio.CancelledError` | `N/A` | Stream terminates cleanly; underlying connection closed without connection leak. |

---

## 5. Verification & Testing

### 1. Automated Test Suite
* **Unit Tests**: [`backend/tests/test_ollama_client.py`](../../backend/tests/test_ollama_client.py)
  - 13 test cases covering configuration, hardware safety guardrails, health check parsing, model listing, chat generation, streaming chunk parsing, and error mappings.
* **Integration Tests**: [`backend/tests/test_ollama_api.py`](../../backend/tests/test_ollama_api.py)
  - 10 test cases verifying endpoint responses, mock injection, SSE streaming headers, and error codes (503, 504, 404, 422).
* **Total Backend Tests**: **73 passed in 0.73s** (100% pass rate).

### 2. Standalone Smoke Test Script
* Implemented in [`backend/scripts/smoke_test_ollama.py`](../../backend/scripts/smoke_test_ollama.py).
* Verified against running local Ollama instance:
  - Connectivity probe: **PASS**
  - Model inventory inspection: **PASS**
  - Hardware constraint validation: **PASS**
  - Offline / missing model graceful notice: **PASS**
