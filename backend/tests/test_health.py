"""
Tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoint:
    """Test suite for health check endpoints."""

    def test_health_check_sync(self, test_client: TestClient):
        """Test health check endpoint with synchronous client."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient):
        """Test health check endpoint with async client."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_api_health_check(self, async_client: AsyncClient):
        """Test versioned health check endpoint."""
        response = await async_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

        # Status should be one of: ok, degraded, error
        assert data["status"] in ["ok", "degraded", "error"]

        # Should include database and redis status
        if "database" in data:
            assert data["database"] in ["ok", "unavailable", "error"]
        if "redis" in data:
            assert data["redis"] in ["ok", "unavailable", "error"]

    def test_health_check_response_schema(self, test_client: TestClient):
        """Test health check response matches expected schema."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = ["status", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check optional fields have correct types if present
        if "database" in data:
            assert isinstance(data["database"], str)
        if "redis" in data:
            assert isinstance(data["redis"], str)

    @pytest.mark.asyncio
    async def test_health_check_headers(self, async_client: AsyncClient):
        """Test health check response headers."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_openapi_docs_available(self, test_client: TestClient):
        """Test that OpenAPI documentation is accessible."""
        response = test_client.get("/docs")
        assert response.status_code == 200

        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
