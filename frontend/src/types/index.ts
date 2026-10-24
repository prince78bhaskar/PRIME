export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  evalCount?: number;
  durationMs?: number;
  isStreaming?: boolean;
  error?: boolean;
}

export type ConnectionStatus = 'checking' | 'connected' | 'unavailable' | 'degraded';

export interface BackendHealth {
  status: 'healthy' | 'degraded' | 'offline';
  version: string;
  environment: string;
  database: 'connected' | 'disconnected' | 'error';
  uptimeSeconds: number | null;
}

export interface OllamaHealth {
  status: ConnectionStatus;
  baseUrl: string;
  defaultModel: string;
  isConnected: boolean;
  isDefaultModelInstalled: boolean;
  availableModels: string[];
  error: string | null;
}

export type VoiceLanguage = 'en' | 'hi';

export interface VoiceStatus {
  stt_ready: boolean;
  stt_model_present: boolean;
  stt_runtime_installed: boolean;
  tts_runtime_installed: boolean;
  tts_models: Record<string, boolean>;
  tts_ready_languages: string[];
}

export interface AppSettings {
  apiBaseUrl: string;
  ollamaModel: string;
  temperature: number;
  maxTokens: number;
  stream: boolean;
  soundEffects: boolean;
}

export type ActiveTab = 'command' | 'agents' | 'tasks' | 'settings';
