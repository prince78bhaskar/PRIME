"""
Tests for P.R.I.M.E. health check endpoint and application startup.

Covers:
- Application starts successfully
- Health endpoint returns correct status
- Database connectivity is reported
- Version and environment are reported
- Uptime tracking works
"""

from fastapi.testclient import TestClient


class TestApplicationStartup:
    """Verify the application starts and initializes correctly."""

    def test_app_starts_without_error(self, client: TestClient) -> None:
        """Application should start cleanly with test settings."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_app_has_correct_title(self, client: TestClient) -> None:
        """OpenAPI schema should reflect app name."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["title"] == "P.R.I.M.E."


class TestHealthEndpoint:
    """Verify health check endpoint responses."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_reports_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["version"] == "0.2.0-alpha.phase01"

    def test_health_reports_testing_environment(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["environment"] == "testing"

    def test_health_reports_database_connected(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["database"] == "connected"

    def test_health_reports_uptime(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["uptime_seconds"] is not None
        assert data["uptime_seconds"] >= 0

    def test_health_response_structure(self, client: TestClient) -> None:
        """Verify all expected keys are present."""
        data = client.get("/health").json()
        expected_keys = {"status", "version", "environment", "database", "uptime_seconds"}
        assert expected_keys == set(data.keys())


class TestErrorHandling:
    """Verify global error handling."""

    def test_404_for_unknown_route(self, client: TestClient) -> None:
        response = client.get("/nonexistent")
        assert response.status_code == 404
