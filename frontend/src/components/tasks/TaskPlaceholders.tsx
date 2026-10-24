import React from 'react';
import { Database, ShieldAlert, CheckCircle2, Clock, GitBranch } from 'lucide-react';

export const TaskPlaceholders: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-cyan-500/30 text-xs font-mono text-cyan-300 flex items-start space-x-3">
        <GitBranch className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold uppercase tracking-wider text-white">
            AUTONOMOUS TASK & PERSISTENT MEMORY MODULES (PHASE 04 PIPELINE)
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            SQLite session storage, vector episodic memory indexing, and scheduled workflow tasks are formally specified in{' '}
            <code className="text-cyan-400 font-bold">TASKS.md</code>. Below are the verified active blueprints awaiting activation.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Memory Hub Blueprint */}
        <div className="hud-panel hud-corner-brackets p-5 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400 font-display font-bold text-sm">
              <Database className="w-4 h-4 text-amber-400" />
              <span>PERSISTENT MEMORY STACK</span>
            </div>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-700">
              STANDBY
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Structured Storage:</span>
              <span className="text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>SQLite WAL Initialized</span>
              </span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Vector Embeddings:</span>
              <span className="text-amber-400 flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>LanceDB Embedded (Phase 04)</span>
              </span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400">Episodic Reflection:</span>
              <span className="text-slate-500">Scheduled Phase 04</span>
            </div>
          </div>
        </div>

        {/* HITL Safety Hub Blueprint */}
        <div className="hud-panel hud-corner-brackets p-5 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400 font-display font-bold text-sm">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>HUMAN-IN-THE-LOOP (HITL) ARBITRATION</span>
            </div>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-700">
              STANDBY
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Tier 3 destructive OS actions (file deletion, arbitrary PowerShell script execution, process termination) will require interactive approval modals streamed over WebSockets.
          </p>

          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/20 text-[11px] font-mono text-rose-300">
            Current Privilege Limit: Tier 1 (Read-Only Direct LLM Chat Link active).
          </div>
        </div>
      </div>
    </div>
  );
};
