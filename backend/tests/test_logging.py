"""
Tests for P.R.I.M.E. structured logging configuration.

Covers:
- JSON formatter produces valid JSON
- Text formatter produces readable output
- Log directory creation
- setup_logging configures handlers
"""

import json
import logging
from pathlib import Path

from app.core.logging import JSONFormatter, TextFormatter, setup_logging


class TestJSONFormatter:
    """Verify JSON log formatter output."""

    def test_produces_valid_json(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"

    def test_includes_timestamp(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="msg", args=None, exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert "timestamp" in parsed

    def test_includes_exception_info(self) -> None:
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="error", args=None, exc_info=sys.exc_info(),
            )
        output = json.loads(formatter.format(record))
        assert "exception" in output
        assert "ValueError" in output["exception"]


class TestTextFormatter:
    """Verify text log formatter."""

    def test_produces_readable_output(self) -> None:
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Hello world", args=None, exc_info=None,
        )
        output = formatter.format(record)
        assert "INFO" in output
        assert "Hello world" in output


class TestSetupLogging:
    """Verify logging configuration."""

    def test_configures_root_logger(self) -> None:
        setup_logging(level="DEBUG", log_format="text")
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) > 0

    def test_creates_log_directory(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "new_logs"
        setup_logging(level="INFO", log_format="json", log_dir=log_dir)
        assert log_dir.exists()
        assert (log_dir / "prime.log").exists()

    def test_json_format_handler(self) -> None:
        setup_logging(level="INFO", log_format="json")
        root = logging.getLogger()
        has_json = any(
            isinstance(h.formatter, JSONFormatter)
            for h in root.handlers
        )
        assert has_json
