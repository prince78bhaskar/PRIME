# Phase 00: Architecture, Documentation & Groundwork

**Status**: **COMPLETED**  
**Phase Date**: 2026-10-25  
**Deliverable**: Foundational System Architecture, Technical Documentation, Task Dependency Board, and Repository Blueprint for P.R.I.M.E.

---

## 1. Executive Summary

Phase 00 establishes the technical baseline, specifications, constraints, and architecture for **P.R.I.M.E. (Personal Responsive Intelligent Multi-Agent Environment)**. 

No application code was compiled and no large models were downloaded during this phase. Instead, every architectural decision, security boundary, memory schema, multi-agent protocol, and hardware allocation constraint was rigorously defined to ensure that future implementation phases (Phase 01 through Phase 07) proceed deterministically without design ambiguity.

---

## 2. Hardware Constraints & Resource Budget

P.R.I.M.E. is designed specifically for consumer workstation specifications:
* **Operating System**: Windows 10/11 (64-bit)
* **System RAM**: 16 GB Physical RAM
* **Dedicated GPU**: NVIDIA GPU with 4 GB VRAM
* **Inference Runtime**: Ollama local daemon + CTranslate2 / ONNX Runtime

### Strict VRAM Ceiling Breakdown
On a 4 GB VRAM GPU, the Windows Desktop Window Manager (DWM) and display subsystem consume approximately 600 MB to 900 MB of VRAM. This leaves **~3.1 GB to 3.4 GB of usable VRAM** for AI inference.

$$\text{Usable VRAM} \approx 4096\text{ MB} - 800\text{ MB (OS)} \approx 3296\text{ MB}$$

To guarantee stability and prevent CUDA Out-Of-Memory (OOM) fatal aborts:
1. **Primary Model**: Standardized on 4-bit quantized (Q4_K_M) 3B parameter models (`qwen2.5:3b-instruct` or `llama3.2:3b-instruct`). Model weights occupy **~2.0 GB to 2.2 GB VRAM**.
2. **Context Cache**: Context window is capped at 2048 to 4096 tokens, allocating **~400 MB to 600 MB VRAM** for KV cache.
3. **Total LLM VRAM Budget**: $\le 2.8\text{ GB}$, leaving $\ge 400\text{ MB}$ headroom.
4. **Speech-to-Text (STT)**: Faster-Whisper (`base.en`) is offloaded to CPU using multi-threaded CTranslate2, or time-shared. It will **not** share persistent VRAM with the LLM.
5. **Text-to-Speech (TTS)**: Piper TTS runs on CPU via ONNX Runtime (<80 MB RAM, 0 MB VRAM).
6. **Embeddings & Vector Search**: `bge-small-en-v1.5` runs on CPU via ONNX (<120 MB RAM, 0 MB VRAM).

> [!WARNING]
> **No Large Models**: Models exceeding 7B parameters (e.g. 13B, 14B, 32B, 70B) or unquantized FP16 models MUST NOT be loaded into GPU memory. Fine-tuning workloads (LoRA/QLoRA backpropagation) MUST NOT be executed on this local device.

---

## 3. Subsystem Architecture Specifications

### 3.1. Master Agent & Four Specialists
P.R.I.M.E. partitions autonomous work across five coordinated agent personas:

1. **Master Agent (Executive Orchestrator)**:
   - Receives all incoming queries from the user or voice pipeline.
   - Performs intent classification, sub-task decomposition, and constraint verification.
   - Dispatches structured JSON-RPC tasks to specialists.
   - Collects specialist outputs, enforces safety bounds, and synthesizes final natural language responses.
2. **Specialist 1: Research & Knowledge Specialist**:
   - Manages document ingestion (PDF, Markdown, TXT, CSV, Code) into embedded LanceDB.
   - Executes hybrid retrieval (dense embeddings + BM25 keyword matching).
   - Generates grounded answers with strict source file and line-number citations.
3. **Specialist 2: System & Automation Specialist**:
   - Manages Windows OS operations: file system traversal, application launching, system metrics inspection.
   - Runs scripts and PowerShell commands strictly within sandbox guidelines.
   - Triggers Tier 3 interactive confirmation modals (HITL) for destructive actions.
4. **Specialist 3: Code & Development Specialist**:
   - Inspects project codebases, analyzes syntax, and writes unified diff patches.
   - Generates and executes automated tests (`pytest`, `vitest`).
   - Conducts local git operations (status, diff, branch, commit).
5. **Specialist 4: Personal & Executive Specialist**:
   - Tracks user schedules, daily briefings, and task lists in SQLite.
   - Manages episodic and semantic long-term user preferences and notes.
   - Provides proactive morning summaries and actionable digests.

