import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Trash2, AlertCircle, Bot, User, Sparkles, Terminal, Volume2 } from 'lucide-react';
import { ChatMessage, OllamaHealth, VoiceLanguage } from '../../types';
import { VoiceControls } from './VoiceControls';

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  selectedModel: string;
  availableModels: string[];
  ollamaHealth: OllamaHealth | null;
  onSendMessage: (content: string) => void;
  onCancelStream: () => void;
  onClearMessages: () => void;
  onSelectModel: (model: string) => void;
  voiceLanguage: VoiceLanguage;
  onVoiceLanguageChange: (language: VoiceLanguage) => void;
  onSpeak: (text: string, language: VoiceLanguage) => Promise<void>;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  selectedModel,
  availableModels,
  ollamaHealth,
  onSendMessage,
  onCancelStream,
  onClearMessages,
  onSelectModel,
  voiceLanguage,
  onVoiceLanguageChange,
  onSpeak,
}) => {
  const [input, setInput] = useState('');
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [speechNotice, setSpeechNotice] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const isOllamaConnected = ollamaHealth?.isConnected === true;

  const handleSpeak = async (messageId: string, text: string) => {
    setSpeechNotice('');
    setSpeakingMessageId(messageId);
    try {
      await onSpeak(text, voiceLanguage);
    } catch (error: unknown) {
      setSpeechNotice(error instanceof Error ? error.message : 'Local speech synthesis failed.');
    } finally {
      setSpeakingMessageId(null);
    }
  };

  return (
    <div className="hud-panel hud-corner-brackets rounded-xl flex flex-col h-full overflow-hidden">
      {/* Chat Header Console */}
      <div className="px-4 py-3 border-b border-cyan-500/20 bg-slate-900/60 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Terminal className="w-4 h-4" />
          <span className="font-bold tracking-widest font-display text-sm">PRIME CONSOLE</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400">LOCAL LLM LINK</span>
        </div>

        <div className="flex items-center space-x-3">
          {/* Model Selector Dropdown */}
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 text-[10px] hidden sm:inline">TARGET:</span>
            <select
              value={selectedModel}
              onChange={(e) => onSelectModel(e.target.value)}
              disabled={isStreaming}
              className="bg-slate-950 border border-cyan-500/30 text-cyan-300 text-xs rounded px-2 py-1 font-mono focus:outline-none focus:border-cyan-400 transition-colors disabled:opacity-50"
            >
              {availableModels.length > 0 ? (
                availableModels.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))
              ) : (
                <option value={selectedModel}>{selectedModel}</option>
              )}
            </select>
          </div>

          {/* Clear Button */}
          <button
            onClick={onClearMessages}
            disabled={messages.length === 0 || isStreaming}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors disabled:opacity-30"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Ollama Disconnected Warning Banner */}
      {!isOllamaConnected && (
        <div className="px-4 py-2.5 bg-amber-950/40 border-b border-amber-500/30 text-amber-300 text-xs font-mono flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold">LOCAL OLLAMA DAEMON STANDBY</div>
            <div className="text-[11px] text-amber-200/80">
              Run <code className="bg-amber-900/50 px-1 py-0.2 rounded text-white font-mono">ollama serve</code> and{' '}
              <code className="bg-amber-900/50 px-1 py-0.2 rounded text-white font-mono">ollama pull {selectedModel}</code>{' '}
              to enable sovereign inference.
            </div>
          </div>
        </div>
      )}

      {/* Message Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 text-slate-400 select-none">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-glow-cyan">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div className="max-w-md space-y-1">
              <h3 className="font-display font-bold text-sm tracking-widest text-cyan-300">
                P.R.I.M.E. DIRECT LINK READY
              </h3>
              <p className="text-xs font-mono text-slate-400 leading-relaxed">
                Execute local queries through Ollama. All prompt tokens are processed 100% on this machine with strict 4GB VRAM hardware bounds.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {[
                'Report system diagnostic telemetry',
                'What are your hardware bounds?',
                'Explain your multi-agent architecture',
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(suggestion)}
                  disabled={!isOllamaConnected}
                  className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-cyan-500/20 hover:border-cyan-400/50 text-xs font-mono text-slate-300 hover:text-cyan-300 transition-colors disabled:opacity-40"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`flex items-start space-x-2 max-w-[85%] ${
                  msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar Icon */}
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
                    msg.role === 'user'
                      ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
                      : msg.error
                      ? 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                      : 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300 shadow-glow-cyan'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User className="w-3.5 h-3.5" />
                  ) : (
                    <Bot className="w-3.5 h-3.5" />
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`px-3.5 py-2.5 rounded-xl border text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-cyan-950/30 border-cyan-500/30 text-slate-100'
                      : msg.error
                      ? 'bg-rose-950/30 border-rose-500/30 text-rose-200 font-mono text-xs'
                      : 'bg-slate-900/80 border-slate-700/60 text-slate-100'
                  }`}
                >
                  {msg.content}
                  {msg.isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-cyan-400 animate-pulse align-middle" />
                  )}
                </div>
              </div>

              {/* Message Metadata (Tokens & Timing) */}
              <div
                className={`mt-1 flex items-center space-x-2 text-[10px] font-mono text-slate-500 px-9 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <span>{msg.timestamp}</span>
                {msg.role === 'assistant' && msg.content.trim() && !msg.isStreaming && !msg.error && (
                  <button
                    type="button"
                    onClick={() => void handleSpeak(msg.id, msg.content)}
                    disabled={speakingMessageId !== null}
                    className="inline-flex items-center gap-1 rounded text-cyan-400 hover:text-cyan-200 disabled:opacity-50"
                    title={`Speak with the local ${voiceLanguage === 'hi' ? 'Hindi' : 'English'} voice`}
                    aria-label="Play assistant response using local speech"
                  >
                    <Volume2 className="w-3 h-3" />
                    {speakingMessageId === msg.id ? 'SPEAKING' : 'SPEAK'}
                  </button>
                )}
                {msg.evalCount !== undefined && msg.durationMs !== undefined && (
                  <>
                    <span>•</span>
                    <span className="text-cyan-400/80">
                      {msg.evalCount} tok ({msg.durationMs}ms)
                    </span>
                  </>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSubmit}
        className="p-3 border-t border-cyan-500/20 bg-slate-900/80 flex items-center space-x-2"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isStreaming
              ? 'P.R.I.M.E. is streaming response...'
              : isOllamaConnected
              ? `Message P.R.I.M.E. (${selectedModel})...`
              : 'Ollama is offline — messages will trigger diagnostic check'
          }
          className="flex-1 bg-slate-950/80 border border-cyan-500/30 text-slate-100 placeholder-slate-500 text-xs sm:text-sm rounded-lg px-3 py-2.5 font-mono focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
        />

        <VoiceControls
          language={voiceLanguage}
          disabled={isStreaming}
          onLanguageChange={onVoiceLanguageChange}
          onTranscript={(transcript) => onSendMessage(transcript)}
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onCancelStream}
            className="px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs flex items-center space-x-1.5 transition-colors shadow-glow-crimson"
            title="Cancel Streaming Generation"
          >
            <Square className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">CANCEL</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-black font-mono font-bold text-xs flex items-center space-x-1.5 transition-all shadow-glow-cyan disabled:opacity-40 disabled:hover:bg-cyan-600 disabled:cursor-not-allowed"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">SEND</span>
          </button>
        )}
      </form>
      {speechNotice && (
        <div role="alert" className="px-3 pb-2 text-[10px] font-mono text-amber-300 bg-slate-900/80">
          {speechNotice}
        </div>
      )}
    </div>
  );
};
