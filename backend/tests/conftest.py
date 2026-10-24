"""
Shared pytest fixtures for P.R.I.M.E. backend tests.

Provides reusable fixtures for settings, database, and HTTPX test client.
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import DatabaseManager
from app.main import create_app


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary data directory for test isolation."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "memory").mkdir()
    return data_dir


@pytest.fixture
def test_settings(tmp_data_dir: Path) -> Settings:
    """Create test-specific settings with isolated paths.

    Uses a temporary directory to avoid polluting the real database.
    """
    return Settings(
        environment="testing",
        debug=True,
        db_path=tmp_data_dir / "memory" / "test.db",
        data_dir=tmp_data_dir,
        log_dir=tmp_data_dir / "logs",
        log_level="DEBUG",
        log_format="text",
    )


@pytest.fixture
def db_manager(test_settings: Settings) -> Generator[DatabaseManager, None, None]:
    """Provide a connected and initialized DatabaseManager.

    Yields a database manager with schema applied, then closes on teardown.
    """
    db = DatabaseManager(db_path=test_settings.db_path)
    db.connect()
    db.initialize_schema()
    yield db
    db.close()


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Provide an HTTPX test client with fully initialized app.

    The app uses test-specific settings with an isolated database.
    """
    app = create_app(settings=test_settings)
    with TestClient(app) as c:
        yield c
