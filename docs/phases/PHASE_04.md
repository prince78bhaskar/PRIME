# Phase 04: Local Voice Interaction

**Status**: Implemented; local model and physical-microphone acceptance test pending  
**Date**: 2026-10-25

## Scope

Phase 04 adds explicit push-to-talk microphone capture to the React chat, local speech recognition with Faster-Whisper, and on-demand local speech playback with Piper. Voice has its own `/api/v1/voice` API and configuration, separate from the Ollama chat endpoint. It does not add a wake word, background listening, or cloud speech services.

## Pipeline

1. The user presses and holds the microphone control. Only then does the browser request `getUserMedia` permission and start a `MediaRecorder`.
2. Releasing the control uploads the recording to the local backend. A selected English (`en`) or Hindi (`hi`) language is passed to Faster-Whisper.
3. The locally configured `Systran/faster-whisper-small` model transcribes the audio on CPU with `int8` by default, preserving GPU memory for Ollama. The backend uses a local model directory only and does not download models at runtime.
4. A non-empty transcript is submitted through the existing chat callback. The user can play a completed assistant reply with the selected local Piper voice.
5. Piper returns WAV audio to the browser. The selected `en_US-lessac-medium` and `hi_IN-pratham-medium` voice files are local-only.

The app handles permission denial, missing/busy devices, unsupported browser recording, recording interruption, silence/empty transcript, audio decode errors, and missing runtime/model files. Recordings and synthesis requests are sent only to a loopback backend; the frontend blocks voice API URLs that are not `localhost`, `127.0.0.1`, or `::1`. STT recordings are bounded to 25 MiB by default and temporary files are removed after processing.

## Language Coverage

- The `Systran/faster-whisper-small` model repository advertises both English (`en`) and Hindi (`hi`).
- The Piper voice repository contains `en_US-lessac-medium` and `hi_IN-pratham-medium` ONNX voices and their required JSON configurations.
- The language inventory and model files are verified from their repositories; voice quality and recognition accuracy have not yet been measured on the target microphone/hardware.
- No Silero VAD or wake-word detector is enabled. Capture is push-to-talk only. Wake-word support is a separate optional task and must not be described as always-on.

## Configuration

All variables use the existing `PRIME_` prefix. Default model locations are under the project root:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PRIME_VOICE_STT_MODEL_PATH` | `models/faster-whisper-small` | Local Faster-Whisper model directory |
| `PRIME_VOICE_STT_DEVICE` | `cpu` | STT execution device (`cpu` or `cuda`) |
| `PRIME_VOICE_STT_COMPUTE_TYPE` | `int8` | CTranslate2 compute type |
| `PRIME_VOICE_TTS_EN_MODEL_PATH` | `models/voice/en_US-lessac-medium.onnx` | English Piper model |
| `PRIME_VOICE_TTS_HI_MODEL_PATH` | `models/voice/hi_IN-pratham-medium.onnx` | Hindi Piper model |
| `PRIME_VOICE_MAX_AUDIO_BYTES` | `26214400` | Maximum recording size |
| `PRIME_VOICE_MAX_TEXT_CHARS` | `5000` | Maximum TTS input length |

Install the optional runtimes in the backend environment:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -e ".[voice]"
```

## Download Models Before Offline Use

Model downloads require internet access once. Inference and playback thereafter use only local files.

Download the complete Faster-Whisper snapshot from Hugging Face into the expected local directory:

```powershell
cd backend
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-small', local_dir='../models/faster-whisper-small')"
```

Download the ONNX voice and matching JSON configuration for each language:

```powershell
New-Item -ItemType Directory -Force ..\models\voice | Out-Null
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true" -OutFile ..\models\voice\en_US-lessac-medium.onnx
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true" -OutFile ..\models\voice\en_US-lessac-medium.onnx.json
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx?download=true" -OutFile ..\models\voice\hi_IN-pratham-medium.onnx
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx.json?download=true" -OutFile ..\models\voice\hi_IN-pratham-medium.onnx.json
```

Alternatively, change the environment paths to files stored elsewhere. Never put model weights or recordings in source control. The API reports readiness at `GET /api/v1/voice/status`; absent files produce a clear service error, not an automatic download.

## Endpoint Reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/voice/status` | Report installed local runtimes and model-file readiness |
| `POST` | `/api/v1/voice/transcribe?language=en\|hi` | Accept raw local audio bytes and return a transcript |
| `POST` | `/api/v1/voice/synthesize` | Accept `{ "text": "...", "language": "en" }` and return WAV audio |

The STT route accepts WebM, Ogg, WAV, MP4, or MP3 audio. It has an explicit upload-size limit. No voice request is routed through Ollama or any external network service.

## Verification

Independent backend tests cover the model adapters with local fakes, missing model files, Hindi transcript output, silence, WAV output, API request validation, payload limits, and both HTTP directions. The frontend production build verifies the TypeScript UI integration.

### End-to-end acceptance test (run after model download)

1. Start the backend bound to loopback (`127.0.0.1`) and start the frontend on `127.0.0.1:5173`.
2. Confirm `GET http://127.0.0.1:8000/api/v1/voice/status` reports `stt_ready: true` and `tts_ready_languages` contains the voice being tested.
3. Open the local frontend, choose `EN`, press and hold the microphone button, allow microphone permission, say “Good morning, PRIME”, then release. Confirm the transcript is added as a user chat turn.
4. Repeat with `HI` and say “नमस्ते, प्राइम”. Confirm a non-empty Hindi transcript and chat turn.
5. Click **SPEAK** on a completed assistant response in each language. Confirm audio plays locally and both transcripts and synthesized WAV responses remain on loopback.
6. Reload and deny microphone permission; verify the explicit permission-denied message. Repeat without a microphone, with silence, while navigating away during capture, and with model files removed; verify the respective errors and confirm no silent chat submission.
7. Inspect browser network requests: voice paths must target loopback only. Repeat with the API base URL set to a non-loopback host and confirm the frontend rejects voice requests before sending audio.

**Execution record for this change:** all 87 backend tests pass, including mocked Faster-Whisper/Piper adapter tests and the HTTP API round-trip; the frontend production build passes. A real microphone/model acceptance run was not possible in this environment because Faster-Whisper/Piper and model weights are not installed. Do not mark the hardware acceptance test complete until steps 1–7 have been run on the target machine.

## Deferred

- Optional wake-word detection, only after a separate design and tested implementation.
- Measured Hindi/English recognition and speech-quality evaluation on target hardware.
- Browser-level manual test with actual microphone and downloaded voice assets.
