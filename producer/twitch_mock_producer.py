"""
Twitch Mock Data Producer for Kafka

Generates synthetic Twitch streaming data (chat messages and viewer counts)
and publishes to Kafka topics for testing the analytics pipeline.
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List
from kafka import KafkaProducer
from kafka.errors import KafkaError


# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
CHAT_TOPIC = os.getenv("CHAT_TOPIC", "twitch-chat")
VIEWER_TOPIC = os.getenv("VIEWER_TOPIC", "twitch-viewers")
MESSAGE_RATE_MIN = float(os.getenv("MESSAGE_RATE_MIN", "0.5"))  # seconds
MESSAGE_RATE_MAX = float(os.getenv("MESSAGE_RATE_MAX", "2.0"))  # seconds

# Mock data
STREAM_IDS = ["xqc", "shroud", "pokimane", "summit1g", "ninja"]
USERNAMES = [
    "viewer123", "chatbot99", "proGamer", "twitchFan", "streamSniper",
    "moderator1", "subscriber42", "lurker777", "donator88", "emoteKing",
    "memeLord", "clipChamp", "vipUser", "newbie101", "veteran999"
]
CHAT_MESSAGES = [
    "LUL", "KEKW", "PogChamp", "Kreygasm", "monkaS",
    "gg", "wp", "nice play!", "omg", "what a shot!",
    "let's go!", "clutch", "rip", "F", "hype!",
    "first time here!", "love the stream", "Pog", "poggers",
    "this is insane", "how did you do that?", "amazing"
]


def create_producer() -> KafkaProducer:
    """Create and configure Kafka producer with retry logic."""
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            print(f"✓ Connected to Kafka broker at {KAFKA_BROKER}")
            return producer
        except KafkaError as e:
            print(f"✗ Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise

    raise Exception("Failed to connect to Kafka after max retries")


def generate_chat_message(stream_id: str) -> Dict:
    """Generate a synthetic chat message."""
    return {
        "stream_id": stream_id,
        "user": random.choice(USERNAMES),
        "message": random.choice(CHAT_MESSAGES),
        "timestamp": datetime.utcnow().isoformat(),
        "is_subscription": random.random() < 0.05,  # 5% chance of sub message
        "is_moderator": random.random() < 0.1  # 10% chance of moderator
    }


def generate_viewer_count(stream_id: str, base_viewers: Dict[str, int]) -> Dict:
    """Generate viewer count with realistic fluctuations."""
    # Initialize base viewer count if not exists
    if stream_id not in base_viewers:
        base_viewers[stream_id] = random.randint(1000, 50000)

    # Fluctuate viewer count by ±5%
    current = base_viewers[stream_id]
    change = int(current * random.uniform(-0.05, 0.05))
    new_count = max(100, current + change)  # Minimum 100 viewers
    base_viewers[stream_id] = new_count

    return {
        "stream_id": stream_id,
        "viewer_count": new_count,
        "timestamp": datetime.utcnow().isoformat()
    }


def send_message(producer: KafkaProducer, topic: str, message: Dict) -> None:
    """Send a message to Kafka topic."""
    try:
        future = producer.send(topic, value=message)
        future.get(timeout=10)  # Block until message is sent
    except Exception as e:
        print(f"✗ Error sending message to {topic}: {e}")


def main():
    """Main producer loop."""
    print("=" * 60)
    print("Twitch Mock Data Producer")
    print("=" * 60)
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Chat Topic: {CHAT_TOPIC}")
    print(f"Viewer Topic: {VIEWER_TOPIC}")
    print(f"Stream IDs: {', '.join(STREAM_IDS)}")
    print(f"Message Rate: {MESSAGE_RATE_MIN}s - {MESSAGE_RATE_MAX}s")
    print("=" * 60)

    # Create producer
    producer = create_producer()

    # Track viewer counts per stream
    base_viewers = {}

    # Counters
    chat_count = 0
    viewer_count = 0

    print("\n🚀 Starting data generation... (Press Ctrl+C to stop)\n")

    try:
        while True:
            # Select random stream
            stream_id = random.choice(STREAM_IDS)

            # Decide what to generate (80% chat, 20% viewer update)
            if random.random() < 0.8:
                # Generate chat message
                chat_msg = generate_chat_message(stream_id)
                send_message(producer, CHAT_TOPIC, chat_msg)
                chat_count += 1
                print(f"📨 Chat [{chat_count:4d}] {stream_id:12s} | {chat_msg['user']:12s}: {chat_msg['message']}")
            else:
                # Generate viewer count update
                viewer_msg = generate_viewer_count(stream_id, base_viewers)
                send_message(producer, VIEWER_TOPIC, viewer_msg)
                viewer_count += 1
                print(f"👥 View [{viewer_count:4d}] {stream_id:12s} | Viewers: {viewer_msg['viewer_count']:6d}")

            # Random delay between messages
            delay = random.uniform(MESSAGE_RATE_MIN, MESSAGE_RATE_MAX)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping producer...")
        print(f"📊 Final Stats:")
        print(f"   - Chat messages sent: {chat_count}")
        print(f"   - Viewer updates sent: {viewer_count}")
        print(f"   - Total messages: {chat_count + viewer_count}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
    finally:
        producer.flush()
        producer.close()
        print("✓ Producer closed cleanly")


if __name__ == "__main__":
    main()
