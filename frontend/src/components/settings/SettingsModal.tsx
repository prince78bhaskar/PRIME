import React, { useState } from 'react';
import { X, Sliders, Check, RotateCcw } from 'lucide-react';
import { AppSettings } from '../../types';

interface SettingsModalProps {
  isOpen: boolean;
  settings: AppSettings;
  availableModels: string[];
  onClose: () => void;
  onSave: (settings: AppSettings) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  settings,
  availableModels,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<AppSettings>(settings);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
    onClose();
  };

  const handleReset = () => {
    setFormData({
      apiBaseUrl: '',
      ollamaModel: 'qwen2.5:3b-instruct-q4_K_M',
      temperature: 0.7,
      maxTokens: 2048,
      stream: true,
      soundEffects: true,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm select-none">
      <div className="hud-panel hud-corner-brackets w-full max-w-lg rounded-2xl border border-cyan-500/40 p-6 space-y-6 shadow-glow-cyan">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-cyan-500/20">
          <div className="flex items-center space-x-2 text-cyan-400 font-display font-bold">
            <Sliders className="w-5 h-5" />
            <h2 className="text-base tracking-wider text-white">SYSTEM TELEMETRY CONFIGURATION</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          {/* API Base URL */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold">BACKEND API GATEWAY</label>
            <input
              type="text"
              value={formData.apiBaseUrl}
              onChange={(e) => setFormData({ ...formData, apiBaseUrl: e.target.value })}
              placeholder="http://127.0.0.1:8000 (or leave empty for relative)"
              className="w-full bg-slate-950 border border-cyan-500/30 text-cyan-300 rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
            />
            <p className="text-[10px] text-slate-500">
              Leave blank to use Vite development proxy to localhost:8000.
            </p>
          </div>

          {/* Model Selection */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold">DEFAULT LOCAL MODEL TAG</label>
            <input
              type="text"
              value={formData.ollamaModel}
              onChange={(e) => setFormData({ ...formData, ollamaModel: e.target.value })}
              className="w-full bg-slate-950 border border-cyan-500/30 text-cyan-300 rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
            />
            {availableModels.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                <span className="text-[10px] text-slate-500">Detected:</span>
                {availableModels.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setFormData({ ...formData, ollamaModel: m })}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 border border-cyan-500/20 text-cyan-400 hover:border-cyan-400"
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Temperature Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-300">
              <span className="font-semibold">TEMPERATURE (SAMPLING RANDOMNESS)</span>
              <span className="text-cyan-400">{formData.temperature.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.5"
              step="0.05"
              value={formData.temperature}
              onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
              className="w-full accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.0 (Deterministic / Code)</span>
              <span>1.5 (Creative)</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-300">
              <span className="font-semibold">MAX GENERATION TOKENS (4GB VRAM GUARD)</span>
              <span className="text-cyan-400">{formData.maxTokens}</span>
            </div>
            <input
              type="range"
              min="256"
              max="4096"
              step="256"
              value={formData.maxTokens}
              onChange={(e) => setFormData({ ...formData, maxTokens: parseInt(e.target.value) })}
              className="w-full accent-cyan-400"
            />
            <p className="text-[10px] text-slate-500">
              Capped at 4096 tokens to prevent VRAM buffer overflow on consumer GPUs.
            </p>
          </div>

          {/* Streaming Toggle */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <div>
              <div className="text-slate-200 font-semibold">SERVER-SENT EVENTS (SSE) STREAMING</div>
              <div className="text-[10px] text-slate-500">
                Stream token deltas in real-time as they are emitted by Ollama.
              </div>
            </div>
            <input
              type="checkbox"
              checked={formData.stream}
              onChange={(e) => setFormData({ ...formData, stream: e.target.checked })}
              className="w-4 h-4 accent-cyan-400"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-4 flex items-center justify-between border-t border-cyan-500/20">
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center space-x-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESET DEFAULTS</span>
            </button>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded border border-slate-700 text-slate-400 hover:text-white transition-colors text-xs"
              >
                CANCEL
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-black font-bold text-xs flex items-center space-x-1.5 transition-colors shadow-glow-cyan"
              >
                <Check className="w-3.5 h-3.5" />
                <span>APPLY CONFIG</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
