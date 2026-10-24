"""Unit tests for the offline voice model adapters."""

import importlib.util
import io
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.voice_service import VoiceModelMissingError, VoiceService


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="testing",
        db_path=tmp_path / "memory" / "test.db",
        voice_stt_model_path=tmp_path / "whisper",
        voice_tts_en_model_path=tmp_path / "voices" / "en.onnx",
        voice_tts_hi_model_path=tmp_path / "voices" / "hi.onnx",
    )


def _create_stt_files(model_path: Path) -> None:
    model_path.mkdir()
    for name in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt"):
        (model_path / name).touch()


def test_transcribe_uses_local_recording_and_returns_text(tmp_path: Path, monkeypatch) -> None:
    model_path = tmp_path / "whisper"
    _create_stt_files(model_path)
    service = VoiceService(_settings(tmp_path))
    recorded = {}

    class FakeModel:
        def transcribe(self, path, **kwargs):
            recorded["audio"] = Path(path).read_bytes()
            recorded["suffix"] = Path(path).suffix
            recorded["kwargs"] = kwargs
            return iter([SimpleNamespace(text="नमस्ते"), SimpleNamespace(text="दुनिया")]), None

    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(service, "_get_whisper_model", lambda: FakeModel())

    transcript = service.transcribe(b"local-audio", ".webm", "hi")

    assert transcript == "नमस्ते दुनिया"
    assert recorded == {
        "audio": b"local-audio",
        "suffix": ".webm",
        "kwargs": {"language": "hi", "vad_filter": False},
    }


def test_transcribe_returns_empty_for_silence(tmp_path: Path, monkeypatch) -> None:
    _create_stt_files(tmp_path / "whisper")
    service = VoiceService(_settings(tmp_path))

    class FakeModel:
        def transcribe(self, path, **kwargs):
            return iter([]), None

    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(service, "_get_whisper_model", lambda: FakeModel())

    assert service.transcribe(b"silent-audio", ".wav", "en") == ""


def test_transcribe_reports_missing_model(tmp_path: Path) -> None:
    service = VoiceService(_settings(tmp_path))

    with pytest.raises(VoiceModelMissingError, match="model files are missing"):
        service.transcribe(b"audio", ".webm", "en")


def test_status_rejects_incomplete_stt_model_directory(tmp_path: Path) -> None:
    model_path = tmp_path / "whisper"
    model_path.mkdir()
    service = VoiceService(_settings(tmp_path))

    assert service.status()["stt_model_present"] is False


def test_synthesize_returns_wav_bytes(tmp_path: Path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.voice_tts_hi_model_path.parent.mkdir(parents=True)
    settings.voice_tts_hi_model_path.touch()
    settings.voice_tts_hi_model_path.with_suffix(".onnx.json").touch()
    service = VoiceService(settings)

    class FakeVoice:
        def synthesize_wav(self, text, output):
            assert text == "नमस्ते"
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(22050)
            output.writeframes(b"\x00\x00")

    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(
        service,
        "_get_piper_voice",
        lambda language, model_path, config_path: FakeVoice(),
    )

    audio = service.synthesize("नमस्ते", "hi")

    assert audio.startswith(b"RIFF")
    with wave.open(io.BytesIO(audio)) as output:
        assert output.getframerate() == 22050


def test_synthesize_reports_missing_voice_files(tmp_path: Path) -> None:
    service = VoiceService(_settings(tmp_path))

    with pytest.raises(VoiceModelMissingError, match="Hindi Piper voice files are missing"):
        service.synthesize("नमस्ते", "hi")
