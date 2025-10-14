import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from .websocket_manager import ConnectionManager
import os

logger = logging.getLogger(__name__)

class KafkaLiveConsumer:
    """Consumes Kafka messages and pushes them to WebSocket clients"""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self.consumer = None
        self.running = False
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

    async def start(self):
        """Start consuming from Kafka"""
        self.running = True

        try:
            self.consumer = AIOKafkaConsumer(
                'telemetra.chat',
                'telemetra.viewer',
                'telemetra.derived.sentiment',
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='telemetra-websocket-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            await self.consumer.start()
            logger.info("Kafka consumer started for WebSocket broadcasting")

            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    data = message.value
                    stream_id = data.get('stream_id')

                    if stream_id:
                        # Broadcast to all connections watching this stream
                        await self.manager.broadcast_to_stream(stream_id, {
                            'topic': message.topic,
                            'data': data,
                            'timestamp': message.timestamp
                        })
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")

        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
