"""Request and response models for local voice endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

VoiceLanguage = Literal["en", "hi"]


class TranscriptionResponse(BaseModel):
    transcript: str = Field(description="Recognized speech; empty when no speech was detected")
    language: VoiceLanguage


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, description="Text to synthesize with a local Piper voice")
    language: VoiceLanguage = Field(default="en")


class VoiceStatusResponse(BaseModel):
    stt_ready: bool
    stt_model_present: bool
    stt_runtime_installed: bool
    tts_runtime_installed: bool
    tts_models: dict[str, bool]
    tts_ready_languages: list[str]
