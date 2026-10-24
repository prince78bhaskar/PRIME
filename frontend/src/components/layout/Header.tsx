import React from 'react';
import { Cpu, RefreshCw, Sliders, ShieldCheck, HardDrive } from 'lucide-react';
import { BackendHealth, OllamaHealth } from '../../types';

interface HeaderProps {
  backendHealth: BackendHealth | null;
  ollamaHealth: OllamaHealth | null;
  isChecking: boolean;
  onRefresh: () => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendHealth,
  ollamaHealth,
  isChecking,
  onRefresh,
  onOpenSettings,
}) => {
  const isBackendOnline = backendHealth?.status === 'healthy';
  const isOllamaConnected = ollamaHealth?.isConnected === true;

  return (
    <header className="h-16 border-b border-cyan-500/20 bg-hud-bg/90 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between z-20 select-none">
      {/* Brand & Arc Identity */}
      <div className="flex items-center space-x-3">
        <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-cyan-950/40 border border-cyan-500/40 shadow-glow-cyan">
          <div className="w-4 h-4 rounded-full bg-cyan-400 animate-pulse-glow shadow-glow-cyan" />
          <div className="absolute inset-0 rounded-lg border border-cyan-400/20 animate-ping opacity-25" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-display font-black tracking-widest text-lg lg:text-xl text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-200 to-amber-300">
              P.R.I.M.E.
            </h1>
            <span className="text-[10px] font-mono tracking-wider px-1.5 py-0.5 rounded border border-cyan-500/30 text-cyan-400 bg-cyan-950/40">
              v0.3.0-PHASE.03
            </span>
          </div>
          <p className="text-[10px] font-mono text-slate-400 tracking-tight hidden sm:block">
            PERSONAL RESPONSIVE INTELLIGENT MULTI-AGENT ENVIRONMENT
          </p>
        </div>
      </div>

      {/* Telemetry Status Indicators */}
      <div className="flex items-center space-x-2 sm:space-x-4">
        {/* Hardware Constraint Badge */}
        <div className="hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-900/80 border border-slate-700/60 text-[11px] font-mono text-slate-300">
          <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
          <span>GPU: 4GB VRAM CEILING</span>
          <span className="text-slate-600">|</span>
          <span>16GB RAM</span>
        </div>

        {/* Backend Health Badge */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-[11px] font-mono transition-colors ${
            isBackendOnline
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-400'
              : 'bg-rose-950/30 border-rose-500/40 text-rose-400'
          }`}
          title={isBackendOnline ? 'Backend service online' : 'Backend offline or unreachable'}
        >
          <span className={`w-2 h-2 rounded-full ${isBackendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className="hidden md:inline">BACKEND:</span>
          <span>{isBackendOnline ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        {/* Ollama Local Runtime Badge */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-[11px] font-mono transition-colors ${
            isOllamaConnected
              ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-300'
              : 'bg-amber-950/30 border-amber-500/40 text-amber-400'
          }`}
          title={
            isOllamaConnected
              ? `Ollama connected (${ollamaHealth?.availableModels.length || 0} models ready)`
              : 'Ollama offline at 127.0.0.1:11434'
          }
        >
          <Cpu className="w-3.5 h-3.5" />
          <span className="hidden md:inline">OLLAMA:</span>
          <span>{isOllamaConnected ? 'CONNECTED' : 'STANDBY'}</span>
        </div>

        {/* Sovereign Mode Badge */}
        <div className="hidden lg:flex items-center space-x-1 px-2.5 py-1 rounded bg-cyan-950/20 border border-cyan-500/30 text-[11px] font-mono text-cyan-400">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>100% LOCAL</span>
        </div>

        {/* Refresh Diagnostics */}
        <button
          onClick={onRefresh}
          disabled={isChecking}
          className="p-2 rounded bg-slate-900/60 border border-slate-700/60 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition-colors disabled:opacity-50"
          title="Refresh diagnostics"
        >
          <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin text-cyan-400' : ''}`} />
        </button>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="p-2 rounded bg-slate-900/60 border border-slate-700/60 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition-colors"
          title="Configure System Settings"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
