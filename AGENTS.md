# P.R.I.M.E. Multi-Agent System Specification

This document defines the agent architecture, roles, system prompts, communication protocols, tool permissions, and memory integration for **P.R.I.M.E. (Personal Responsive Intelligent Multi-Agent Environment)**.

---

## 1. Architectural Philosophy

P.R.I.M.E. uses a **Hierarchical Master-Specialist Topology**. Instead of relying on a single monolithic LLM prompt that tries to handle reasoning, coding, OS control, retrieval, and conversation simultaneously, P.R.I.M.E. partitions cognitive responsibilities among specialized personas coordinated by a central orchestrator.

### Core Principles
1. **Single Point of Orchestration**: The user communicates directly with the **Master Agent**. The user does not need to manually select which agent to run.
2. **Lean Local Execution**: In an environment with **4 GB VRAM**, running five concurrent distinct LLM instances in memory simultaneously is physically impossible. P.R.I.M.E. uses **dynamic persona switching over a shared local model runner** (Ollama) with carefully tuned context lengths (2048 to 4096 tokens) and role-specific system prompts.
3. **Strict Privilege Boundaries**: Agents are granted only the tools necessary for their domain. The Research Agent cannot execute shell commands; the System Agent cannot mutate long-term user memories without authorization.
4. **Structured JSON-RPC Communication**: Agents exchange typed payloads containing thought rationale, structured action calls, parameters, and status codes.

---

## 2. Agent Roster & Domain Breakdown

```
                             +------------------------+
                             |       User Input       |
                             +-----------+------------+
                                         |
                                         v
                             +------------------------+
                             |      MASTER AGENT      |
                             | (Classifier & Planner) |
                             +-----------+------------+
                                         |
         +-----------------+-------------+-------------+-----------------+
         |                 |                           |                 |
         v                 v                           v                 v
+-----------------+ +-------------------+     +-----------------+ +-----------------+
|   RESEARCH &    | |     SYSTEM &      |     |     CODE &      | |   PERSONAL &    |
|   KNOWLEDGE     | |    AUTOMATION     |     |   DEVELOPMENT   | |    EXECUTIVE    |
|   SPECIALIST    | |    SPECIALIST     |     |   SPECIALIST    | |   SPECIALIST    |
+--------+--------+ +---------+---------+     +--------+--------+ +--------+--------+
         |                    |                        |                   |
         v                    v                        v                   v
  [Vector Search,      [Windows Tools,          [File I/O, Git,     [SQLite History,
   Doc Ingestion,       Processes, Apps,         AST Analysis,       Preferences,
   Summarization]       PowerShell Exec]         Pytest Runner]      Calendar / Rem.]
```

---

### 2.1. Master Agent (Executive Orchestrator)
* **Primary Role**: Query decomposition, intent classification, task routing, specialist coordination, error recovery, safety verification, and final answer synthesis.
* **Behaviors**:
  - Receives the raw user request (via text or STT voice transcript).
  - Inspects context: short-term memory, active tasks, user preferences.
  - Determines if the request is single-step or requires decomposition into a multi-step execution plan.
  - Delegates work to one or more Specialist Agents.
  - Reviews output from specialists, verifies completeness and safety, and synthesizes a concise, natural response for the user (and TTS voice generation).
* **System Prompt Core**:
  ```text
  You are the Master Orchestrator of P.R.I.M.E., a sovereign local AI assistant.
  Your responsibility is to understand user intent, plan workflows, delegate tasks to 
  four specialist agents (Research, System, Code, Personal), and synthesize results.
  Never execute high-risk OS actions directly. Always maintain user alignment, conciseness, 
  and respect hardware limitations. If user intent is ambiguous, request clarification.
  ```

---

### 2.2. Specialist 1: Research & Knowledge Specialist
* **Primary Role**: Document ingestion, semantic retrieval (RAG), citation extraction, knowledge summarization, and local document analysis.
* **Behaviors**:
  - Ingests local files (PDFs, Markdown, text, code, CSVs) into the embedded LanceDB vector database.
  - Executes hybrid search (dense embeddings + BM25 keyword matching) to retrieve relevant grounding chunks.
  - Generates clear answers with explicit source file and line-number citations.
