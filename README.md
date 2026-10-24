# P.R.I.M.E.
### Personal Responsive Intelligent Multi-Agent Environment

[![Phase](https://img.shields.io/badge/Current_Phase-Phase_00:_Architecture-blue.svg)](#roadmap)
[![Hardware](https://img.shields.io/badge/Target_Hardware-16GB_RAM_|_4GB_VRAM-orange.svg)](#hardware-constraints)
[![Runtime](https://img.shields.io/badge/Runtime-Offline--First_|_Ollama-green.svg)](#architecture-overview)
[![License](https://img.shields.io/badge/License-Proprietary_/_Private-lightgrey.svg)](#)

P.R.I.M.E. is a sovereign, 100% offline-capable, local-first intelligent executive assistant designed for consumer-grade hardware (specifically Windows, 16 GB system RAM, and a 4 GB VRAM NVIDIA GPU). 

It coordinates a **Master Orchestrator Agent** and **four Specialist Agents** to manage daily workflows, local knowledge retrieval (RAG), voice interaction, persistent episodic and semantic memory, and safe, audited computer automation without sending a single byte of telemetry or prompt data to external cloud servers.

---

## Table of Contents

1. [Project Vision & Principles](#project-vision--principles)
2. [Hardware Constraints & VRAM Budget](#hardware-constraints--vram-budget)
3. [System Architecture Overview](#system-architecture-overview)
4. [Multi-Agent Topology](#multi-agent-topology)
5. [Core Subsystems](#core-subsystems)
   - [Backend (FastAPI)](#backend-fastapi)
   - [Frontend (React + Vite + Tailwind)](#frontend-react--vite--tailwind)
   - [Model Runtime (Ollama)](#model-runtime-ollama)
   - [Local Voice Engine (STT / TTS / VAD)](#local-voice-engine)
   - [RAG & Embedded Vector Store](#rag--embedded-vector-store)
   - [Persistent Memory Engine](#persistent-memory-engine)
   - [Controlled Computer Tools & Safety Tiers](#controlled-computer-tools--safety-tiers)
   - [Dataset Curation & Future Fine-Tuning](#dataset-curation--future-fine-tuning)
6. [Repository Structure](#repository-structure)
7. [Documentation Map](#documentation-map)
8. [Phase 00 Status & Next Steps](#phase-00-status--next-steps)

---

## Project Vision & Principles

P.R.I.M.E. is founded on five core pillars:

1. **Total Sovereignty & Offline Functionality**: Once dependencies and model weights are installed, P.R.I.M.E. operates completely disconnected from the Internet. No third-party LLM APIs (OpenAI, Anthropic, Google Cloud) are required for operation.
2. **Hardware Respect**: Explicitly engineered to operate inside a strict resource envelope: **16 GB RAM and 4 GB VRAM**. Heavy multi-billion parameter models and simultaneous memory-hogging processes are replaced by lean, quantized 3B–7B models, dynamic VRAM sharing, and hybrid CPU/GPU offloading.
3. **Specialized Multi-Agent Coordination**: Rather than asking a single generalist prompt to do everything, tasks are routed by a central Master Agent to dedicated Specialists (Research, System Automation, Code, Personal Executive).
4. **Safety & Human-in-the-Loop (HITL)**: Autonomous capability must not mean unchecked execution. Computer tools use a three-tier permission model requiring explicit user authorization for state-changing or destructive actions.
5. **Continuous Adaptation**: Every user interaction, correction, and approved execution trajectory is captured in a standardized format for persistent memory and future parameter-efficient fine-tuning (LoRA/QLoRA).

---

## Hardware Constraints & VRAM Budget

P.R.I.M.E. is strictly calibrated for:
* **Operating System**: Windows 10/11 (64-bit)
* **System RAM**: 16 GB DDR4/DDR5
* **Dedicated GPU**: NVIDIA GPU with 4 GB VRAM (e.g., GTX 1650, RTX 3050 Mobile/Desktop 4GB, or similar)
* **Compute Platform**: CUDA 12.x / PyTorch cu121+

### VRAM & Memory Allocation Envelope

| Subsystem | Component / Model | Quantization | Footprint (VRAM / RAM) | Execution Device |
| :--- | :--- | :--- | :--- | :--- |
| **Primary LLM** | Qwen 2.5 3B / Llama 3.2 3B | Q4_K_M | ~2.2 GB VRAM | GPU (Full offload) |
| **Alternative LLM (Heavy)** | Qwen 2.5 7B / Phi 3.5 Mini | Q4_K_M | ~3.2 GB VRAM + RAM | Hybrid GPU/CPU Offload |
| **Embeddings** | `bge-small-en-v1.5` / `all-MiniLM-L6-v2` | FP16/INT8 | ~120 MB RAM/VRAM | CPU / GPU Shared |
| **Speech-to-Text (STT)**| Faster-Whisper (base.en / small.en) | INT8 / FP16 | ~150–400 MB VRAM/RAM | GPU / CPU Offload on demand |
| **Text-to-Speech (TTS)**| Piper TTS (onnx runtime) | INT8 | ~80 MB RAM | CPU (Zero VRAM impact) |
| **Voice Activity (VAD)**| Silero VAD | ONNX | ~20 MB RAM | CPU |
| **Vector DB** | ChromaDB / LanceDB | Embedded | ~250 MB RAM | CPU / System RAM |
| **Core Services** | FastAPI + React (Node) | N/A | ~400 MB RAM | CPU / System RAM |
| **OS & Display Reserve**| Windows DWM + Desktop Display | N/A | ~600–900 MB VRAM | GPU Dedicated |

> [!CAUTION]
> **VRAM Exclusivity Rule**: At 4 GB VRAM, running Whisper and a 7B LLM simultaneously inside GPU memory risks an Out-Of-Memory (OOM) crash. P.R.I.M.E. enforces sequential execution or delegates audio transcription to CPU (utilizing Faster-Whisper's efficient CTranslate2 multi-threading) while keeping the LLM resident in GPU memory.

---

## System Architecture Overview

```
                      +---------------------------------------+
                      |       React + Vite + Tailwind UI      |
                      |  (Dashboard, Audio Visualizer, Logs)  |
                      +-------------------+-------------------+
                                          | WebSocket / REST
                                          v
                      +---------------------------------------+
                      |        FastAPI Backend Gateway        |
                      |  (Session Mgr, Event Bus, Dispatcher) |
                      +-------------------+-------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
+--------------------------------------+      +--------------------------------------+
|             MASTER AGENT             |      |       Audio & Sensory Pipeline       |
| (Planner, Classifier, Decomposer,    |      | (Silero VAD -> Faster-Whisper STT    |
|  Synthesizer, Safety Verifier)       |      |  -> Piper TTS Audio Out)             |
+------------------+-------------------+      +--------------------------------------+
                   |
     +-------------+-------------+-------------+
     |             |             |             |
     v             v             v             v
+----------+ +-----------+ +-----------+ +------------+
| Research | |  System   | |   Code    | |  Personal  |
| Specialist| | Automation| | Specialist| | Specialist |
+----+-----+ +-----+-----+ +-----+-----+ +-----+------+
     |             |             |             |
     v             v             v             v
+----------+ +-----------+ +-----------+ +------------+
| RAG Store| | Tool Exec | | File/Git  | | Episodic / |
| (LanceDB)| | (Sandbox) | | Engine    | | SQLite Mem |
+----------+ +-----------+ +-----------+ +------------+
                   |
                   v
+-----------------------------------------------------+
|           Local Model Runtime: Ollama               |
|    (Small Quantized Models: Qwen2.5 3B / 7B)        |
+-----------------------------------------------------+
```

---

## Multi-Agent Topology

P.R.I.M.E. employs a hierarchical multi-agent architecture orchestrated by a central dispatcher:

1. **Master Agent**: The single point of entry for user requests. Analyzes intent, decomposes multi-step goals into distinct sub-tasks, assigns tasks to specialists, monitors execution, arbitrates tool confirmations, and synthesizes the final response.
2. **Research & Knowledge Specialist**: Specializes in document analysis, semantic search across local knowledge bases, web search (when internet is manually enabled), and multi-document synthesis.
3. **System & Automation Specialist**: Manages local OS operations, file organization, application launching, system health diagnostics, and script execution within strict safety boundaries.
4. **Code & Development Specialist**: Analyzes source code, generates bug fixes, creates automated unit tests, and conducts static analysis.
5. **Personal & Executive Specialist**: Manages user schedules, task lists, daily briefings, user preferences, and tracks long-term conversational memory.

For complete agent specifications, interaction protocols, and system prompts, see [`AGENTS.md`](AGENTS.md).

---

## Core Subsystems

### Backend (FastAPI)
* **Framework**: Python 3.11+ with FastAPI and Uvicorn.
* **Communication**: Asynchronous REST endpoints for CRUD operations and bidirectional WebSockets for low-latency streaming of agent reasoning, voice packets, and tool telemetry.
* **Architecture**: Clean Architecture separating Domain Models, Application Services, Infrastructure Drivers, and API Controllers.

### Frontend (React + Vite + Tailwind)
* **Tech Stack**: React 18, Vite, Tailwind CSS, Lucide Icons, Zustand for state management.
* **Features**: Live streaming thought bubbles, agent activity monitors, interactive tool approval modals (HITL), real-time audio waveform visualization, and knowledge base document manager.

### Model Runtime (Ollama)
* **Integration**: Local HTTP REST API connection (`http://127.0.0.1:11434`).
* **Models**:
  - General Orchestration & Chat: `qwen2.5:3b-instruct-q4_K_M` or `llama3.2:3b-instruct-q4_K_M`
  - Deep Reasoning / Coding: `qwen2.5-coder:3b` or `qwen2.5:7b-instruct-q4_K_M` (hybrid offloaded)
  - Embeddings: `bge-small-en-v1.5` or `nomic-embed-text`

### Local Voice Engine
* **VAD**: Silero VAD running via ONNX Runtime on CPU (<1% CPU utilization).
* **STT**: Faster-Whisper (quantized `base.en` or `small.en`) via CTranslate2 with CPU/GPU dynamic device selection.
* **TTS**: Piper TTS (high-quality, fast local neural text-to-speech, low memory footprint, zero internet dependency).

### RAG & Embedded Vector Store
* **Engine**: LanceDB or ChromaDB in serverless/embedded mode running directly in the Python process.
* **Pipeline**: Recursive character chunking with metadata tagging, BM25 keyword + dense vector hybrid retrieval, and reciprocal rank fusion.

### Persistent Memory Engine
* **Structured Store**: SQLite with WAL (Write-Ahead Logging) mode for conversations, tasks, agent audit logs, and configuration.
* **Episodic & Semantic Store**: Vector-indexed memory chunks representing facts, preferences, and key interactions.
* **Reflection & Consolidation**: Periodic background consolidation of raw logs into high-level user preferences and project knowledge.

### Controlled Computer Tools & Safety Tiers
All tool executions are categorized into three explicit safety tiers:
* **Tier 1 (Safe / Read-Only)**: File read, directory list, system status, search. Automatically executed without prompt.
* **Tier 2 (Modifying / Low-Risk)**: File write inside workspace, app launch, clipboard copy. Logged and executed with notification.
* **Tier 3 (Destructive / High-Risk)**: File deletion, shell script execution, process termination, system configuration. **Requires explicit user modal confirmation (HITL)**.

### Dataset Curation & Future Fine-Tuning
* P.R.I.M.E. writes all successful agent thought-action-result trajectories into structured JSONL datasets (`data/training/curated/`).
* Standard format compatible with HuggingFace `trl` / `peft` / Unsloth for future QLoRA instruction fine-tuning when external compute or dedicated GPUs are available.

---

## Repository Structure

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
│   ├── app/
│   │   ├── api/            # REST and WebSocket endpoints
│   │   ├── core/           # Configuration, security, logging
│   │   ├── agents/         # Master and Specialist agent implementations
│   │   ├── memory/         # SQLite and Vector memory managers
│   │   ├── rag/            # Chunking, indexing, retrieval pipeline
│   │   ├── tools/          # Controlled computer tools & sandboxes
│   │   └── voice/          # Whisper, Piper, and VAD audio pipelines
│   └── tests/              # Pytest test suite
├── frontend/               # React + Vite dashboard (Phase 06)
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

## Documentation Map

* **System & Multi-Agent Architecture**: [`AGENTS.md`](AGENTS.md)
* **Real-Time Project State & Active Focus**: [`PROJECT_STATE.md`](PROJECT_STATE.md)
* **Task Board & Dependency Graph**: [`TASKS.md`](TASKS.md)
* **Architectural Decision Records**: [`DECISIONS.md`](DECISIONS.md)
* **Change History**: [`CHANGELOG.md`](CHANGELOG.md)
* **Phase 00 Blueprint & Verification**: [`docs/phases/PHASE_00.md`](docs/phases/PHASE_00.md)

---

## Phase 00 Status & Next Steps

* **Current Status**: Phase 00 (Architecture, Groundwork, & System Design) is **COMPLETE**.
* **Next Task**: `TASK-01-ENV-01` — Initialize Python 3.11 virtual environment, FastAPI scaffold, hardware check script, and Ollama connectivity verification.
* Refer to [`TASKS.md`](TASKS.md) and [`PROJECT_STATE.md`](PROJECT_STATE.md) for step-by-step instructions.
"# PRIME" 
