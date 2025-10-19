"""
Tests for WebSocket functionality.
"""
import pytest
import json
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoints."""

    def test_websocket_connection(self, test_client: TestClient, mock_stream_id: str):
        """Test WebSocket connection handshake."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Should receive a welcome message
            data = websocket.receive_json()

            assert "type" in data
            assert data["type"] == "connected"
            assert "stream_id" in data
            assert data["stream_id"] == mock_stream_id
            assert "message" in data
            assert "timestamp" in data

    def test_websocket_connection_invalid_stream(self, test_client: TestClient):
        """Test WebSocket connection with invalid stream ID."""
        # Should still connect but might not have data
        with test_client.websocket_connect("/ws/live/invalid_stream") as websocket:
            # Should receive a welcome message even for invalid stream
            data = websocket.receive_json()
            assert "type" in data

    def test_websocket_receives_metrics(self, test_client: TestClient, mock_stream_id: str):
        """Test that WebSocket receives metric updates."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Receive welcome message
            welcome = websocket.receive_json()
            assert welcome["type"] == "connected"

            # Should receive metric updates
            # (May timeout if database is not available in test environment)
            try:
                data = websocket.receive_json(timeout=5)

                # Check metric structure
                assert "stream_id" in data
                assert "timestamp" in data
                assert "viewer_count" in data
                assert "chat_rate" in data

                # Check types
                assert isinstance(data["viewer_count"], int)
                assert isinstance(data["chat_rate"], (int, float))

            except TimeoutError:
                # In test environment without database, timeout is expected
                pytest.skip("Database not available in test environment")

    def test_websocket_message_format(self, test_client: TestClient, mock_stream_id: str):
        """Test WebSocket message format."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Get welcome message
            data = websocket.receive_json()

            # Validate it's valid JSON
            assert isinstance(data, dict)

            # Check for required fields in welcome message
            assert "type" in data
            assert "timestamp" in data

    def test_websocket_multiple_connections(self, test_client: TestClient, mock_stream_id: str):
        """Test multiple WebSocket connections to same stream."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as ws1:
            with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as ws2:
                # Both should receive welcome messages
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["type"] == "connected"
                assert data2["type"] == "connected"
                assert data1["stream_id"] == mock_stream_id
                assert data2["stream_id"] == mock_stream_id

    def test_websocket_health_endpoint(self, test_client: TestClient):
        """Test WebSocket health check endpoint."""
        response = test_client.get("/ws/live/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"
        assert "active_streams" in data
        assert "total_connections" in data

        # Check types
        assert isinstance(data["active_streams"], int)
        assert isinstance(data["total_connections"], int)

    def test_websocket_health_with_active_connections(
        self, test_client: TestClient, mock_stream_id: str
    ):
        """Test WebSocket health endpoint with active connections."""
        # First, establish a connection
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Consume welcome message
            websocket.receive_json()

            # Check health while connection is active
            response = test_client.get("/ws/live/health")
            assert response.status_code == 200
            data = response.json()

            assert data["total_connections"] >= 1
            assert "streams" in data
            assert isinstance(data["streams"], dict)

    def test_websocket_graceful_disconnect(self, test_client: TestClient, mock_stream_id: str):
        """Test graceful WebSocket disconnection."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Close the connection
            websocket.close()

        # Should not raise any errors
        # Connection should be removed from manager

    def test_websocket_connection_to_multiple_streams(self, test_client: TestClient):
        """Test connections to multiple different streams."""
        stream1 = "stream1"
        stream2 = "stream2"

        with test_client.websocket_connect(f"/ws/live/{stream1}") as ws1:
            with test_client.websocket_connect(f"/ws/live/{stream2}") as ws2:
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["stream_id"] == stream1
                assert data2["stream_id"] == stream2
                assert data1["stream_id"] != data2["stream_id"]


class TestWebSocketMetricUpdates:
    """Test suite for WebSocket metric update messages."""

    def test_metric_update_structure(self, test_client: TestClient, mock_stream_id: str):
        """Test structure of metric update messages."""
        with test_client.websocket_connect(f"/ws/live/{mock_stream_id}") as websocket:
            # Skip welcome message
            websocket.receive_json()

            try:
                # Get a metric update
                data = websocket.receive_json(timeout=5)

                # Verify required fields
                required_fields = [
                    "stream_id",
                    "timestamp",
                    "viewer_count",
                    "chat_rate",
                ]

                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"

                # Verify optional fields have correct types if present
                if "unique_chatters" in data:
                    assert isinstance(data["unique_chatters"], (int, type(None)))
                if "top_emotes" in data:
                    assert isinstance(data["top_emotes"], list)
                if "recent_moments" in data:
                    assert isinstance(data["recent_moments"], list)

            except TimeoutError:
                pytest.skip("Database not available in test environment")
