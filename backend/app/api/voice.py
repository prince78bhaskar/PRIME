"""Offline speech recognition and synthesis endpoints."""

import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.voice_service import (
    VoiceDependencyMissingError,
    VoiceModelMissingError,
    VoiceProcessingError,
    VoiceService,
    VoiceServiceError,
)
from app.schemas.voice import (
    SynthesisRequest,
    TranscriptionResponse,
    VoiceLanguage,
    VoiceStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

_AUDIO_SUFFIXES = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "application/octet-stream": ".audio",
}


def get_voice_service(request: Request) -> VoiceService:
    """Return the lazy local voice service from application state."""
    service = getattr(request.app.state, "voice_service", None)
    if service is None:
        settings: Settings = getattr(request.app.state, "settings", get_settings())
        service = VoiceService(settings)
        request.app.state.voice_service = service
    return service


@router.get("/status", response_model=VoiceStatusResponse, summary="Local voice model readiness")
async def voice_status(
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> VoiceStatusResponse:
    return VoiceStatusResponse(**service.status())


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe a local microphone recording",
    responses={
        413: {"description": "Recording exceeds the configured size limit"},
        415: {"description": "Unsupported recording format"},
        503: {"description": "Local model or voice dependency is missing"},
    },
)
async def transcribe_audio(
    request: Request,
    service: Annotated[VoiceService, Depends(get_voice_service)],
    language: VoiceLanguage = "en",
) -> TranscriptionResponse:
    """Transcribe posted microphone audio without forwarding it outside this machine."""
    settings: Settings = request.app.state.settings
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    suffix = _AUDIO_SUFFIXES.get(content_type)
    if suffix is None:
        raise HTTPException(status_code=415, detail="Use a WebM, Ogg, WAV, MP4, or MP3 audio recording.")

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.voice_max_audio_bytes:
        raise HTTPException(status_code=413, detail="Recording exceeds the configured size limit.")

    audio = bytearray()
    async for chunk in _bounded_request_stream(request, settings.voice_max_audio_bytes):
        audio.extend(chunk)
    if not audio:
        raise HTTPException(status_code=400, detail="The audio recording is empty.")

    try:
        transcript = await run_in_threadpool(service.transcribe, bytes(audio), suffix, language)
    except VoiceModelMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceDependencyMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VoiceServiceError as exc:
        logger.exception("Unexpected local voice recognition failure")
        raise HTTPException(status_code=500, detail="Local speech recognition failed.") from exc

    return TranscriptionResponse(transcript=transcript, language=language)


async def _bounded_request_stream(request: Request, max_bytes: int) -> AsyncIterator[bytes]:
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="Recording exceeds the configured size limit.")
        yield chunk


@router.post(
    "/synthesize",
    summary="Synthesize speech with a local Piper voice",
    responses={
        200: {"content": {"audio/wav": {}}},
        503: {"description": "Local model or voice dependency is missing"},
    },
)
async def synthesize_speech(
    synthesis: SynthesisRequest,
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> Response:
    """Create a WAV response locally; the text is not sent to a remote service."""
    text = synthesis.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text to speak must not be blank.")
    if len(text) > service.settings.voice_max_text_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Text exceeds the {service.settings.voice_max_text_chars}-character limit.",
        )

    try:
        audio = await run_in_threadpool(service.synthesize, text, synthesis.language)
    except VoiceModelMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceDependencyMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VoiceProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VoiceServiceError as exc:
        logger.exception("Unexpected local voice synthesis failure")
        raise HTTPException(status_code=500, detail="Local speech synthesis failed.") from exc

    return Response(content=audio, media_type="audio/wav")
