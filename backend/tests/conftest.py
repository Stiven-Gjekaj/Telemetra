"""
Pytest configuration and fixtures for Telemetra backend tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Import the FastAPI app
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Provide a synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_stream_id():
    """Provide a mock stream ID for testing."""
    return "demo_stream"


@pytest.fixture
def mock_stream_data():
    """Provide mock stream data."""
    return {
        "stream_id": "demo_stream",
        "streamer_name": "test_streamer",
        "title": "Test Stream",
        "game_category": "Just Chatting",
        "started_at": "2024-01-01T00:00:00",
        "is_live": True,
        "viewer_count": 1000,
    }


@pytest.fixture
def mock_metrics_data():
    """Provide mock metrics data."""
    return {
        "stream_id": "demo_stream",
        "timestamp": "2024-01-01T00:00:00",
        "viewer_count": 1000,
        "chat_rate": 50.5,
        "unique_chatters": 100,
        "top_emotes": [
            {"emote": "Kappa", "count": 25},
            {"emote": "PogChamp", "count": 20},
        ],
        "sentiment_score": 0.75,
    }


@pytest.fixture
def mock_moment_data():
    """Provide mock moment data."""
    return {
        "moment_id": 1,
        "stream_id": "demo_stream",
        "timestamp": "2024-01-01T00:00:00",
        "moment_type": "spike",
        "description": "Viewer count spike detected",
        "metric_name": "viewer_count",
        "metric_value": 2000.0,
        "threshold": 1500.0,
        "z_score": 3.5,
        "metadata": {"previous_value": 1000},
    }
