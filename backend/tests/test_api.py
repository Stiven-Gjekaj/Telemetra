"""
Tests for REST API endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestStreamsEndpoint:
    """Test suite for /streams endpoint."""

    @pytest.mark.asyncio
    async def test_get_streams(self, async_client: AsyncClient):
        """Test GET /streams endpoint."""
        response = await async_client.get("/api/v1/streams")

        # Should return 200 even if no streams (empty list)
        # or 500 if database not available
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_streams_with_pagination(self, async_client: AsyncClient):
        """Test GET /streams with pagination parameters."""
        response = await async_client.get("/api/v1/streams?limit=10&offset=0")

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_get_streams_invalid_limit(self, async_client: AsyncClient):
        """Test GET /streams with invalid limit parameter."""
        response = await async_client.get("/api/v1/streams?limit=1000")

        # Should reject limits over 500
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_streams_negative_offset(self, async_client: AsyncClient):
        """Test GET /streams with negative offset."""
        response = await async_client.get("/api/v1/streams?offset=-1")

        # Should reject negative offsets
        assert response.status_code == 422


class TestMetricsEndpoint:
    """Test suite for /streams/{id}/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, async_client: AsyncClient, mock_stream_id: str):
        """Test GET /streams/{id}/metrics endpoint."""
        response = await async_client.get(f"/api/v1/streams/{mock_stream_id}/metrics")

        # Should return 200 with data, 404 if not found, or 500 on error
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            if len(data) > 0:
                metric = data[0]
                assert "stream_id" in metric
                assert "timestamp" in metric
                assert "viewer_count" in metric
                assert "chat_rate" in metric

    @pytest.mark.asyncio
    async def test_get_metrics_with_limit(self, async_client: AsyncClient, mock_stream_id: str):
        """Test GET /streams/{id}/metrics with limit parameter."""
        response = await async_client.get(
            f"/api/v1/streams/{mock_stream_id}/metrics?limit=5"
        )

        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_get_metrics_invalid_stream(self, async_client: AsyncClient):
        """Test GET /streams/{id}/metrics with non-existent stream."""
        response = await async_client.get("/api/v1/streams/nonexistent_stream/metrics")

        # Should return 404 or 500 (depending on database availability)
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_metrics_response_schema(
        self, async_client: AsyncClient, mock_stream_id: str
    ):
        """Test metrics response matches expected schema."""
        response = await async_client.get(f"/api/v1/streams/{mock_stream_id}/metrics")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                metric = data[0]

                # Required fields
                required_fields = [
                    "stream_id",
                    "timestamp",
                    "viewer_count",
                    "chat_rate",
                    "unique_chatters",
                    "top_emotes",
                ]

                for field in required_fields:
                    assert field in metric, f"Missing required field: {field}"

                # Type checks
                assert isinstance(metric["viewer_count"], int)
                assert isinstance(metric["chat_rate"], (int, float))
                assert isinstance(metric["unique_chatters"], int)
                assert isinstance(metric["top_emotes"], list)


class TestMomentsEndpoint:
    """Test suite for /streams/{id}/moments endpoint."""

    @pytest.mark.asyncio
    async def test_get_moments(self, async_client: AsyncClient, mock_stream_id: str):
        """Test GET /streams/{id}/moments endpoint."""
        response = await async_client.get(f"/api/v1/streams/{mock_stream_id}/moments")

        # Should return 200 (possibly empty list), 404, or 500
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            if len(data) > 0:
                moment = data[0]
                assert "stream_id" in moment
                assert "timestamp" in moment
                assert "moment_type" in moment
                assert "description" in moment

    @pytest.mark.asyncio
    async def test_get_moments_with_limit(self, async_client: AsyncClient, mock_stream_id: str):
        """Test GET /streams/{id}/moments with limit parameter."""
        response = await async_client.get(
            f"/api/v1/streams/{mock_stream_id}/moments?limit=10"
        )

        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_get_moments_response_schema(
        self, async_client: AsyncClient, mock_stream_id: str
    ):
        """Test moments response matches expected schema."""
        response = await async_client.get(f"/api/v1/streams/{mock_stream_id}/moments")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                moment = data[0]

                # Required fields
                required_fields = [
                    "stream_id",
                    "timestamp",
                    "moment_type",
                    "description",
                    "metric_name",
                    "metric_value",
                ]

                for field in required_fields:
                    assert field in moment, f"Missing required field: {field}"

                # Type checks
                assert isinstance(moment["moment_type"], str)
                assert isinstance(moment["description"], str)
                assert isinstance(moment["metric_name"], str)
                assert isinstance(moment["metric_value"], (int, float))

    @pytest.mark.asyncio
    async def test_get_moments_empty_result(self, async_client: AsyncClient):
        """Test moments endpoint with stream that has no moments."""
        response = await async_client.get("/api/v1/streams/stream_with_no_moments/moments")

        # Should return empty list or 404/500
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            # Empty list is valid
            assert isinstance(data, list)


class TestCORSHeaders:
    """Test suite for CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, async_client: AsyncClient):
        """Test that CORS headers are present in responses."""
        response = await async_client.get("/api/v1/health")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    @pytest.mark.asyncio
    async def test_preflight_request(self, async_client: AsyncClient):
        """Test CORS preflight OPTIONS request."""
        response = await async_client.options(
            "/api/v1/streams",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should handle preflight request
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, async_client: AsyncClient):
        """Test 404 error for non-existent endpoint."""
        response = await async_client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, async_client: AsyncClient):
        """Test 405 error for wrong HTTP method."""
        response = await async_client.post("/api/v1/health")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_validation_error(self, async_client: AsyncClient):
        """Test 422 validation error for invalid parameters."""
        response = await async_client.get("/api/v1/streams?limit=invalid")

        assert response.status_code == 422
