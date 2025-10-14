#!/usr/bin/env python3
"""
Twitch Mock Producer - Generates synthetic streaming events for Telemetra demo
Produces to Kafka topics: chat, viewer, transactions, stream_meta
"""

import json
import time
import random
import os
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitchMockProducer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.producer_interval = float(os.getenv("PRODUCER_INTERVAL", "0.5"))
        self.num_channels = int(os.getenv("NUM_CHANNELS", "3"))
        self.chat_rate_mean = int(os.getenv("CHAT_RATE_MEAN", "50"))
        self.viewer_count_mean = int(os.getenv("VIEWER_COUNT_MEAN", "1000"))

        # Initialize Kafka producer
        self.producer = None
        self.connect_kafka()

        # Mock data
        self.channels = [f"channel_{i}" for i in range(1, self.num_channels + 1)]
        self.stream_ids = {ch: f"stream_{ch}_{int(time.time())}" for ch in self.channels}

        self.emotes = [
            "Kappa", "PogChamp", "LUL", "4Head", "ResidentSleeper",
            "NotLikeThis", "BibleThump", "TriHard", "Kreygasm", "DansGame"
        ]

        self.usernames = [
            "gamer123", "streamer_fan", "chat_master", "lurker_bob",
            "mod_alice", "sub_charlie", "viewer_dana", "raid_leader",
            "emote_spammer", "clip_maker", "vip_user", "donor_frank"
        ]

        self.messages = [
            "this is amazing!",
            "nice play",
            "what just happened?",
            "lol",
            "gg",
            "F in chat",
            "clutch!",
            "POG",
            "lets gooo",
            "not bad",
        ]

    def connect_kafka(self):
        """Connect to Kafka with retry logic"""
        max_retries = 30
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3
                )
                logger.info(f"Successfully connected to Kafka at {self.bootstrap_servers}")
                return
            except KafkaError as e:
                logger.warning(f"Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(retry_delay)

        raise Exception("Failed to connect to Kafka after maximum retries")

    def generate_chat_event(self, channel: str) -> dict:
        """Generate a synthetic chat message"""
        message = random.choice(self.messages)

        # Add emotes randomly
        if random.random() < 0.3:
            message += f" {random.choice(self.emotes)}"

        return {
            "stream_id": self.stream_ids[channel],
            "channel": channel,
            "username": random.choice(self.usernames),
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "message_length": len(message),
            "has_emote": any(emote in message for emote in self.emotes),
            "user_type": random.choice(["viewer", "subscriber", "moderator", "vip"])
        }

    def generate_viewer_event(self, channel: str) -> dict:
        """Generate viewer count event with some variation"""
        base_count = self.viewer_count_mean
        # Add random walk variation
        variation = random.gauss(0, base_count * 0.1)
        viewer_count = max(10, int(base_count + variation))

        return {
            "stream_id": self.stream_ids[channel],
            "channel": channel,
            "viewer_count": viewer_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    def generate_transaction_event(self, channel: str) -> dict:
        """Generate transaction event (sub, donation, bits)"""
        transaction_type = random.choice([
            "subscription", "subscription", "donation", "bits", "gift_sub"
        ])

        amounts = {
            "subscription": 4.99,
            "donation": random.uniform(1.0, 100.0),
            "bits": random.choice([100, 500, 1000, 5000]) * 0.01,
            "gift_sub": 4.99
        }

        return {
            "stream_id": self.stream_ids[channel],
            "channel": channel,
            "transaction_type": transaction_type,
            "amount": round(amounts[transaction_type], 2),
            "username": random.choice(self.usernames),
            "timestamp": datetime.utcnow().isoformat()
        }

    def generate_stream_meta_event(self, channel: str) -> dict:
        """Generate stream metadata event"""
        return {
            "stream_id": self.stream_ids[channel],
            "channel": channel,
            "title": f"Epic Gaming Stream - {channel}",
            "game": random.choice(["Fortnite", "League of Legends", "Valorant", "Minecraft", "Just Chatting"]),
            "language": "en",
            "tags": random.sample(["gaming", "competitive", "fun", "chill", "educational"], k=3),
            "timestamp": datetime.utcnow().isoformat()
        }

    def send_to_kafka(self, topic: str, key: str, value: dict):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(topic, key=key, value=value)
            record_metadata = future.get(timeout=10)
            logger.debug(f"Sent to {topic} - partition {record_metadata.partition} offset {record_metadata.offset}")
        except Exception as e:
            logger.error(f"Failed to send to {topic}: {e}")

    def run(self):
        """Main producer loop"""
        logger.info(f"Starting Twitch mock producer for {self.num_channels} channels")
        logger.info(f"Producing events every {self.producer_interval} seconds")

        # Send initial stream metadata
        for channel in self.channels:
            meta = self.generate_stream_meta_event(channel)
            self.send_to_kafka("stream_meta", channel, meta)

        iteration = 0
        try:
            while True:
                for channel in self.channels:
                    # Generate chat messages (high frequency)
                    num_chat_messages = random.randint(1, 5)
                    for _ in range(num_chat_messages):
                        chat = self.generate_chat_event(channel)
                        self.send_to_kafka("chat", channel, chat)

                    # Generate viewer count (every iteration)
                    viewer = self.generate_viewer_event(channel)
                    self.send_to_kafka("viewer", channel, viewer)

                    # Generate transaction (low frequency)
                    if random.random() < 0.05:  # 5% chance per interval
                        transaction = self.generate_transaction_event(channel)
                        self.send_to_kafka("transactions", channel, transaction)

                    # Update stream metadata occasionally
                    if iteration % 100 == 0:
                        meta = self.generate_stream_meta_event(channel)
                        self.send_to_kafka("stream_meta", channel, meta)

                iteration += 1
                if iteration % 20 == 0:
                    logger.info(f"Produced {iteration * len(self.channels)} batches of events")

                time.sleep(self.producer_interval)

        except KeyboardInterrupt:
            logger.info("Shutting down producer...")
        finally:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer shutdown complete")


if __name__ == "__main__":
    producer = TwitchMockProducer()
    producer.run()
