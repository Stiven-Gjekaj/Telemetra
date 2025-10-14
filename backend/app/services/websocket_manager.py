from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for live stream updates"""

    def __init__(self):
        # Map stream_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = set()

        self.active_connections[stream_id].add(websocket)
        logger.info(f"New connection for stream {stream_id}. Total: {len(self.active_connections[stream_id])}")

    def disconnect(self, websocket: WebSocket, stream_id: str):
        """Remove a WebSocket connection"""
        if stream_id in self.active_connections:
            self.active_connections[stream_id].discard(websocket)

            if len(self.active_connections[stream_id]) == 0:
                del self.active_connections[stream_id]

            logger.info(f"Connection removed for stream {stream_id}")

    async def broadcast_to_stream(self, stream_id: str, message: dict):
        """Broadcast a message to all connections watching a specific stream"""
        if stream_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[stream_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, stream_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
