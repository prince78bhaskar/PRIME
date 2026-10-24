import React from 'react';
import { Compass, BookOpen, Terminal, Code2, Calendar, Lock, AlertTriangle } from 'lucide-react';

export const AgentRoster: React.FC = () => {
  const agents = [
    {
      id: 'master',
      name: 'Master Orchestrator',
      role: 'Executive Orchestrator & Synthesizer',
      desc: 'Central coordinator. Handles intent classification, sub-task decomposition, specialist delegation, and final answer synthesis.',
      status: 'INACTIVE (PHASE 04)',
      assignedTools: ['intent_decompose', 'specialist_route', 'response_synthesize'],
      tier: 'Tier 1 / Orchestrator',
      icon: <Compass className="w-5 h-5 text-cyan-400" />,
      color: 'border-cyan-500/30 bg-cyan-950/20',
    },
    {
      id: 'research',
      name: 'Research & Knowledge Specialist',
      role: 'RAG & Semantic Retrieval Specialist',
      desc: 'Embedded LanceDB vector search, document ingestion (PDF, Markdown, code), BM25 hybrid ranking, and source citation extraction.',
      status: 'INACTIVE (PHASE 04)',
      assignedTools: ['rag_query', 'rag_ingest', 'document_read', 'citation_format'],
      tier: 'Tier 1 (Read-Only)',
      icon: <BookOpen className="w-5 h-5 text-sky-400" />,
      color: 'border-sky-500/30 bg-sky-950/20',
    },
    {
      id: 'system',
      name: 'System & Automation Specialist',
      role: 'OS Control & Scripted Automation',
      desc: 'Windows host environment interaction, file system operations, process diagnostics, and Tier 3 Human-in-the-Loop confirmation modals.',
      status: 'INACTIVE (PHASE 04)',
      assignedTools: ['fs_list_dir', 'fs_read_meta', 'fs_delete (HITL)', 'sys_run_command (HITL)'],
      tier: 'Tier 3 (HITL Mandatory)',
      icon: <Terminal className="w-5 h-5 text-amber-400" />,
      color: 'border-amber-500/30 bg-amber-950/20',
    },
    {
      id: 'code',
      name: 'Code & Development Specialist',
      role: 'Source Code Analysis & Testing',
      desc: 'AST code parsing, automated unit test generation, unified patch/diff formatting, and local Git repository management.',
      status: 'INACTIVE (PHASE 04)',
      assignedTools: ['code_read_file', 'code_write_file', 'code_edit_diff', 'code_run_tests'],
      tier: 'Tier 2 (Workspace Logged)',
      icon: <Code2 className="w-5 h-5 text-emerald-400" />,
      color: 'border-emerald-500/30 bg-emerald-950/20',
    },
    {
      id: 'personal',
      name: 'Personal & Executive Specialist',
      role: 'Episodic Memory & Agenda Tracker',
      desc: 'Maintains user active task priorities, calendar agendas, recurring preferences, and long-term conversational memory.',
      status: 'INACTIVE (PHASE 04)',
      assignedTools: ['memory_get_preferences', 'task_create', 'task_list', 'daily_brief_generate'],
      tier: 'Tier 1 / Tier 2',
      icon: <Calendar className="w-5 h-5 text-purple-400" />,
      color: 'border-purple-500/30 bg-purple-950/20',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Notice Banner */}
      <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-300 text-xs font-mono flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-amber-200 uppercase tracking-wider">
            AGENT ORCHESTRATION SUBSYSTEM INACTIVE (PHASE 04 SCHEDULED)
          </div>
          <p className="text-slate-300 leading-relaxed text-[11px]">
            In Phase 03, the frontend communicates directly with the local Ollama runtime. Specialist agent personas, tool sandboxing, and autonomous Master-Specialist routing are specified in{' '}
            <code className="text-cyan-400 font-bold">AGENTS.md</code> and will be implemented in Phase 04. Agents are displayed below for architectural inspection.
          </p>
        </div>
      </div>

      {/* Roster Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={`hud-panel hud-corner-brackets p-5 rounded-xl border ${agent.color} space-y-3 relative overflow-hidden`}
          >
            {/* Header with Inactive Badge */}
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-700/60">
                  {agent.icon}
                </div>
                <div>
                  <h3 className="font-display font-bold text-sm tracking-wide text-white">
                    {agent.name}
                  </h3>
                  <p className="text-[11px] font-mono text-cyan-400/80">
                    {agent.role}
                  </p>
                </div>
              </div>

              <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-900 text-amber-400 border border-amber-500/40 font-bold flex items-center space-x-1">
                <Lock className="w-2.5 h-2.5" />
                <span>INACTIVE</span>
              </span>
            </div>

            {/* Description */}
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              {agent.desc}
            </p>

            {/* Security Tier & Tools */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-500">PRIVILEGE:</span>
                <span className="text-slate-300 font-semibold">{agent.tier}</span>
              </div>
              <div className="space-y-1">
                <div className="text-[10px] font-mono text-slate-500">PLANNED TOOLS:</div>
                <div className="flex flex-wrap gap-1">
                  {agent.assignedTools.map((t, idx) => (
                    <span
                      key={idx}
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-950/80 border border-slate-700/60 text-slate-400"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
