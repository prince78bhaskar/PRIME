import { VoiceLanguage, VoiceStatus } from '../types';

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]']);

export class VoiceApiService {
  private baseUrl = '';

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, '');
  }

  ensureLocal() {
    this.endpoint('/api/v1/voice/status');
  }

  async getStatus(): Promise<VoiceStatus> {
    const response = await fetch(this.endpoint('/api/v1/voice/status'));
    if (!response.ok) {
      throw await this.responseError(response);
    }
    return response.json();
  }

  async transcribe(audio: Blob, language: VoiceLanguage): Promise<string> {
    if (!audio.size) {
      throw new Error('The recording was empty. Hold the microphone button while speaking.');
    }
    const contentType = audio.type || 'audio/webm';
    const response = await fetch(
      `${this.endpoint('/api/v1/voice/transcribe')}?language=${language}`,
      {
        method: 'POST',
        headers: { 'Content-Type': contentType },
        body: audio,
      }
    );
    if (!response.ok) {
      throw await this.responseError(response);
    }
    const result: { transcript: string } = await response.json();
    return result.transcript;
  }

  async synthesize(text: string, language: VoiceLanguage): Promise<Blob> {
    const response = await fetch(this.endpoint('/api/v1/voice/synthesize'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!response.ok) {
      throw await this.responseError(response);
    }
    return response.blob();
  }

  private endpoint(path: string): string {
    const url = new URL(`${this.baseUrl}${path}`, window.location.href);
    if (!LOOPBACK_HOSTS.has(url.hostname.toLowerCase())) {
      throw new Error('Voice data is restricted to this computer. Use the local P.R.I.M.E. app.');
    }
    return url.toString();
  }

  private async responseError(response: Response): Promise<Error> {
    let message = `Local voice service returned HTTP ${response.status}.`;
    try {
      const body = await response.json();
      const detail = body.detail;
      if (typeof detail === 'string') message = detail;
      else if (typeof detail?.message === 'string') message = detail.message;
    } catch {
      // Keep the HTTP status when the server does not return JSON.
    }
    return new Error(message);
  }
}

export const voiceApi = new VoiceApiService();
