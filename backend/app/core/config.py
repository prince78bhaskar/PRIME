"""
P.R.I.M.E. Configuration Management.

Loads settings from environment variables and optional .env file.
All secrets and environment-specific values must be configured via
environment variables - never hardcoded.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root (3 levels up from this file: core/ -> app/ -> backend/)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    Configuration priority (highest to lowest):
    1. Environment variables
    2. .env file in backend/ directory
    3. Default values defined below
    """

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="PRIME_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = Field(default="P.R.I.M.E.", description="Application display name")
    app_version: str = Field(default="0.2.0-alpha.phase01", description="Semantic version")
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Runtime environment",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Server ───────────────────────────────────────────────────
    host: str = Field(default="127.0.0.1", description="Server bind address")
    port: int = Field(default=8000, description="Server bind port")

    # ── Paths ────────────────────────────────────────────────────
    project_root: Path = Field(default=_PROJECT_ROOT, description="Project root directory")
    data_dir: Path = Field(default=_PROJECT_ROOT / "data", description="Data storage directory")
    db_path: Path = Field(
        default=_PROJECT_ROOT / "data" / "memory" / "prime.db",
        description="SQLite database file path",
    )
    log_dir: Path = Field(default=_PROJECT_ROOT / "logs", description="Log output directory")

    # ── Logging ──────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum log level",
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output format",
    )

    # ── Ollama (Phase 01+) ───────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama local API base URL",
    )
    ollama_model: str = Field(
        default="qwen2.5:3b-instruct-q4_K_M",
        description="Default Ollama model tag",
    )
    ollama_timeout_seconds: int = Field(default=30, description="Ollama request timeout")

    # ── Local voice pipeline ────────────────────────────────────
    voice_stt_model_path: Path = Field(
        default=_PROJECT_ROOT / "models" / "faster-whisper-small",
        description="Path to a downloaded Faster-Whisper model directory",
    )
    voice_stt_device: Literal["cpu", "cuda"] = Field(
        default="cpu",
        description="Inference device for local speech recognition",
    )
    voice_stt_compute_type: str = Field(
        default="int8",
        description="CTranslate2 compute type for local speech recognition",
    )
    voice_tts_en_model_path: Path = Field(
        default=_PROJECT_ROOT / "models" / "voice" / "en_US-lessac-medium.onnx",
        description="Path to the Piper English ONNX voice model",
    )
    voice_tts_hi_model_path: Path = Field(
        default=_PROJECT_ROOT / "models" / "voice" / "hi_IN-pratham-medium.onnx",
        description="Path to the Piper Hindi ONNX voice model",
    )
    voice_max_audio_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
        description="Maximum recorded audio payload accepted by the local STT endpoint",
    )
    voice_max_text_chars: int = Field(
        default=5000,
        ge=1,
        le=20000,
        description="Maximum text length accepted by the local TTS endpoint",
    )

    @field_validator("port")
    @classmethod
    def _validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @field_validator("db_path", mode="before")
    @classmethod
    def _resolve_db_path(cls, v: str | Path) -> Path:
        return Path(v).resolve()


def get_settings() -> Settings:
    """Factory function returning a Settings instance.

    In production, settings are cached at module level.
    During testing, this function can be overridden via FastAPI dependency injection.
    """
    return Settings()
