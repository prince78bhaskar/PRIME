# P.R.I.M.E. Backend

Backend service for the **P.R.I.M.E. (Personal Responsive Intelligent Multi-Agent Environment)** system.

Built with **Python 3.11+**, **FastAPI**, **SQLite (WAL mode)**, and native **Ollama Local AI Runtime Integration**.

---

## Quick Start (Windows)

### Prerequisites
- **Python 3.11 or later** installed and available on `PATH`
- **Git** installed
- **Ollama** installed locally (https://ollama.ai) for local model inference

### 1. Create Virtual Environment
```powershell
cd backend
python -m venv .venv
```

### 2. Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
pip install --no-build-isolation -e . --no-deps
```

### 4. Configure Environment
```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env with your preferred settings (defaults work out of the box)
```

### 5. Run Test Suite
```powershell
pytest
```

### 6. Run Ollama Smoke Test
```powershell
# Real-model smoke test (probes local Ollama at 127.0.0.1:11434)
python scripts/smoke_test_ollama.py
```

### 7. Start the Server
```powershell
# Development mode with auto-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 8. Verify Endpoints
```powershell
# Application health check
curl http://127.0.0.1:8000/health

# Ollama local runtime health check
curl http://127.0.0.1:8000/api/v1/ollama/health

# List installed local models
curl http://127.0.0.1:8000/api/v1/ollama/models
```

---

## Local AI Runtime (Ollama)

P.R.I.M.E. routes 100% of model inference through the local Ollama daemon (`http://127.0.0.1:11434`).
* **Zero Cloud Fallback**: No third-party AI keys or external API dependencies are supported or permitted.
* **4GB VRAM Safety Ceiling**: Explicitly oversized model tags are rejected early, then Ollama's local parameter-count metadata must confirm a model is at most 8B. Models above 8B or without verifiable metadata are rejected with HTTP 422.
* **Recommended Models**: `qwen2.5:3b-instruct-q4_K_M` (default), `llama3.2:3b-instruct`, or `phi3.5:mini`.

### Ollama API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Core backend liveness and database readiness |
| `GET` | `/api/v1/ollama/health` | Local Ollama connection status and model availability |
| `GET` | `/api/v1/ollama/models` | List installed models in local Ollama |
| `POST` | `/api/v1/ollama/chat` | Chat completion (non-streaming or SSE streaming via `stream=true`) |

### Example Chat Request

```powershell
# Non-streaming chat completion
curl -X POST http://127.0.0.1:8000/api/v1/ollama/chat `
  -H "Content-Type: application/json" `
  -d '{"messages": [{"role": "user", "content": "Hello P.R.I.M.E."}], "stream": false}'

# Streaming chat completion (Server-Sent Events)
curl -X POST http://127.0.0.1:8000/api/v1/ollama/chat `
  -H "Content-Type: application/json" `
  -d '{"messages": [{"role": "user", "content": "Introduce yourself."}], "stream": true}'
```

---

## Local Voice Interaction

Voice processing is an optional local pipeline, separate from the Ollama chat endpoint. The browser requests microphone permission only when the user presses and holds the microphone button. Audio is posted only to a loopback backend and is not sent to external speech services. Push-to-talk is supported; wake-word and always-on listening are not.

Install the optional voice dependencies and download the local models before going offline. Instructions, model sources, configuration, endpoint contracts, and the end-to-end acceptance checklist are in [Phase 04](../docs/phases/PHASE_04.md).

The voice endpoints are `GET /api/v1/voice/status`, `POST /api/v1/voice/transcribe`, and `POST /api/v1/voice/synthesize`. English (`en`) and Hindi (`hi`) use Faster-Whisper and Piper models configured independently through `PRIME_VOICE_*` variables.

---

## Project Structure

```
backend/
├── pyproject.toml               # Project metadata, dependencies, tool config
├── requirements.txt             # Pinned dependency manifest
├── requirements.lock            # Exact dependency lockfile
├── .env.example                 # Template for environment variables
├── README.md                    # This file
├── app/
│   ├── __init__.py              # Package marker
│   ├── main.py                  # FastAPI application factory & lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py            # GET /health endpoint
│   │   └── ollama.py            # Local Ollama REST & SSE streaming endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings (env var management)
│   │   ├── database.py          # SQLite WAL database manager
│   │   ├── logging.py           # Structured JSON/text logging
│   │   ├── ollama_client.py     # Async HTTP Ollama client with guardrails
│   │   └── ollama_errors.py     # Custom exceptions (503, 504, 404, 422)
│   └── schemas/
│       ├── __init__.py
│       └── ollama.py            # Pydantic models for chat, streaming, telemetry
├── scripts/
│   └── smoke_test_ollama.py     # Real-model smoke test script
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures (settings, db, client)
    ├── test_config.py           # Configuration tests
    ├── test_database.py         # Database lifecycle tests
    ├── test_health.py           # Health endpoint & startup tests
    ├── test_logging.py          # Logging formatter tests
    ├── test_ollama_client.py    # Ollama client unit & guardrail tests
    └── test_ollama_api.py       # Ollama API integration tests
```

---

## Configuration Reference

All settings use the `PRIME_` environment variable prefix.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PRIME_APP_NAME` | `P.R.I.M.E.` | Application display name |
| `PRIME_ENVIRONMENT` | `development` | Runtime environment (`development`, `testing`, `production`) |
| `PRIME_DEBUG` | `false` | Enable debug mode and OpenAPI `/docs` |
| `PRIME_HOST` | `127.0.0.1` | Server bind host |
| `PRIME_PORT` | `8000` | Server bind port |
| `PRIME_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PRIME_LOG_FORMAT` | `json` | Log output format (`json` or `text`) |
| `PRIME_DB_PATH` | `../data/memory/prime.db` | SQLite database file location |
| `PRIME_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama daemon base URL |
| `PRIME_OLLAMA_MODEL` | `qwen2.5:3b-instruct-q4_K_M` | Default Ollama model tag |
| `PRIME_OLLAMA_TIMEOUT_SECONDS` | `30` | Request timeout in seconds |
