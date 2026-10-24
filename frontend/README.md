# P.R.I.M.E. Frontend

Command Center interface for the **P.R.I.M.E. (Personal Responsive Intelligent Multi-Agent Environment)** system.

Built with **React 18**, **TypeScript**, **Vite**, and **Tailwind CSS**. Designed with an original, futuristic holographic dark command center aesthetic.

---

## Features

* **Central Animated AI Orb (Arc Core)**:
  - Multi-ring concentric rotating SVG assembly with dynamic counter-rotation.
  - Status-reactive pulse breathing: Cyan (Ready/Idle), High-Speed Blue/Cyan (Streaming Tokens), Amber (Standby/Offline).
  - Dynamic hardware telemetry envelope display (2.2 GB VRAM / 16 GB RAM).
* **Audio Waveform Visualizer**:
  - 28-band responsive audio frequency visualizer indicating sensory bus status.
* **Direct Ollama Chat Console**:
  - Real-time Server-Sent Events (SSE) streaming token deltas.
  - Active model selector dropdown populated dynamically from local Ollama tags.
  - AbortController stream cancellation support.
  - Graceful connection error diagnostics when Ollama or backend is offline.
  - Zero simulated or fake AI responses — all inference is routed strictly to the local daemon.
* **Specialist Agent Roster (Phase 04 Blueprint)**:
  - Detailed cards for Master Agent and 4 Specialists (Research, System, Code, Personal).
  - Explicitly marked with **INACTIVE (PHASE 04)** badges to maintain full honesty.
* **Persistent Memory & Tasks (Phase 04 Blueprint)**:
  - SQLite WAL status, vector embedding blueprints, and Human-in-the-Loop (HITL) Tier 3 safety protocols.
* **System Telemetry & Settings**:
  - Modal allowing configuration of API endpoints, temperature, max generation tokens, and streaming toggles.

---

## Quick Start (Windows)

### Prerequisites
- **Node.js 18+** (v24.15 tested)
- **Backend running** on port 8000 (`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`)

### 1. Install Dependencies
```powershell
cd frontend
npm install
```

### 2. Start Development Server
```powershell
npm run dev
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

### 3. Production Build
```powershell
npm run build
```

---

## Component Architecture

```
frontend/src/
├── App.tsx                     # Main application layout, polling & chat state
├── main.tsx                    # React DOM root entry
├── index.css                   # Tailwind base, HUD panels & scanline overlay
├── types/
│   └── index.ts                # TypeScript data models (Chat, Health, Settings)
├── services/
│   └── api.ts                  # REST & SSE streaming client for FastAPI backend
└── components/
    ├── layout/
    │   ├── Header.tsx          # Top bar with backend/Ollama/VRAM telemetry badges
    │   ├── Sidebar.tsx         # Left vertical navigation (Command, Agents, Tasks, Config)
    │   └── StatusBar.tsx       # Bottom telemetry strip (Model, SQLite WAL, Token speed)
    ├── orb/
    │   └── ArcReactorOrb.tsx   # Central rotating multi-ring animated AI core
    ├── waveform/
    │   └── AudioWaveform.tsx   # 28-band sensory audio frequency visualizer
    ├── chat/
    │   └── ChatPanel.tsx       # Live chat stream console with model selector & cancellation
    ├── agents/
    │   └── AgentRoster.tsx     # Inactive Phase 04 specialist agent cards
    ├── tasks/
    │   └── TaskPlaceholders.tsx# Inactive Phase 04 task & memory stack inspection
    └── settings/
        └── SettingsModal.tsx   # System configuration & hardware guardrail controls
```