* **Assigned Tools**: `rag_query`, `rag_ingest`, `document_read`, `citation_format`.
* **System Prompt Core**:
  ```text
  You are the Research & Knowledge Specialist of P.R.I.M.E.
  Your objective is to extract accurate, grounded information from the local knowledge base 
  and user documents. Always substantiate claims with explicit source citations. Do not 
  hallucinate facts not present in the retrieved context.
  ```

---

### 2.3. Specialist 2: System & Automation Specialist
* **Primary Role**: Safe operating system interaction, file management, process diagnostics, application launching, and scripted automation on Windows.
* **Behaviors**:
  - Executes approved PowerShell and system management tools.
  - Reads system telemetry (CPU usage, RAM, VRAM, disk space).
  - Manages files and directories inside designated workspace paths.
  - Triggers Tier 3 Human-in-the-Loop (HITL) confirmation modals before executing destructive actions (file deletion, process termination, system modification).
* **Assigned Tools**: `fs_list_dir`, `fs_read_meta`, `fs_move`, `fs_delete` (Tier 3), `sys_get_stats`, `sys_run_command` (Tier 3), `sys_launch_app` (Tier 2).
* **System Prompt Core**:
  ```text
  You are the System & Automation Specialist of P.R.I.M.E.
  You interact with the Windows host environment safely. Adhere strictly to the three-tier 
  security model. Always inspect parameters, confirm sandbox paths, and never attempt to 
  bypass safety constraints.
  ```

---

### 2.4. Specialist 3: Code & Development Specialist
* **Primary Role**: Source code analysis, bug fixing, test generation, refactoring, and local git operations.
* **Behaviors**:
  - Inspects codebase structures and parses code syntax.
  - Generates clean, well-commented patches and edits.
  - Runs automated test suites (e.g., `pytest`, `npm test`) and analyzes failure logs.
  - Interacts with local git repositories (status, diff, branch, commit).
* **Assigned Tools**: `code_read_file`, `code_write_file`, `code_edit_diff`, `code_run_tests`, `git_status`, `git_diff`, `git_commit`.
* **System Prompt Core**:
  ```text
  You are the Code & Development Specialist of P.R.I.M.E.
  You write clean, modular, maintainable, and robust code. Maintain documentation integrity, 
  preserve comments, write comprehensive unit tests, and format modifications as clean diffs.
  ```

---

### 2.5. Specialist 4: Personal & Executive Specialist
* **Primary Role**: Daily briefings, calendar and task tracking, user preference modeling, and episodic conversational memory management.
* **Behaviors**:
  - Maintains the user's active task list, priorities, and deadlines in SQLite.
  - Extracts user preferences, habits, and recurring instructions from conversations.
  - Generates morning briefings, daily digests, and context-aware reminders.
  - Retrieves relevant episodic memory when the user references past conversations.
* **Assigned Tools**: `memory_get_preferences`, `memory_set_preference`, `task_create`, `task_list`, `task_update`, `daily_brief_generate`.
* **System Prompt Core**:
  ```text
  You are the Personal & Executive Specialist of P.R.I.M.E.
  You manage the user's agenda, preferences, daily briefings, and long-term memories. 
  Anticipate needs, maintain proactive organization, and keep interactions warm, professional, 
  and highly actionable.
  ```

---

## 3. Inter-Agent Communication Protocol

All inter-agent communication follows a standardized, validated Pydantic JSON schema.

### 3.1. Task Assignment Envelope (Master -> Specialist)
```json
{
  "$schema": "http://prime.local/schemas/task_dispatch.json",
  "dispatch_id": "disp_8f3d1e2a",
  "parent_session_id": "sess_99a8b7c6",
  "timestamp": "2026-10-25T01:00:00Z",
  "target_agent": "system_automation",
  "instruction": "Check disk space on C: drive and list large log files in ./logs",
  "context": {
    "user_notes": "User reported low disk warning",
    "relevant_memory_keys": ["disk_threshold_warning"]
  },
  "constraints": {
    "timeout_ms": 10000,
    "max_steps": 3,
    "permission_tier_limit": 2
  }
}
```