### 3.2. Backend Architecture (FastAPI + Async Python)
* **Framework**: FastAPI with Uvicorn.
* **Endpoints**:
  - REST endpoints for configuration, health diagnostics, file uploads, and session management.
  - Bidirectional WebSocket (`/ws/events`) for low-latency streaming of agent thought tokens, tool execution telemetry, audio packets, and HITL approval dialogs.
* **Separation of Concerns**:
  - `app/api/`: REST routes and WebSocket connection handlers.
  - `app/core/`: Settings, hardware probes, security policies, event bus.
  - `app/agents/`: Master orchestrator and specialist implementations.
  - `app/tools/`: Controlled computer tools with tier decorators.
  - `app/memory/`: SQLite session store and preference database.
  - `app/rag/`: Document ingestion, chunking, and LanceDB vector store.
  - `app/voice/`: Silero VAD, Faster-Whisper STT, and Piper TTS wrappers.

### 3.3. Frontend Architecture (React + Vite + Tailwind CSS)
* **Framework**: React 18 with Vite bundling.
* **Styling**: Tailwind CSS with dark-mode executive aesthetic.
* **State Management**: Zustand for real-time WebSocket state, active agent indicators, and audio state.
* **Key Components**:
  - `StreamingFeed`: Real-time token streaming with collapsible thought accordions.
  - `AgentRosterBar`: Visual indicators showing active specialist and resource utilization.
  - `ApprovalModal`: Interactive Human-in-the-Loop dialog for Tier 3 actions with diff/command preview.
  - `VoiceVisualizer`: Live WebAudio waveform visualizer with push-to-talk toggle.
  - `KnowledgeManager`: Drag-and-drop interface for local RAG document indexing.

### 3.4. Local Model Runtime (Ollama)
* **Communication**: HTTP REST API communicating with `http://127.0.0.1:11434`.
* **Endpoints Used**:
  - `/api/generate`: Streaming completion.
  - `/api/chat`: Structured conversational and tool-calling exchanges.
  - `/api/tags`: Model inventory and health inspection.
* **Model Configuration**:
  - Default: `qwen2.5:3b-instruct-q4_K_M`
  - Parameters: `temperature=0.2`, `top_p=0.9`, `num_ctx=2048` (or `4096` for Research Specialist), `num_gpu=99` (full GPU offload).

### 3.5. Local Voice Pipeline
```
[Microphone In] 
      │
      ▼
[Silero VAD (ONNX on CPU)] ──(Voice Detected)──► [Faster-Whisper STT (CPU/CTranslate2)]
                                                              │
                                                              ▼
                                                     [User Text Prompt]
                                                              │
                                                              ▼
                                                     [Master Agent Loop]
                                                              │
                                                              ▼
[Speaker Out] ◄── [Audio Stream] ◄── [Piper TTS (CPU/ONNX)] ◄── [Synthesized Text]
```

### 3.6. Controlled Computer Tools & 3-Tier Security
* **Tier 1 (Safe / Read-Only)**: File read, directory list, system status, search. Executed automatically without user interruption.
* **Tier 2 (Modifying / Low-Risk)**: File write within workspace bounds, application launch, clipboard copy. Executed automatically with persistent log entry and notification.
* **Tier 3 (Destructive / High-Risk)**: File deletion, arbitrary shell/PowerShell command, process termination, system modification. **Requires explicit interactive approval (HITL) via UI modal**. Backend suspends execution until approval/rejection event is received.

### 3.7. Offline Requirements & Air-Gapped Operation
* P.R.I.M.E. makes **zero** outbound network requests to third-party APIs.
* All model weights, voice models, vector indices, and SQLite databases reside locally on the host file system.
* In Phase 07, an air-gap verification test will ensure the application boots, transcribes voice, answers queries via RAG, and executes tools with all network adapters disabled.

### 3.8. Dataset Curation for Future QLoRA Fine-Tuning
* Local hardware cannot fine-tune models directly without OOM.
* P.R.I.M.E. includes an automated **Trajectory Curation Pipeline** in `backend/app/core/curator.py`.
* Every successful interaction where the user approves the output or verifies an action is serialized into `data/training/curated/trajectories.jsonl` in standard ShareGPT format:
  ```json
  {
    "id": "traj_001",
    "conversations": [
      {"from": "human", "value": "..."},
      {"from": "thought", "value": "..."},
      {"from": "tool_call", "value": "..."},
      {"from": "tool_result", "value": "..."},
      {"from": "gpt", "value": "..."}
    ]
  }
  ```
