import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { voiceApi } from '../../services/voiceApi';
import { VoiceLanguage, VoiceStatus } from '../../types';

interface VoiceControlsProps {
  language: VoiceLanguage;
  disabled: boolean;
  onLanguageChange: (language: VoiceLanguage) => void;
  onTranscript: (transcript: string) => void;
}

const MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4',
];

function microphoneError(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
      return 'Microphone permission was denied. Allow microphone access in the browser, then try again.';
    }
    if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      return 'No microphone was found. Connect or enable a microphone and try again.';
    }
    if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
      return 'The microphone is busy or unavailable. Close other recording apps and try again.';
    }
  }
  return error instanceof Error ? error.message : 'Unable to start microphone capture.';
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  language,
  disabled,
  onLanguageChange,
  onTranscript,
}) => {
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isRequesting, setIsRequesting] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [notice, setNotice] = useState('');
  const pressedRef = useRef(false);
  const requestingRef = useRef(false);
  const cancelledRef = useRef(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    voiceApi.getStatus().then((status) => {
      if (mountedRef.current) setVoiceStatus(status);
    }).catch(() => {
      if (mountedRef.current) setVoiceStatus(null);
    });
    return () => {
      mountedRef.current = false;
      pressedRef.current = false;
      cancelledRef.current = true;
      recorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const beginRecording = async () => {
    if (pressedRef.current || requestingRef.current || disabled || isTranscribing) return;
    pressedRef.current = true;
    requestingRef.current = true;
    cancelledRef.current = false;
    setNotice('');
    setIsRequesting(true);
    try {
      voiceApi.ensureLocal();
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        throw new Error('This browser does not support local microphone recording.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      if (!pressedRef.current || !mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      const mimeType = MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      chunksRef.current = [];
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        cancelledRef.current = true;
        setNotice('Microphone capture was interrupted. Please try again.');
        if (recorder.state !== 'inactive') recorder.stop();
      };
      stream.getAudioTracks().forEach((track) => {
        track.addEventListener('ended', () => {
          if (!pressedRef.current) return;
          pressedRef.current = false;
          cancelledRef.current = true;
          setNotice('Microphone capture was interrupted. Please try again.');
          if (recorder.state !== 'inactive') recorder.stop();
        }, { once: true });
      });
      recorder.onstop = () => {
        const recording = new Blob(chunksRef.current, {
          type: recorder.mimeType || mimeType || 'audio/webm',
        });
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        recorderRef.current = null;
        chunksRef.current = [];
        if (mountedRef.current) setIsRecording(false);
        if (cancelledRef.current) return;
        if (!recording.size) {
          setNotice('No audio was captured. Hold the button while speaking.');
          return;
        }
        setIsTranscribing(true);
        voiceApi
          .transcribe(recording, language)
          .then((transcript) => {
            if (!mountedRef.current) return;
            if (!transcript.trim()) {
              setNotice('No speech was recognized. Try again in a quieter environment.');
              return;
            }
            setNotice('Transcript sent to the local chat model.');
            onTranscript(transcript.trim());
          })
          .catch((error: unknown) => {
            if (mountedRef.current) {
              setNotice(error instanceof Error ? error.message : 'Local transcription failed.');
            }
          })
          .finally(() => {
            if (mountedRef.current) setIsTranscribing(false);
          });
      };
      recorder.start();
      setIsRecording(true);
    } catch (error: unknown) {
      pressedRef.current = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (mountedRef.current) setNotice(microphoneError(error));
    } finally {
      requestingRef.current = false;
      if (mountedRef.current) setIsRequesting(false);
    }
  };

  const stopRecording = (cancel = false) => {
    pressedRef.current = false;
    if (cancel) cancelledRef.current = true;
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop();
    } else if (!recorder) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setIsRecording(false);
    }
  };

  useEffect(() => {
    const interrupt = () => {
      if (!pressedRef.current) return;
      setNotice('Microphone capture was interrupted and discarded. Please try again.');
      stopRecording(true);
    };
    window.addEventListener('blur', interrupt);
    document.addEventListener('visibilitychange', interrupt);
    return () => {
      window.removeEventListener('blur', interrupt);
      document.removeEventListener('visibilitychange', interrupt);
    };
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (event.detail !== 0) return;
    if (pressedRef.current) stopRecording();
    else void beginRecording();
  };

  const modelReady = voiceStatus?.stt_ready === true;

  return (
    <div className="flex items-center gap-1.5">
      <label className="sr-only" htmlFor="voice-language">Speech language</label>
      <select
        id="voice-language"
        value={language}
        onChange={(event) => onLanguageChange(event.target.value as VoiceLanguage)}
        disabled={isRecording || isTranscribing}
        className="bg-slate-950 border border-cyan-500/30 text-cyan-300 text-[10px] rounded px-1.5 py-2.5 font-mono focus:outline-none focus:border-cyan-400 disabled:opacity-50"
        title="Speech recognition and voice language"
      >
        <option value="en">EN</option>
        <option value="hi">HI</option>
      </select>
      <button
        type="button"
        onPointerDown={(event) => {
          event.preventDefault();
          event.currentTarget.setPointerCapture(event.pointerId);
          void beginRecording();
        }}
        onPointerUp={() => stopRecording()}
        onPointerCancel={() => {
          setNotice('Microphone capture was interrupted and discarded. Please try again.');
          stopRecording(true);
        }}
        onLostPointerCapture={() => {
          if (pressedRef.current) {
            setNotice('Microphone capture was interrupted and discarded. Please try again.');
            stopRecording(true);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            if (!pressedRef.current) void beginRecording();
          }
        }}
        onKeyUp={(event) => {
          if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            stopRecording();
          }
        }}
        onClick={handleClick}
        disabled={disabled || isTranscribing}
        aria-label={
          isRecording
            ? 'Recording. Release to transcribe.'
            : isRequesting
            ? 'Waiting for microphone permission'
            : 'Hold to speak'
        }
        aria-pressed={isRecording}
        title="Hold to speak. Microphone permission is requested only when pressed."
        className={`p-2.5 rounded-lg border font-mono transition-colors disabled:opacity-40 ${
          isRecording
            ? 'bg-rose-700 border-rose-400 text-white animate-pulse'
            : 'bg-slate-950 border-cyan-500/30 text-cyan-300 hover:border-cyan-400'
        }`}
      >
        {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>
      <span className="sr-only" role="status" aria-live="polite">
        {notice}
      </span>
      <span
        className="hidden md:inline text-[9px] font-mono text-slate-500"
        title={notice || (modelReady ? 'Local speech recognition is ready' : 'Download local voice models first')}
      >
        {isRecording
          ? 'RECORDING'
          : isRequesting
          ? 'MIC PERMISSION'
          : isTranscribing
          ? 'TRANSCRIBING'
          : modelReady
          ? 'LOCAL MIC'
          : 'VOICE SETUP'}
      </span>
    </div>
  );
};