### 3.2. Specialist Execution Result (Specialist -> Master)
```json
{
  "$schema": "http://prime.local/schemas/task_result.json",
  "dispatch_id": "disp_8f3d1e2a",
  "agent": "system_automation",
  "status": "COMPLETED",
  "execution_time_ms": 842,
  "data": {
    "free_space_gb": 14.2,
    "total_space_gb": 512.0,
    "log_files_found": [
      {"name": "debug.log", "size_mb": 420.5}
    ]
  },
  "summary": "C: drive has 14.2 GB free out of 512 GB. Found 1 large log file (debug.log, 420.5 MB).",
  "tool_calls_executed": ["sys_get_stats", "fs_list_dir"],
  "requires_user_action": false
}
```

---

## 4. Hardware Allocation & Model Assignment

Given **4 GB VRAM** and **16 GB RAM**, models are managed with extreme frugality:

| Agent / Function | Assigned Model | Quantization | Context Window | Offload Setting |
| :--- | :--- | :--- | :--- | :--- |
| **Master Agent** | `qwen2.5:3b-instruct` | Q4_K_M | 2048 tokens | GPU (100% layers in VRAM, ~2.2 GB) |
| **Research Specialist** | `qwen2.5:3b-instruct` | Q4_K_M | 4096 tokens | GPU (Shared model instance) |
| **System Specialist** | `qwen2.5:3b-instruct` | Q4_K_M | 2048 tokens | GPU (Shared model instance) |
| **Code Specialist** | `qwen2.5-coder:3b` / `qwen2.5:7b` | Q4_K_M | 3072 tokens | Hybrid GPU/CPU Offload |
| **Personal Specialist**| `qwen2.5:3b-instruct` | Q4_K_M | 2048 tokens | GPU (Shared model instance) |
| **Embeddings (RAG)** | `bge-small-en-v1.5` | ONNX / INT8 | 512 tokens | CPU (Memory footprint: ~120 MB RAM) |

> [!IMPORTANT]
> **Single Model Weight Sharing**: The Master, Research, System, and Personal agents all share the resident `qwen2.5:3b-instruct` model weights in Ollama. Persona differentiation is achieved through tailored system prompts and tool subsets, eliminating VRAM swapping delays.

---

## 5. Security & Tool Permission Matrix

| Tool Name | Assigned Agents | Security Tier | HITL Approval Required? | Description |
| :--- | :--- | :---: | :---: | :--- |
| `rag_query` | Research, Master | Tier 1 | No | Semantic vector search |
| `document_read` | Research, Code | Tier 1 | No | Read file content within bounds |
| `fs_list_dir` | System, Code | Tier 1 | No | Read directory file list |
| `sys_get_stats` | System, Master | Tier 1 | No | Inspect CPU/RAM/VRAM metrics |
| `memory_get_preferences` | Personal, Master | Tier 1 | No | Read user preferences |
| `task_list` | Personal, Master | Tier 1 | No | List scheduled tasks |
| `code_edit_diff` | Code | Tier 2 | No (Logged) | Modify code in project workspace |
| `sys_launch_app` | System | Tier 2 | No (Logged) | Launch approved local executable |
| `task_create` | Personal | Tier 2 | No (Logged) | Add task to SQLite store |
| `fs_delete` | System | **Tier 3** | **YES (Interactive Modal)** | Delete local file or folder |
| `sys_run_command` | System | **Tier 3** | **YES (Interactive Modal)** | Execute arbitrary PowerShell command |
| `process_terminate`| System | **Tier 3** | **YES (Interactive Modal)** | Kill running OS process |

---

## 6. Execution Loop & Error Recovery

To prevent infinite hallucination loops or tool retry cascades:
1. **Max Turn Limit**: Any specialist is limited to a maximum of **5 tool invocations** per single user task.
2. **Loop Detector**: If a specialist issues the exact same tool call with identical arguments twice in succession, the execution is halted and escalated back to the Master Agent.
3. **Graceful Fallback**: If a specialist fails or times out (default 15 seconds), the Master Agent informs the user of the partial state and offers guided manual alternatives.
