# P.R.I.M.E. Architectural Decision Records (ADRs)

This document captures the key architectural and design decisions made for **P.R.I.M.E. (Personal Responsive Intelligent Multi-Agent Environment)**, including the context, considered options, decision outcome, and consequences.

---

## Index of Decisions

- [ADR-001: Local-First and 100% Offline Architecture](#adr-001-local-first-and-100-offline-architecture)
- [ADR-002: Hardware Constraint Strategy (4GB VRAM / 16GB RAM)](#adr-002-hardware-constraint-strategy-4gb-vram--16gb-ram)
- [ADR-003: Backend Framework Selection: FastAPI with WebSockets](#adr-003-backend-framework-selection-fastapi-with-websockets)
- [ADR-004: Frontend Architecture: React + Vite + Tailwind CSS](#adr-004-frontend-architecture-react--vite--tailwind-css)
- [ADR-005: Multi-Agent Topology: Hierarchical Master-Specialist](#adr-005-multi-agent-topology-hierarchical-master-specialist)
- [ADR-006: Local Voice Pipeline: Faster-Whisper + Piper TTS + Silero VAD](#adr-006-local-voice-pipeline-faster-whisper--piper-tts--silero-vad)
- [ADR-007: Embedded Vector Store: LanceDB Embedded](#adr-007-embedded-vector-store-lancedb-embedded)
- [ADR-008: 3-Tier Tool Security & Human-in-the-Loop (HITL) Execution](#adr-008-3-tier-tool-security--human-in-the-loop-hitl-execution)
- [ADR-009: Dataset Curation Pipeline for Future QLoRA Fine-Tuning](#adr-009-dataset-curation-pipeline-for-future-qlora-fine-tuning)

---

## ADR-001: Local-First and 100% Offline Architecture

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
Modern AI assistants predominantly depend on cloud API endpoints (e.g., OpenAI, Anthropic, Google Cloud). This introduces critical dependencies on active internet connectivity, latency variance, recurring API costs, and privacy risks associated with transmitting sensitive user files and personal data to third parties.

### Decision
P.R.I.M.E. will operate entirely locally and offline once initial models and dependencies are downloaded. The core model runtime will be powered by local Ollama serving quantized open-weights models (`qwen2.5:3b`, `llama3.2:3b`). No cloud API keys or external telemetry endpoints will be required or permitted in the core execution path.

### Consequences
* **Positive**: Complete privacy sovereignty, zero API subscription costs, reliable operation in air-gapped environments, consistent latency independent of internet speeds.
* **Negative**: Model reasoning capability is bounded by consumer local hardware rather than 400B+ parameter cloud models.

---

## ADR-002: Hardware Constraint Strategy (4GB VRAM / 16GB RAM)

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
The target host environment is a consumer Windows PC equipped with **16 GB System RAM** and an **NVIDIA GPU with 4 GB VRAM**. Operating within 4 GB VRAM makes it impossible to run large 14B+ models or run multiple models simultaneously (such as a 7B LLM alongside a GPU-resident Whisper model).

### Decision
1. **Model Selection**: Standardize on 4-bit quantized (Q4_K_M) 3B parameter models (e.g. `qwen2.5:3b-instruct` or `llama3.2:3b-instruct`), occupying ~2.0–2.2 GB VRAM.
2. **Context Window Cap**: Enforce context window limits between 2048 and 4096 tokens to prevent VRAM allocation spikes during KV cache generation.
3. **Audio Offloading**: Execute Faster-Whisper on CPU (utilizing CTranslate2 multi-threading) or time-slice GPU usage so that STT and LLM generation do not collide in VRAM. Run Piper TTS purely on CPU.
4. **No Training On-Device**: Do not run fine-tuning or backpropagation passes on this hardware. Focus on inference, retrieval, and dataset curation.

### Consequences
* **Positive**: Reliable execution without CUDA Out-of-Memory (OOM) fatal crashes; snappy token generation rates (30–50 tokens/sec on 3B models).
* **Negative**: Strict limits on simultaneous active contexts and model size.

---

## ADR-003: Backend Framework Selection: FastAPI with WebSockets

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
The backend must orchestrate multiple agents, stream tokens and thoughts in real time, communicate with Ollama, manage audio streams, and handle tool confirmations with low latency.

### Decision
Adopt **Python 3.11+ with FastAPI and Uvicorn**. Utilize asynchronous endpoints (`async`/`await`) for REST APIs and native WebSockets (`/ws/events`) for bidirectional streaming of agent tokens, telemetry, and interactive HITL approvals.

### Consequences
* **Positive**: Native async I/O, excellent typing via Pydantic v2, clean integration with Python ML/audio libraries (Faster-Whisper, LanceDB, PyTorch), fast development velocity.
* **Negative**: Python GIL requires careful usage of process pools or async wrappers for CPU-bound tasks.

---

## ADR-004: Frontend Architecture: React + Vite + Tailwind CSS

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
Users require an intuitive, low-latency desktop interface that visualizes agent reasoning, tool invocations, audio waveforms, and interactive approval prompts.

### Decision
Implement the frontend using **React 18, Vite, Tailwind CSS, Lucide Icons, and Zustand**. Communication with the backend occurs over REST for initial configuration and WebSockets for real-time live events.

### Consequences
* **Positive**: Fast builds with Vite, responsive modern UI with Tailwind, lightweight footprint compared to heavy monolithic desktop frameworks.
* **Negative**: Requires Node.js tooling during frontend development.

---

## ADR-005: Multi-Agent Topology: Hierarchical Master-Specialist

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
A single generalist prompt often fails when alternating between coding, system automation, document retrieval, and personal scheduling. Conversely, a decentralized peer-to-peer swarm creates unpredictable message storms and high token consumption.

### Decision
Implement a **Hierarchical Master-Specialist Topology**:
1. **Master Agent**: Handles decomposition, classification, specialist dispatch, and response synthesis.
2. **Four Specialists**: Research & Knowledge, System & Automation, Code & Development, Personal & Executive.
3. Personas share the resident 3B model in Ollama, utilizing distinct system prompts, context slices, and scoped tool sets.

### Consequences
* **Positive**: Clear division of labor, minimal prompt dilution, predictable control flow, zero token thrashing between autonomous agents.
* **Negative**: Master Agent is a single point of failure for query routing (mitigated by fallback defaults).

---

## ADR-006: Local Voice Pipeline: Faster-Whisper + Piper TTS + Silero VAD

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
Voice interaction must feel responsive (<600ms latency) while functioning 100% offline and consuming minimal CPU and zero VRAM.

### Decision
1. **VAD**: Silero VAD (ONNX runtime on CPU) for voice activity detection.
2. **STT**: Faster-Whisper (quantized `base.en` or `small.en`) running via CTranslate2.
3. **TTS**: Piper TTS (high-quality local ONNX voice synthesizer running on CPU).

### Consequences
* **Positive**: Completely offline voice pipeline; Piper produces speech in ~100ms on CPU; zero impact on the 4GB GPU VRAM needed by the LLM.
* **Negative**: Synthetic voices require local voice model file downloads (~60 MB).

---

## ADR-007: Embedded Vector Store: LanceDB Embedded

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
Retrieval-Augmented Generation (RAG) requires a vector store. Running a standalone database server (like Milvus, Qdrant in Docker, or Weaviate) consumes unnecessary system RAM and adds process management overhead.

### Decision
Use **LanceDB** (or embedded ChromaDB) running in-process via Python bindings, storing data directly on disk in Apache Arrow format. Combined with local lightweight sentence embeddings (`bge-small-en-v1.5` running via ONNX).

### Consequences
* **Positive**: Zero external services or Docker containers; disk-based persistence; sub-millisecond retrieval; low memory footprint (<200 MB RAM).
* **Negative**: In-process store is bound to the single host application.

---

## ADR-008: 3-Tier Tool Security & Human-in-the-Loop (HITL) Execution

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
Autonomous agents interacting with operating system commands, file systems, and processes risk unintended damage if hallucinating or misinterpreting instructions.

### Decision
Classify all computer tools into three explicit security tiers:
* **Tier 1 (Safe / Read-Only)**: Automatically executed (e.g. read file, search vector store, get telemetry).
* **Tier 2 (Modifying / Low-Risk)**: Executed inside workspace with detailed logging and user notification.
* **Tier 3 (Destructive / High-Risk)**: Execution is paused at the backend; an interactive HITL modal is pushed to the frontend via WebSocket. The tool does not execute until the user clicks "Approve".

### Consequences
* **Positive**: Absolute safety against accidental data loss or unauthorized command execution.
* **Negative**: Slightly increases interaction friction for destructive workflows.

---

## ADR-009: Dataset Curation Pipeline for Future QLoRA Fine-Tuning

* **Status**: Accepted
* **Date**: 2026-10-25
* **Deciders**: Architecture Team

### Context
While the local 4 GB VRAM GPU cannot fine-tune models directly, user interactions, tool executions, and manual corrections provide high-value training signals.

### Decision
Build an automated dataset curation pipeline that logs successful, user-verified agent trajectories into standardized JSONL files (`data/training/curated/`). The data schema adheres to standard instruction-tuning formats (ShareGPT / Alpaca format), allowing export to Google Colab, external high-VRAM machines, or cloud GPUs for QLoRA adapter training.

### Consequences
* **Positive**: Zero wasted interaction data; seamless future fine-tuning path without burdening the local 4 GB GPU.
* **Negative**: Requires disk space to store conversation logs and curated trajectory files.
