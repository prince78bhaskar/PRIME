"""
Tests for P.R.I.M.E. configuration management.

Covers:
- Default settings loading
- Environment variable override
- Port validation
- Settings factory function
"""


import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestDefaultSettings:
    """Verify default configuration values."""

    def test_app_name_default(self) -> None:
        settings = Settings()
        assert settings.app_name == "P.R.I.M.E."

    def test_environment_default(self) -> None:
        settings = Settings()
        assert settings.environment == "development"

    def test_debug_default_false(self) -> None:
        settings = Settings()
        assert settings.debug is False

    def test_host_default_localhost(self) -> None:
        settings = Settings()
        assert settings.host == "127.0.0.1"

    def test_port_default_8000(self) -> None:
        settings = Settings()
        assert settings.port == 8000

    def test_log_level_default_info(self) -> None:
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_ollama_base_url_default(self) -> None:
        settings = Settings()
        assert settings.ollama_base_url == "http://127.0.0.1:11434"

    def test_db_path_is_resolved(self) -> None:
        settings = Settings()
        assert settings.db_path.is_absolute()


class TestEnvironmentOverride:
    """Verify settings can be overridden via constructor (simulating env vars)."""

    def test_override_environment(self) -> None:
        settings = Settings(environment="testing")
        assert settings.environment == "testing"

    def test_override_debug(self) -> None:
        settings = Settings(debug=True)
        assert settings.debug is True

    def test_override_port(self) -> None:
        settings = Settings(port=9000)
        assert settings.port == 9000

    def test_override_log_level(self) -> None:
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"


class TestPortValidation:
    """Verify port number validation."""

    def test_port_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Settings(port=0)

    def test_port_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Settings(port=-1)

    def test_port_too_high_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Settings(port=70000)

    def test_port_boundary_low(self) -> None:
        settings = Settings(port=1)
        assert settings.port == 1

    def test_port_boundary_high(self) -> None:
        settings = Settings(port=65535)
        assert settings.port == 65535


class TestSettingsFactory:
    """Verify the get_settings() factory function."""

    def test_returns_settings_instance(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_factory_returns_consistent_defaults(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1.app_name == s2.app_name
        assert s1.port == s2.port
