"""
Tests for P.R.I.M.E. SQLite database manager.

Covers:
- Connection lifecycle (connect, close)
- WAL mode activation
- Schema initialization and idempotency
- Error handling for disconnected state
"""

import sqlite3
from pathlib import Path

import pytest

from app.core.database import DatabaseManager


class TestDatabaseConnection:
    """Verify database connection lifecycle."""

    def test_connect_creates_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path=db_path)
        db.connect()
        assert db_path.exists()
        db.close()

    def test_connect_creates_parent_directories(self, tmp_path: Path) -> None:
        db_path = tmp_path / "deep" / "nested" / "dir" / "test.db"
        db = DatabaseManager(db_path=db_path)
        db.connect()
        assert db_path.parent.exists()
        db.close()

    def test_is_connected_false_before_connect(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        assert db.is_connected is False

    def test_is_connected_true_after_connect(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        db.connect()
        assert db.is_connected is True
        db.close()

    def test_is_connected_false_after_close(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        db.connect()
        db.close()
        assert db.is_connected is False

    def test_double_connect_is_safe(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        db.connect()
        db.connect()  # Should not raise
        assert db.is_connected is True
        db.close()

    def test_double_close_is_safe(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        db.connect()
        db.close()
        db.close()  # Should not raise


class TestWALMode:
    """Verify WAL journal mode is enabled."""

    def test_wal_mode_enabled(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        db.connect()
        conn = db.get_connection()
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0].lower() == "wal"
        db.close()


class TestSchemaInitialization:
    """Verify schema creation and version tracking."""

    def test_schema_creates_tables(self, db_manager: DatabaseManager) -> None:
        conn = db_manager.get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert "schema_version" in tables
        assert "app_config" in tables
        assert "audit_log" in tables

    def test_schema_version_recorded(self, db_manager: DatabaseManager) -> None:
        conn = db_manager.get_connection()
        cursor = conn.execute("SELECT version, description FROM schema_version")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1

    def test_schema_init_is_idempotent(self, db_manager: DatabaseManager) -> None:
        # Call initialize_schema again - should not raise or duplicate rows
        db_manager.initialize_schema()
        conn = db_manager.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM schema_version WHERE version = 1")
        assert cursor.fetchone()[0] == 1

    def test_schema_init_requires_connection(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        with pytest.raises(RuntimeError, match="not connected"):
            db.initialize_schema()

    def test_get_connection_requires_connect(self, tmp_path: Path) -> None:
        db = DatabaseManager(db_path=tmp_path / "test.db")
        with pytest.raises(RuntimeError, match="not connected"):
            db.get_connection()
