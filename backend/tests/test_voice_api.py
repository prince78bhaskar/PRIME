"""Integration tests for the local voice HTTP pipeline using isolated adapters."""


from app.api.voice import get_voice_service
from app.core.voice_service import VoiceService


class FakeVoiceService:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.transcription = ("recognized locally", None)
        self.synthesis = b"RIFF-local-wav"
        self.transcribe_calls = []
        self.synthesize_calls = []

    def status(self):
        return {
            "stt_ready": True,
            "stt_model_present": True,
            "stt_runtime_installed": True,
            "tts_runtime_installed": True,
            "tts_models": {"en": True, "hi": True},
            "tts_ready_languages": ["en", "hi"],
        }

    def transcribe(self, audio, suffix, language):
        self.transcribe_calls.append((audio, suffix, language))
        return self.transcription[0]

    def synthesize(self, text, language):
        self.synthesize_calls.append((text, language))
        return self.synthesis


def _fake_service(client) -> FakeVoiceService:
    service = FakeVoiceService(client.app.state.settings)
    client.app.dependency_overrides[get_voice_service] = lambda: service
    return service


def test_voice_status_reports_local_readiness(client) -> None:
    service = _fake_service(client)

    response = client.get("/api/v1/voice/status")

    assert response.status_code == 200
    assert response.json()["tts_ready_languages"] == ["en", "hi"]
    assert service.status()["stt_ready"] is True


def test_transcribe_passes_recording_to_local_adapter(client) -> None:
    service = _fake_service(client)

    response = client.post(
        "/api/v1/voice/transcribe?language=hi",
        content=b"recorded-audio",
        headers={"content-type": "audio/webm"},
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": "recognized locally", "language": "hi"}
    assert service.transcribe_calls == [(b"recorded-audio", ".webm", "hi")]


def test_transcribe_handles_empty_recording_and_unsupported_type(client) -> None:
    service = _fake_service(client)

    empty_response = client.post(
        "/api/v1/voice/transcribe",
        content=b"",
        headers={"content-type": "audio/webm"},
    )
    type_response = client.post(
        "/api/v1/voice/transcribe",
        content=b"audio",
        headers={"content-type": "application/json"},
    )

    assert empty_response.status_code == 400
    assert type_response.status_code == 415
    assert service.transcribe_calls == []


def test_transcribe_enforces_configured_recording_limit(client) -> None:
    service = _fake_service(client)
    client.app.state.settings.voice_max_audio_bytes = 4

    response = client.post(
        "/api/v1/voice/transcribe",
        content=b"12345",
        headers={"content-type": "audio/webm"},
    )

    assert response.status_code == 413
    assert service.transcribe_calls == []


def test_missing_local_models_return_service_unavailable(client, tmp_path) -> None:
    settings = client.app.state.settings
    settings.voice_stt_model_path = tmp_path / "missing-whisper"
    settings.voice_tts_en_model_path = tmp_path / "missing-en.onnx"
    service = VoiceService(settings)
    client.app.dependency_overrides[get_voice_service] = lambda: service

    transcription = client.post(
        "/api/v1/voice/transcribe",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )
    synthesis = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language": "en"},
    )

    assert transcription.status_code == 503
    assert "model files are missing" in transcription.json()["detail"]
    assert synthesis.status_code == 503
    assert "English Piper voice files are missing" in synthesis.json()["detail"]


def test_synthesize_returns_local_wav_response(client) -> None:
    service = _fake_service(client)

    response = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language": "en"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFF-local-wav"
    assert service.synthesize_calls == [("Hello", "en")]


def test_local_voice_api_round_trip(client) -> None:
    service = _fake_service(client)

    transcription = client.post(
        "/api/v1/voice/transcribe?language=en",
        content=b"local-microphone-audio",
        headers={"content-type": "audio/webm"},
    )
    synthesis = client.post(
        "/api/v1/voice/synthesize",
        json={"text": transcription.json()["transcript"], "language": "en"},
    )

    assert transcription.status_code == 200
    assert synthesis.status_code == 200
    assert service.transcribe_calls == [(b"local-microphone-audio", ".webm", "en")]
    assert service.synthesize_calls == [("recognized locally", "en")]


def test_synthesize_rejects_blank_and_oversized_text(client) -> None:
    service = _fake_service(client)
    client.app.state.settings.voice_max_text_chars = 3

    blank = client.post("/api/v1/voice/synthesize", json={"text": "  ", "language": "en"})
    oversized = client.post("/api/v1/voice/synthesize", json={"text": "Hello", "language": "en"})

    assert blank.status_code == 422
    assert oversized.status_code == 413
    assert service.synthesize_calls == []
