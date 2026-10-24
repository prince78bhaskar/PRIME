# Changelog

All notable changes to the **P.R.I.M.E.** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0-alpha.phase02] - 2026-10-25

### Added
- **Local Ollama AI Runtime Integration**:
  - `backend/app/core/ollama_client.py`: Asynchronous `OllamaClient` connecting to `http://127.0.0.1:11434`.
  - `backend/app/core/ollama_errors.py`: Typed error domains mapping cleanly to standard HTTP status codes (`OllamaConnectionError` -> 503, `OllamaTimeoutError` -> 504, `OllamaModelNotFoundError` -> 404, `OllamaHardwareLimitError` -> 422).
  - `backend/app/schemas/ollama.py`: Pydantic data schemas for `ChatMessage`, `ChatRequest`, `ChatResponse`, `ChatStreamChunk`, `OllamaHealthResponse`, and `OllamaModelsListResponse`.
  - `backend/app/api/ollama.py`: REST and Server-Sent Events (SSE) streaming API endpoints:
    - `GET /api/v1/ollama/health`: Checks local Ollama connectivity, model availability, and default model presence.
    - `GET /api/v1/ollama/models`: Retrieves inventory of downloaded local models.
    - `POST /api/v1/ollama/chat`: Chat completion supporting single-turn responses and real-time token streaming via SSE (`stream=true`).
- **Hardware Safety Guardrail**:
  - Code-level validator rejecting models exceeding 8B parameters (e.g. 14B, 32B, 70B, 405B) to guarantee the 4GB VRAM ceiling is never violated.
  - Prohibition against automatic model pulls/downloads.
- **Verification & Testing**:
  - `backend/tests/test_ollama_client.py`: 13 unit tests for client methods, guardrails, streaming chunks, and cancellation.
  - `backend/tests/test_ollama_api.py`: 10 integration tests for all API endpoints with mocked Ollama service.
  - `backend/scripts/smoke_test_ollama.py`: Standalone real-model smoke test script verifying live connection, model listing, chat speed, and graceful offline handling.
  - Reached **73 passing automated tests** with 100% pass rate.
  - Authored `docs/phases/PHASE_02.md`.

## [0.2.0-alpha.phase01] - 2026-10-25

### Added
- **Core Backend Architecture**:
  - Initialized Python 3.11+ virtual environment (`.venv`) with pinned `requirements.txt` and `requirements.lock`.
  - `backend/app/main.py`: FastAPI application factory with lifespan startup and graceful shutdown hooks.
  - `backend/app/core/config.py`: Pydantic Settings supporting environment variables and `.env` loading with `PRIME_` prefix.
  - `backend/app/core/logging.py`: Structured JSON and human-readable text log formatters.
  - `backend/app/core/database.py`: SQLite DatabaseManager with WAL mode, schema versioning, and baseline tables (`schema_version`, `app_config`, `audit_log`).
  - `backend/app/api/health.py`: Liveness and readiness probe endpoint (`GET /health`).
  - `backend/tests/`: Initial test suite with 49 tests covering config, database lifecycle, health endpoints, and logging.

## [0.1.0-alpha.phase00] - 2026-10-25

### Added
- **Core Documentation**:
  - `README.md`: Project vision, hardware constraints, VRAM budgeting matrix, tech stack, and subsystem definitions.
  - `AGENTS.md`: Detailed specification for Master Agent and four Specialist Agents (Research, System, Code, Personal) with JSON-RPC schemas and tool permission matrices.
  - `PROJECT_STATE.md`: Real-time status tracker, active milestones, risk register, and hand-off pointers.
  - `TASKS.md`: Formal task ID scheme (`TASK-<PHASE>-<CATEGORY>-<INDEX>`), task statuses, acceptance criteria, and complete Mermaid dependency graph across Phases 00 through 07.
  - `DECISIONS.md`: 9 Architectural Decision Records (ADRs) covering offline sovereignty, 4GB VRAM hardware bounds, FastAPI, React/Vite, Master-Specialist topology, voice pipeline, embedded RAG, 3-tier HITL safety, and future fine-tuning dataset curation.
  - `docs/phases/PHASE_00.md`: Comprehensive Phase 00 blueprint, execution log, directory architecture, and verification checklist.
- **Repository Groundwork**:
  - Initialized Git repository.
  - Created `.gitignore` configured for Python, Node.js, Ollama/models, vector stores, and local data files.

### Architectural Commitments
- Bound maximum primary model VRAM footprint to 2.2 GB (using quantized 3B models such as `qwen2.5:3b-instruct` or `llama3.2:3b-instruct`) on the target 4GB VRAM NVIDIA GPU.
- Enforced offline-first operation with zero reliance on cloud APIs.
- Established 3-Tier security model for controlled computer tools with mandatory Human-in-the-Loop (HITL) approval for destructive or state-changing actions.
