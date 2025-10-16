#!/usr/bin/env python3
"""
Simple test consumer to verify Twitch mock producer is working.

Usage:
    python test_consumer.py [topic_name]

Example:
    python test_consumer.py telemetra.events.chat
    python test_consumer.py  # consumes from all topics
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

from confluent_kafka import Consumer, KafkaError, KafkaException


# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPICS = [
    "telemetra.events.chat",
    "telemetra.events.viewer",
    "telemetra.events.transactions",
    "telemetra.events.stream_meta"
]


def format_message(topic: str, msg_data: Dict[str, Any]) -> str:
    """Format message for display"""
    timestamp = msg_data.get("timestamp", "")

    if topic == "telemetra.events.chat":
        return (
            f"[CHAT] {msg_data.get('username', 'unknown')}: "
            f"{msg_data.get('message', '')} "
            f"| emotes: {', '.join(msg_data.get('emotes', []))}"
        )

    elif topic == "telemetra.events.viewer":
        return (
            f"[VIEWER] Channel: {msg_data.get('channel', 'unknown')} | "
            f"Viewers: {msg_data.get('viewer_count', 0)} | "
            f"Chatters: {msg_data.get('chatter_count', 0)}"
        )

    elif topic == "telemetra.events.transactions":
        return (
            f"[TRANSACTION] {msg_data.get('transaction_type', 'unknown').upper()} | "
            f"{msg_data.get('username', 'anonymous')}: "
            f"${msg_data.get('amount', 0):.2f} to {msg_data.get('channel', 'unknown')}"
        )

    elif topic == "telemetra.events.stream_meta":
        event_type = msg_data.get('event_type', 'unknown')
        channel = msg_data.get('channel', 'unknown')

        if event_type == "stream_start":
            return (
                f"[META] STREAM START | {channel} | "
                f"Title: {msg_data.get('title', 'N/A')} | "
                f"Category: {msg_data.get('category', 'N/A')}"
            )
        elif event_type == "stream_end":
            return f"[META] STREAM END | {channel}"
        elif event_type == "raid_incoming":
            raid_data = msg_data.get('raid_data', {})
            return (
                f"[META] RAID INCOMING | {channel} | "
                f"From: {raid_data.get('from_channel', 'unknown')} | "
                f"Viewers: {raid_data.get('viewer_count', 0)}"
            )
        else:
            return f"[META] {event_type.upper()} | {channel}"

    return f"[UNKNOWN] {topic}"


def consume_messages(topics, max_messages=None):
    """Consume and display messages from topics"""
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': f'test-consumer-{datetime.now().timestamp()}',
        'auto.offset.reset': 'earliest',  # Start from beginning
        'enable.auto.commit': True
    }

    consumer = Consumer(conf)
    consumer.subscribe(topics)

    print(f"Subscribed to topics: {', '.join(topics)}")
    print(f"Kafka brokers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Waiting for messages... (Ctrl+C to stop)\n")
    print("=" * 80)

    message_count = 0
    topic_counts = {topic: 0 for topic in topics}

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition
                    continue
                else:
                    raise KafkaException(msg.error())

            # Parse message
            try:
                topic = msg.topic()
                value = json.loads(msg.value().decode('utf-8'))

                # Display message
                formatted = format_message(topic, value)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {formatted}")

                message_count += 1
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

                # Print statistics every 50 messages
                if message_count % 50 == 0:
                    print("\n" + "-" * 80)
                    print(f"Messages consumed: {message_count}")
                    for t, count in topic_counts.items():
                        if count > 0:
                            print(f"  {t}: {count}")
                    print("-" * 80 + "\n")

                # Stop if max_messages reached
                if max_messages and message_count >= max_messages:
                    print(f"\nReached max messages ({max_messages}), stopping...")
                    break

            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing message: {e}", file=sys.stderr)

    except KeyboardInterrupt:
        print("\n\nStopping consumer...")

    finally:
        # Print final statistics
        print("\n" + "=" * 80)
        print(f"Total messages consumed: {message_count}")
        for topic, count in topic_counts.items():
            if count > 0:
                print(f"  {topic}: {count}")
        print("=" * 80)

        consumer.close()


def main():
    """Main entry point"""
    topics = TOPICS

    # Override with command line argument if provided
    if len(sys.argv) > 1:
        topics = [sys.argv[1]]

    # Optional: limit number of messages for testing
    max_messages = None
    if len(sys.argv) > 2:
        try:
            max_messages = int(sys.argv[2])
        except ValueError:
            print(f"Invalid max_messages: {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)

    try:
        consume_messages(topics, max_messages)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
