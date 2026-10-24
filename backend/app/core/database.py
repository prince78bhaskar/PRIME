"""
P.R.I.M.E. SQLite Database Manager.

Handles database lifecycle: creation, connection, schema initialization,
and graceful shutdown. Uses WAL mode for concurrent read performance.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Schema Definitions ───────────────────────────────────────────
# Baseline tables created during Phase 01. Additional tables will be
# added by migration scripts in subsequent phases.
_SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    description TEXT    NOT NULL
);

-- Application configuration store (key-value)
CREATE TABLE IF NOT EXISTS app_config (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Audit log for system events
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (datetime('now')),
    level       TEXT    NOT NULL DEFAULT 'INFO',
    source      TEXT    NOT NULL,
    event       TEXT    NOT NULL,
    details     TEXT    -- JSON blob for structured event data
);
"""

_CURRENT_SCHEMA_VERSION = 1
_SCHEMA_DESCRIPTION = "Phase 01 baseline: schema_version, app_config, audit_log"


class DatabaseManager:
    """Manages SQLite database connections and schema lifecycle.

    Attributes:
        db_path: Resolved path to the SQLite database file.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize database manager.

        Args:
            db_path: Path to the SQLite database file.
                     Parent directories are created if they don't exist.
        """
        self.db_path = db_path.resolve()
        self._connection: sqlite3.Connection | None = None

    @property
    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        return self._connection is not None

    def connect(self) -> None:
        """Open a database connection and enable WAL mode.

        Creates the database file and parent directories if they don't exist.
        Configures pragmas for performance and reliability.

        Raises:
            sqlite3.Error: If the connection cannot be established.
        """
        if self._connection is not None:
            logger.debug("Database connection already open")
            return

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Opening database connection", extra={"path": str(self.db_path)})
        self._connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Safe with WAL mode for read concurrency
        )
        self._connection.row_factory = sqlite3.Row

        # Configure pragmas for performance and safety
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA busy_timeout=5000")

        logger.info("Database connected with WAL mode enabled")

    def initialize_schema(self) -> None:
        """Create baseline tables if they don't exist.

        Applies the schema and records the version in schema_version.
        Idempotent - safe to call multiple times.

        Raises:
            RuntimeError: If called before connect().
        """
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        logger.info("Initializing database schema")
        self._connection.executescript(_SCHEMA_SQL)

        # Record schema version if not already present
        cursor = self._connection.execute(
            "SELECT version FROM schema_version WHERE version = ?",
            (_CURRENT_SCHEMA_VERSION,),
        )
        if cursor.fetchone() is None:
            self._connection.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (_CURRENT_SCHEMA_VERSION, _SCHEMA_DESCRIPTION),
            )
            self._connection.commit()
            logger.info(
                "Schema version applied",
                extra={"version": _CURRENT_SCHEMA_VERSION},
            )
        else:
            logger.debug("Schema version already applied, skipping")

    def get_connection(self) -> sqlite3.Connection:
        """Return the active database connection.

        Raises:
            RuntimeError: If the database is not connected.
        """
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    def close(self) -> None:
        """Close the database connection gracefully."""
        if self._connection is not None:
            logger.info("Closing database connection")
            self._connection.close()
            self._connection = None
