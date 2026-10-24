"""Offline speech-to-text and text-to-speech services."""

import importlib.util
import logging
import tempfile
import threading
import wave
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)

_STT_MODEL_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")


class VoiceServiceError(Exception):
    """Base class for expected local voice pipeline failures."""


class VoiceModelMissingError(VoiceServiceError):
    """A locally configured voice model is not present."""


class VoiceDependencyMissingError(VoiceServiceError):
    """An optional local voice runtime has not been installed."""


class VoiceProcessingError(VoiceServiceError):
    """Local audio processing failed."""


class VoiceService:
    """Loads local voice models lazily and never calls an external service."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._whisper_model = None
        self._piper_voices: dict[str, object] = {}
        self._lock = threading.RLock()

    def status(self) -> dict[str, object]:
        """Report local model and runtime availability without loading models."""
        stt_model_present = self._stt_model_present()
        stt_runtime_installed = importlib.util.find_spec("faster_whisper") is not None
        piper_installed = importlib.util.find_spec("piper") is not None
        tts_models = {
            language: self._tts_model_path(language).is_file()
            and self._tts_config_path(language).is_file()
            for language in ("en", "hi")
        }
        return {
            "stt_ready": stt_model_present and stt_runtime_installed,
            "stt_model_present": stt_model_present,
            "stt_runtime_installed": stt_runtime_installed,
            "tts_runtime_installed": piper_installed,
            "tts_models": tts_models,
            "tts_ready_languages": [
                language
                for language, model_present in tts_models.items()
                if model_present and piper_installed
            ],
        }

    def transcribe(self, audio: bytes, suffix: str, language: str) -> str:
        """Transcribe an audio recording using only a local Faster-Whisper model."""
        if not self._stt_model_present():
            raise VoiceModelMissingError("Faster-Whisper model files are missing.")
        if importlib.util.find_spec("faster_whisper") is None:
            raise VoiceDependencyMissingError("Install the optional faster-whisper voice dependency.")

        try:
            with self._lock:
                model = self._get_whisper_model()
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
                    audio_path = Path(audio_file.name)
                    audio_file.write(audio)
                    audio_file.flush()
                try:
                    segments, _ = model.transcribe(
                        str(audio_path),
                        language=language,
                        vad_filter=False,
                    )
                    transcript = " ".join(segment.text.strip() for segment in segments).strip()
                finally:
                    audio_path.unlink(missing_ok=True)
            return transcript
        except VoiceServiceError:
            raise
        except Exception as exc:
            logger.exception("Local speech recognition failed")
            raise VoiceProcessingError("Audio could not be decoded or transcribed locally.") from exc

    def synthesize(self, text: str, language: str) -> bytes:
        """Synthesize a WAV response using a locally installed Piper voice."""
        model_path = self._tts_model_path(language)
        config_path = self._tts_config_path(language)
        if not model_path.is_file() or not config_path.is_file():
            language_name = {"en": "English", "hi": "Hindi"}[language]
            raise VoiceModelMissingError(f"The configured {language_name} Piper voice files are missing.")
        if importlib.util.find_spec("piper") is None:
            raise VoiceDependencyMissingError("Install the optional piper-tts voice dependency.")

        try:
            with self._lock:
                voice = self._get_piper_voice(language, model_path, config_path)
                with tempfile.SpooledTemporaryFile() as output:
                    with wave.open(output, "wb") as wav_file:
                        voice.synthesize_wav(text, wav_file)
                    output.seek(0)
                    return output.read()
        except VoiceServiceError:
            raise
        except Exception as exc:
            logger.exception("Local speech synthesis failed")
            raise VoiceProcessingError("Text could not be synthesized locally.") from exc

    def _get_whisper_model(self):
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise VoiceDependencyMissingError(
                    "Install the optional faster-whisper voice dependency."
                ) from exc
            self._whisper_model = WhisperModel(
                str(self.settings.voice_stt_model_path),
                device=self.settings.voice_stt_device,
                compute_type=self.settings.voice_stt_compute_type,
                local_files_only=True,
            )
        return self._whisper_model

    def _get_piper_voice(self, language: str, model_path: Path, config_path: Path):
        if language not in self._piper_voices:
            try:
                from piper import PiperVoice
            except ImportError as exc:
                raise VoiceDependencyMissingError(
                    "Install the optional piper-tts voice dependency."
                ) from exc
            self._piper_voices[language] = PiperVoice.load(
                str(model_path),
                config_path=str(config_path),
            )
        return self._piper_voices[language]

    def _tts_model_path(self, language: str) -> Path:
        return {
            "en": self.settings.voice_tts_en_model_path,
            "hi": self.settings.voice_tts_hi_model_path,
        }[language]

    def _tts_config_path(self, language: str) -> Path:
        return self._tts_model_path(language).with_suffix(".onnx.json")

    def _stt_model_present(self) -> bool:
        model_path = self.settings.voice_stt_model_path
        return model_path.is_dir() and all((model_path / name).is_file() for name in _STT_MODEL_FILES)
