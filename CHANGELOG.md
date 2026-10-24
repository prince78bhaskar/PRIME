# Changelog

All notable changes to the **P.R.I.M.E.** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