* These curated datasets can be exported at any time to run QLoRA parameter-efficient fine-tuning on external cloud compute or larger GPUs.

---

## 4. Repository Structure Blueprint

```
P.R.I.M.E/
├── README.md               # Project overview, architecture, hardware budget
├── AGENTS.md               # Detailed specification for all 5 agents & protocols
├── PROJECT_STATE.md        # Real-time state of the project, roadmap, active tasks
├── TASKS.md                # Task tracking board, ID scheme, dependency DAG
├── DECISIONS.md            # Architectural Decision Records (ADRs)
├── CHANGELOG.md            # Versioned log of changes across phases
├── .gitignore              # Environment, build, model, and cache exclusions
├── docs/                   # Deep documentation
│   ├── phases/             # Phase specifications and verification logs
│   │   └── PHASE_00.md     # Phase 00 execution and blueprint
│   ├── architecture/       # System diagrams and data flow
│   └── security/           # Safety tiers, sandboxing, and threat model
├── backend/                # FastAPI application (Phase 01+)
│   ├── requirements.txt    # Locked Python dependencies
│   ├── app/
│   │   ├── main.py         # Application entry point & lifespan
│   │   ├── api/            # REST and WebSocket endpoints
│   │   ├── core/           # Config, hardware probe, security, curator
│   │   ├── agents/         # Master and Specialist implementations
│   │   ├── memory/         # SQLite and Vector memory managers
│   │   ├── rag/            # Chunking, indexing, retrieval pipeline
│   │   ├── tools/          # Controlled computer tools & sandboxes
│   │   └── voice/          # Whisper, Piper, and VAD audio pipelines
│   └── tests/              # Pytest test suite
├── frontend/               # React + Vite dashboard (Phase 06)
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.ts      # Vite build configuration
│   ├── src/
│   │   ├── components/     # UI widgets, chat feeds, audio visualizers
│   │   ├── hooks/          # WebSocket and audio hooks
│   │   └── stores/         # Zustand state stores
└── data/                   # Local databases, vectors, and curated datasets
    ├── memory/             # SQLite database and vector indices
    ├── knowledge/          # Raw and processed documents for RAG
    └── training/           # Curated trajectories for future fine-tuning
```

---

## 5. Phase 00 Acceptance Criteria & Verification

| Requirement | Acceptance Standard | Verification Result |
| :--- | :--- | :---: |
| **Document Complete Project Architecture** | Full documentation covering Vision, FastAPI, React, Ollama, 4 Specialists + Master, Voice, RAG, Memory, Tools, Offline, Security, Fine-tuning. | **PASS** (Covered in README, AGENTS, DECISIONS, PHASE_00) |
| **Inspect & Preserve Repository** | Inspect directory, confirm empty state, initialize clean git repo without overwriting existing files. | **PASS** (Inspected, git initialized) |
| **Hardware Constraints Documented** | Explicitly define 16GB RAM / 4GB VRAM limits; reject large models (>7B) and on-device training. | **PASS** (Explicitly budgeted across all docs) |
| **Required Core Files Created** | `README.md`, `AGENTS.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `CHANGELOG.md`, `docs/phases/PHASE_00.md`. | **PASS** (All 7 files created) |
| **Task ID Scheme & Dependency DAG** | Stable format `TASK-<PHASE>-<CAT>-<NUM>`, lifecycle statuses, Mermaid DAG, acceptance criteria. | **PASS** (Defined in TASKS.md) |
| **Clear Next-Task List for New AI** | Immediate prioritized next tasks for Phase 01 clearly defined with preconditions and test specs. | **PASS** (Defined in TASKS.md and PROJECT_STATE.md) |
| **No Application Code / No Model Downloads** | Strictly limit Phase 00 to documentation, architecture, and scaffolding without building full app. | **PASS** (Zero unauthorized code or models downloaded) |

---

## 6. Hand-off Protocol for Phase 01

Any AI agent or software engineer continuing work on P.R.I.M.E. must execute **Phase 01: Core Environment & Local Model Runtime**:

1. Read [`PROJECT_STATE.md`](../../PROJECT_STATE.md) to confirm Phase 00 completion.
2. Locate the active task in [`TASKS.md`](../../TASKS.md): **`TASK-01-ENV-01`**.
3. Create the Python virtual environment and scaffold the `backend/` directory structure.
4. Implement `backend/app/core/hardware.py` to programmatically verify that the host hardware matches the Windows 16GB RAM / 4GB VRAM profile.
5. Implement `backend/app/core/ollama.py` to connect asynchronously to the local Ollama instance.
6. Verify that all unit tests pass before advancing to Phase 02.
