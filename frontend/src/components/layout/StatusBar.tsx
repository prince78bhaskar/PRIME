import React from 'react';
import { Database, ShieldCheck, Cpu } from 'lucide-react';
import { BackendHealth, OllamaHealth } from '../../types';

interface StatusBarProps {
  backendHealth: BackendHealth | null;
  ollamaHealth: OllamaHealth | null;
  selectedModel: string;
  isStreaming: boolean;
  lastTokens?: number;
  lastDurationMs?: number;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  backendHealth,
  ollamaHealth,
  selectedModel,
  isStreaming,
  lastTokens,
  lastDurationMs,
}) => {
  return (
    <footer className="h-8 border-t border-cyan-500/20 bg-hud-panel/95 backdrop-blur px-4 flex items-center justify-between text-[11px] font-mono text-slate-400 select-none z-20">
      <div className="flex items-center space-x-4">
        {/* Active Model Indicator */}
        <div className="flex items-center space-x-1.5 text-cyan-300">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>MODEL:</span>
          <span className="text-white font-semibold truncate max-w-[200px]">
            {selectedModel}
          </span>
        </div>

        {/* Database WAL Status */}
        <div className="hidden sm:flex items-center space-x-1.5 text-slate-400">
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span>SQLITE:</span>
          <span className={backendHealth?.database === 'connected' ? 'text-emerald-400' : 'text-rose-400'}>
            {backendHealth?.database === 'connected' ? 'WAL ACTIVE' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Ollama Status */}
        <div className="hidden md:flex items-center space-x-1.5 text-slate-400">
          <span className="text-slate-600">|</span>
          <span>DAEMON:</span>
          <span className={ollamaHealth?.isConnected ? 'text-cyan-400' : 'text-amber-400'}>
            {ollamaHealth?.isConnected ? '127.0.0.1:11434' : 'OFFLINE'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Token metrics if generated */}
        {isStreaming ? (
          <div className="flex items-center space-x-1.5 text-cyan-400 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span>INFERENCE RUNNING...</span>
          </div>
        ) : lastTokens !== undefined && lastDurationMs !== undefined ? (
          <div className="hidden md:flex items-center space-x-2 text-slate-400">
            <span>LAST: {lastTokens} tokens</span>
            <span className="text-slate-600">/</span>
            <span>{lastDurationMs}ms</span>
            {lastDurationMs > 0 && (
              <span className="text-cyan-400">
                ({((lastTokens / (lastDurationMs / 1000))).toFixed(1)} t/s)
              </span>
            )}
          </div>
        ) : null}

        {/* Airgap Notice */}
        <div className="flex items-center space-x-1 text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-500/60" />
          <span className="hidden lg:inline">AIRGAP PROTECTED • ZERO CLOUD LEAK</span>
        </div>
      </div>
    </footer>
  );
};
