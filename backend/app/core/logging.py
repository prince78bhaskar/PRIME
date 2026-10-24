"""
P.R.I.M.E. Structured Logging Configuration.

Provides JSON-structured and human-readable log formatters.
Log output directory is created automatically on setup.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Emits log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via `extra={"key": "value"}`
        for key in ("request_id", "agent", "tool", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable colored log formatter for development."""

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self.FORMAT, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_dir: Path | None = None,
) -> None:
    """Configure application-wide structured logging.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format - 'json' for structured, 'text' for human-readable.
        log_dir: Optional directory for log file output. Created if it doesn't exist.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear any existing handlers to prevent duplicates on re-init
    root_logger.handlers.clear()

    # Select formatter
    formatter: logging.Formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / "prime.log"
        file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())  # Always JSON for file output
        root_logger.addHandler(file_handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    root_logger.info(
        "Logging configured",
        extra={"level": level, "format": log_format},
    )
