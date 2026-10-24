import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { StatusBar } from './components/layout/StatusBar';
import { ArcReactorOrb } from './components/orb/ArcReactorOrb';
import { AudioWaveform } from './components/waveform/AudioWaveform';
import { ChatPanel } from './components/chat/ChatPanel';
import { AgentRoster } from './components/agents/AgentRoster';
import { TaskPlaceholders } from './components/tasks/TaskPlaceholders';
import { SettingsModal } from './components/settings/SettingsModal';
import { api } from './services/api';
import { voiceApi } from './services/voiceApi';
import {
  ActiveTab,
  AppSettings,
  BackendHealth,
  ChatMessage,
  OllamaHealth,
  VoiceLanguage,
} from './types';
import { HardDrive, Cpu, Shield, Zap } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('command');
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [ollamaHealth, setOllamaHealth] = useState<OllamaHealth | null>(null);
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [voiceLanguage, setVoiceLanguage] = useState<VoiceLanguage>('en');

  // App Settings
  const [settings, setSettings] = useState<AppSettings>({
    apiBaseUrl: '',
    ollamaModel: 'qwen2.5:3b-instruct-q4_K_M',
    temperature: 0.7,
    maxTokens: 2048,
    stream: true,
    soundEffects: true,
  });

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [lastMetrics, setLastMetrics] = useState<{ tokens?: number; durationMs?: number }>({});
  const abortControllerRef = useRef<AbortController | null>(null);
  const speechPlaybackRef = useRef<{ audio: HTMLAudioElement; url: string } | null>(null);

  useEffect(() => () => {
    if (speechPlaybackRef.current) {
      speechPlaybackRef.current.audio.pause();
      URL.revokeObjectURL(speechPlaybackRef.current.url);
      speechPlaybackRef.current = null;
    }
  }, []);

  // Poll Diagnostics
  const checkHealth = useCallback(async () => {
    setIsChecking(true);
    try {
      const [bHealth, oHealth, models] = await Promise.all([
        api.checkBackendHealth(),
        api.checkOllamaHealth(),
        api.fetchModels(),
      ]);
      setBackendHealth(bHealth);
      setOllamaHealth(oHealth);
      if (models.length > 0) {
        setAvailableModels(models);
        // If current model not in list, select first available
        if (!models.includes(settings.ollamaModel) && models.length > 0) {
          setSettings((prev) => ({ ...prev, ollamaModel: models[0] }));
        }
      }
    } finally {
      setIsChecking(false);
    }
  }, [settings.ollamaModel]);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 30s auto check
    return () => clearInterval(interval);
  }, [checkHealth]);

  // Handle Send Message
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);

    const assistantMsgId = crypto.randomUUID();
    const assistantPlaceholder: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantPlaceholder]);

    abortControllerRef.current = new AbortController();

    try {
      // Build conversation history for context
      const history = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      await api.sendChat(history, {
        model: settings.ollamaModel,
        temperature: settings.temperature,
        stream: settings.stream,
        signal: abortControllerRef.current.signal,
        onChunk: (chunk: string) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, content: m.content + chunk } : m
            )
          );
        },
        onDone: (metrics) => {
          setLastMetrics({ tokens: metrics.evalCount, durationMs: metrics.durationMs });
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    isStreaming: false,
                    evalCount: metrics.evalCount,
                    durationMs: metrics.durationMs,
                  }
                : m
            )
          );
        },
      });
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: m.content + '\n\n[Inference stream aborted by user]',
                  isStreaming: false,
                }
              : m
          )
        );
      } else {
        const errorText = err instanceof Error ? err.message : 'Inference failed';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: `[Ollama Error]: ${errorText}`,
                  error: true,
                  isStreaming: false,
                }
              : m
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  // Cancel Stream
  const handleCancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  // Clear Messages
  const handleClearMessages = () => {
    setMessages([]);
    setLastMetrics({});
  };

  const handleSpeak = async (text: string, language: VoiceLanguage) => {
    if (speechPlaybackRef.current) {
      speechPlaybackRef.current.audio.pause();
      URL.revokeObjectURL(speechPlaybackRef.current.url);
      speechPlaybackRef.current = null;
    }
    const audioBlob = await voiceApi.synthesize(text, language);
    const url = URL.createObjectURL(audioBlob);
    const audio = new Audio(url);
    speechPlaybackRef.current = { audio, url };
    audio.onended = () => {
      URL.revokeObjectURL(url);
      if (speechPlaybackRef.current?.audio === audio) speechPlaybackRef.current = null;
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      if (speechPlaybackRef.current?.audio === audio) speechPlaybackRef.current = null;
    };
    try {
      await audio.play();
    } catch (error: unknown) {
      URL.revokeObjectURL(url);
      speechPlaybackRef.current = null;
      throw new Error(
        error instanceof Error && error.name === 'NotAllowedError'
          ? 'Browser blocked audio playback. Press SPEAK again to allow audio.'
          : error instanceof Error
          ? error.message
          : 'Unable to play the local speech response.'
      );
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-hud-bg text-slate-100 font-sans scanline-overlay">
      {/* Top HUD Header */}
      <Header
        backendHealth={backendHealth}
        ollamaHealth={ollamaHealth}
        isChecking={isChecking}
        onRefresh={checkHealth}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Body with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Nav */}
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Tab Views */}
        <main className="flex-1 overflow-y-auto p-3 lg:p-5 flex flex-col">
          {activeTab === 'command' && (
            <div className="flex-1 grid grid-cols-1 xl:grid-cols-12 gap-4 h-full min-h-[500px]">
              {/* Left Column: Arc Reactor Core, Waveform & Telemetry */}
              <div className="xl:col-span-5 flex flex-col space-y-4">
                {/* Central Arc Core Display */}
                <div className="hud-panel hud-corner-brackets rounded-xl p-4 flex flex-col items-center justify-center flex-1 min-h-[320px]">
                  <ArcReactorOrb
                    isStreaming={isStreaming}
                    isConnected={ollamaHealth?.isConnected === true}
                    hasError={backendHealth?.status === 'offline'}
                  />

                  {/* Hardware Envelope Summary Box */}
                  <div className="w-full mt-4 grid grid-cols-3 gap-2 pt-4 border-t border-cyan-500/15 text-center text-xs font-mono">
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-500 text-[10px]">VRAM BUDGET</div>
                      <div className="text-cyan-400 font-bold">2.2 GB / 4 GB</div>
                    </div>
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-500 text-[10px]">SYSTEM RAM</div>
                      <div className="text-amber-400 font-bold">16 GB DDR</div>
                    </div>
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-500 text-[10px]">QUANTIZATION</div>
                      <div className="text-emerald-400 font-bold">Q4_K_M</div>
                    </div>
                  </div>
                </div>

                {/* Audio Waveform Area */}
                <AudioWaveform isActive={isStreaming} />

                {/* Quick Diagnostics Strip */}
                <div className="hud-panel hud-corner-brackets p-3 rounded-xl grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                  <div className="flex items-center space-x-2 text-slate-300">
                    <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                    <span>OLLAMA: {ollamaHealth?.isConnected ? 'ONLINE' : 'OFFLINE'}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-slate-300">
                    <HardDrive className="w-3.5 h-3.5 text-amber-400" />
                    <span>SQLITE: WAL</span>
                  </div>
                  <div className="flex items-center space-x-2 text-slate-300">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    <span>SOVEREIGN: 100%</span>
                  </div>
                  <div className="flex items-center space-x-2 text-slate-300">
                    <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                    <span>TIER: T1 DIRECT</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Chat Console */}
              <div className="xl:col-span-7 flex flex-col h-full min-h-[420px]">
                <ChatPanel
                  messages={messages}
                  isStreaming={isStreaming}
                  selectedModel={settings.ollamaModel}
                  availableModels={availableModels}
                  ollamaHealth={ollamaHealth}
                  onSendMessage={handleSendMessage}
                  onCancelStream={handleCancelStream}
                  onClearMessages={handleClearMessages}
                  onSelectModel={(model) => setSettings((prev) => ({ ...prev, ollamaModel: model }))}
                  voiceLanguage={voiceLanguage}
                  onVoiceLanguageChange={setVoiceLanguage}
                  onSpeak={handleSpeak}
                />
              </div>
            </div>
          )}

          {activeTab === 'agents' && <AgentRoster />}

          {activeTab === 'tasks' && <TaskPlaceholders />}

          {activeTab === 'settings' && (
            <div className="max-w-2xl mx-auto w-full py-4">
              <div className="hud-panel hud-corner-brackets p-6 rounded-2xl space-y-4">
                <h2 className="font-display font-bold text-lg text-cyan-300">
                  P.R.I.M.E. SYSTEM CONFIGURATION
                </h2>
                <p className="text-xs font-mono text-slate-400">
                  Configure local runtime endpoints, model parameters, and hardware safety bounds.
                </p>
                <button
                  onClick={() => setIsSettingsOpen(true)}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-black font-mono font-bold text-xs transition-colors shadow-glow-cyan"
                >
                  OPEN CONFIGURATION MODAL
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Bottom Telemetry Bar */}
      <StatusBar
        backendHealth={backendHealth}
        ollamaHealth={ollamaHealth}
        selectedModel={settings.ollamaModel}
        isStreaming={isStreaming}
        lastTokens={lastMetrics.tokens}
        lastDurationMs={lastMetrics.durationMs}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        settings={settings}
        availableModels={availableModels}
        onClose={() => setIsSettingsOpen(false)}
        onSave={(newSettings) => {
          setSettings(newSettings);
          api.setBaseUrl(newSettings.apiBaseUrl);
          voiceApi.setBaseUrl(newSettings.apiBaseUrl);
        }}
      />
    </div>
  );
};
