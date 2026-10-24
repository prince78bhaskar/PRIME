import { BackendHealth, OllamaHealth, ChatMessage } from '../types';

export class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, '');
  }

  async checkBackendHealth(signal?: AbortSignal): Promise<BackendHealth> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, { signal });
      if (!res.ok) {
        return {
          status: 'degraded',
          version: 'unknown',
          environment: 'unknown',
          database: 'error',
          uptimeSeconds: null,
        };
      }
      const data = await res.json();
      return {
        status: data.status,
        version: data.version,
        environment: data.environment,
        database: data.database,
        uptimeSeconds: data.uptime_seconds,
      };
    } catch {
      return {
        status: 'offline',
        version: 'offline',
        environment: 'offline',
        database: 'disconnected',
        uptimeSeconds: null,
      };
    }
  }

  async checkOllamaHealth(signal?: AbortSignal): Promise<OllamaHealth> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/ollama/health`, { signal });
      if (!res.ok) {
        return {
          status: 'unavailable',
          baseUrl: 'http://127.0.0.1:11434',
          defaultModel: 'qwen2.5:3b-instruct-q4_K_M',
          isConnected: false,
          isDefaultModelInstalled: false,
          availableModels: [],
          error: `HTTP ${res.status}: Backend error`,
        };
      }
      const data = await res.json();
      return {
        status: data.status,
        baseUrl: data.base_url,
        defaultModel: data.default_model,
        isConnected: data.is_connected,
        isDefaultModelInstalled: data.is_default_model_installed,
        availableModels: data.available_models || [],
        error: data.error,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed';
      return {
        status: 'unavailable',
        baseUrl: 'http://127.0.0.1:11434',
        defaultModel: 'qwen2.5:3b-instruct-q4_K_M',
        isConnected: false,
        isDefaultModelInstalled: false,
        availableModels: [],
        error: msg,
      };
    }
  }

  async fetchModels(signal?: AbortSignal): Promise<string[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/ollama/models`, { signal });
      if (!res.ok) return [];
      const data = await res.json();
      return (data.models || []).map((m: { name: string }) => m.name);
    } catch {
      return [];
    }
  }

  async sendChat(
    messages: { role: string; content: string }[],
    options: {
      model?: string;
      temperature?: number;
      stream?: boolean;
      signal?: AbortSignal;
      onChunk?: (chunk: string) => void;
      onDone?: (metrics: { evalCount?: number; durationMs?: number }) => void;
    }
  ): Promise<ChatMessage> {
    const payload = {
      messages,
      model: options.model,
      temperature: options.temperature ?? 0.7,
      stream: options.stream ?? true,
    };

    const res = await fetch(`${this.baseUrl}/api/v1/ollama/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: options.signal,
    });

    if (!res.ok) {
      let errorMsg = `Server error (HTTP ${res.status})`;
      try {
        const errorData = await res.json();
        if (errorData.detail?.message) {
          errorMsg = `${errorData.detail.message}: ${errorData.detail.detail || ''}`;
        }
      } catch {
        // Fallback to text error
      }
      throw new Error(errorMsg);
    }

    if (options.stream && res.body) {
      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullContent = '';
      let evalCount: number | undefined;
      let durationMs: number | undefined;
      let buffer = '';
      let eventType = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('event: ')) {
            eventType = trimmed.slice(7);
          } else if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            if (dataStr === '[DONE]') {
              eventType = '';
              continue;
            }
            let parsed: {
              message?: { content?: string } | string;
              eval_count?: number;
              total_duration_ms?: number;
              detail?: string;
            };
            try {
              parsed = JSON.parse(dataStr);
            } catch {
              if (eventType === 'error') throw new Error(dataStr);
              continue;
            }
            if (eventType === 'error') {
              const errorText = typeof parsed.message === 'string'
                ? `${parsed.message}${parsed.detail ? `: ${parsed.detail}` : ''}`
                : dataStr;
              throw new Error(errorText);
            }
            eventType = '';
            if (typeof parsed.message === 'object' && parsed.message.content) {
              fullContent += parsed.message.content;
              options.onChunk?.(parsed.message.content);
            }
            if (parsed.eval_count) evalCount = parsed.eval_count;
            if (parsed.total_duration_ms) durationMs = parsed.total_duration_ms;
          }
        }
      }

      options.onDone?.({ evalCount, durationMs });

      return {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: fullContent,
        timestamp: new Date().toLocaleTimeString(),
        evalCount,
        durationMs,
        isStreaming: false,
      };
    } else {
      const data = await res.json();
      return {
        id: crypto.randomUUID(),
        role: data.message.role,
        content: data.message.content,
        timestamp: new Date().toLocaleTimeString(),
        evalCount: data.eval_count,
        durationMs: data.total_duration_ms,
        isStreaming: false,
      };
    }
  }
}

export const api = new ApiService();
