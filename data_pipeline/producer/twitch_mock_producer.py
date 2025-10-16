#!/usr/bin/env python3
"""
Twitch Mock Data Producer for Telemetra MVP

Generates realistic Twitch-like streaming data and publishes to Kafka topics:
- telemetra.events.chat: Chat messages with emotes and sentiment
- telemetra.events.viewer: Viewer count updates
- telemetra.events.transactions: Donations, subscriptions, bits
- telemetra.events.stream_meta: Stream lifecycle events

Environment Variables:
    KAFKA_BOOTSTRAP_SERVERS: Kafka broker address (default: kafka:9092)
    CHANNELS: Comma-separated list of channels (default: demo_stream)
    RATE_PER_SEC: Messages per second (default: 10)
    MESSAGE_VARIANTS: Number of message templates to use (default: 50)
    LOG_LEVEL: Logging level (default: INFO)
    PRODUCE_CHAT: Enable chat message production (default: true)
    PRODUCE_VIEWER: Enable viewer count production (default: true)
    PRODUCE_TRANSACTIONS: Enable transaction production (default: true)
    PRODUCE_STREAM_META: Enable stream metadata production (default: true)
"""

import json
import logging
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from confluent_kafka import Producer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic


# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Configuration from environment
@dataclass
class ProducerConfig:
    """Configuration for the mock producer"""
    kafka_bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    )
    channels: List[str] = field(
        default_factory=lambda: os.getenv("CHANNELS", "demo_stream").split(",")
    )
    rate_per_sec: float = field(
        default_factory=lambda: float(os.getenv("RATE_PER_SEC", "10"))
    )
    message_variants: int = field(
        default_factory=lambda: int(os.getenv("MESSAGE_VARIANTS", "50"))
    )
    produce_chat: bool = field(
        default_factory=lambda: os.getenv("PRODUCE_CHAT", "true").lower() == "true"
    )
    produce_viewer: bool = field(
        default_factory=lambda: os.getenv("PRODUCE_VIEWER", "true").lower() == "true"
    )
    produce_transactions: bool = field(
        default_factory=lambda: os.getenv("PRODUCE_TRANSACTIONS", "true").lower() == "true"
    )
    produce_stream_meta: bool = field(
        default_factory=lambda: os.getenv("PRODUCE_STREAM_META", "true").lower() == "true"
    )

    def __post_init__(self):
        """Validate and clean configuration"""
        self.channels = [c.strip() for c in self.channels if c.strip()]
        if not self.channels:
            self.channels = ["demo_stream"]
        logger.info(f"Configuration loaded: {len(self.channels)} channels, {self.rate_per_sec} msg/sec")


# Kafka Topics
TOPICS = {
    "chat": "telemetra.events.chat",
    "viewer": "telemetra.events.viewer",
    "transactions": "telemetra.events.transactions",
    "stream_meta": "telemetra.events.stream_meta"
}


# Mock Data Templates
POPULAR_EMOTES = [
    "Kappa", "PogChamp", "LUL", "KEKW", "Kreygasm", "BibleThump",
    "ResidentSleeper", "4Head", "EZ", "MonkaS", "Pepega", "PepeHands",
    "Sadge", "Pog", "PauseChamp", "widepeepoHappy", "OMEGALUL", "Clap",
    "POGGERS", "FeelsGoodMan", "FeelsBadMan", "TriHard", "CoolStoryBob"
]

USERNAMES = [
    "gamer123", "streamer_fan", "pro_viewer", "chat_master", "meme_lord",
    "epic_gamer", "night_owl", "lurker99", "hype_train", "pog_champ",
    "toxic_gamer", "wholesome_viewer", "sub_legend", "mod_power", "vip_user",
    "tier3_sub", "gifter_king", "raid_boss", "chat_warrior", "emote_spammer",
    "lore_keeper", "clip_hunter", "vod_watcher", "prime_gamer", "twitch_addict",
    "first_viewer", "last_viewer", "lurking_andy", "active_chatter", "hype_man",
    "back_seater", "question_asker", "support_squad", "og_viewer", "new_viewer",
    "bot_suspect", "copypasta_master", "ascii_artist", "spam_reporter", "nice_person",
    "troll_account", "alt_account", "verified_user", "partner_friend", "stream_sniper"
]

CHAT_TEMPLATES = [
    "Hello chat! {emote}",
    "That was insane! {emote} {emote}",
    "GG! {emote}",
    "Let's go! {emote}",
    "What just happened? {emote}",
    "This is so good {emote}",
    "No way! {emote} {emote} {emote}",
    "I can't believe it {emote}",
    "Best stream ever {emote}",
    "First time here! {emote}",
    "How did you do that? {emote}",
    "Amazing play! {emote} {emote}",
    "Subscribed! {emote}",
    "Love this content {emote}",
    "What game is this?",
    "Can you show your settings?",
    "Where are you from?",
    "How long have you been streaming?",
    "What's your rank?",
    "This is so entertaining {emote}",
    "I'm dying {emote} {emote}",
    "Please play more of this!",
    "Congrats on the win! {emote}",
    "You're the best! {emote}",
    "This is why I subbed {emote}",
    "{emote} spam {emote} spam {emote}",
    "Anyone else see that? {emote}",
    "Chat is moving so fast {emote}",
    "Can we get {emote} in chat?",
    "This game looks amazing",
    "I missed it, what happened?",
    "Going to watch the VOD later",
    "Been watching for 3 hours straight {emote}",
    "My favorite streamer! {emote}",
    "This is so chill {emote}",
    "Let's raid someone after!",
    "Who else is here from the raid?",
    "Just followed! {emote}",
    "Notification squad {emote}",
    "Can't stay long but wanted to stop by {emote}",
    "Back from the bathroom, what did I miss?",
    "Making dinner while watching {emote}",
    "Working from home and lurking {emote}",
    "Weekend streams hit different {emote}",
    "Finally off work and catching the stream {emote}",
    "This is my comfort stream {emote}",
    "Been watching since the beginning {emote}",
    "Remember when... nostalgia {emote}",
    "This brings back memories {emote}"
]

DONATION_MESSAGES = [
    "Love the stream! Keep it up!",
    "You deserve this and more!",
    "Thanks for the amazing content!",
    "Best streamer on Twitch!",
    "This is for your hard work!",
    "Keep doing what you're doing!",
    "You've helped me through tough times",
    "Your streams make my day better",
    "Supporting my favorite creator!",
    "Can you say hi to my friend?",
    ""  # Some donations have no message
]

STREAM_CATEGORIES = [
    "Just Chatting", "League of Legends", "Fortnite", "Minecraft",
    "Grand Theft Auto V", "Valorant", "Counter-Strike 2", "Dota 2",
    "World of Warcraft", "Call of Duty", "Apex Legends", "Overwatch 2",
    "Lost Ark", "Escape from Tarkov", "Dead by Daylight", "Rust",
    "Chess", "Music", "Art", "Science & Technology"
]

STREAM_TITLES = [
    "Chill vibes and good times",
    "Grinding ranked all day",
    "New game, who dis?",
    "Subathon Day {day}!",
    "Come hang out!",
    "Learning a new game",
    "Trying to hit {goal} followers!",
    "Best community on Twitch",
    "First stream back!",
    "Charity stream for {cause}",
    "{game} but I'm terrible at it",
    "Viewer games! Join Discord!",
    "Speedrun practice",
    "No commentary, just gameplay",
    "Chatting with viewers",
    "IRL stream adventure",
    "Building something cool",
    "React Andy today",
    "Variety gaming session"
]


class ViewerCountSimulator:
    """Simulates realistic viewer count fluctuations"""

    def __init__(self, base_count: int = 500, volatility: float = 0.15):
        self.base_count = base_count
        self.volatility = volatility
        self.current_count = base_count
        self.trend = 0.0  # Positive for growth, negative for decline
        self.last_update = time.time()

    def update(self) -> int:
        """Generate next viewer count with realistic fluctuations"""
        now = time.time()
        time_delta = now - self.last_update

        # Random walk with trend
        change_rate = random.gauss(self.trend, self.volatility)
        change = int(self.current_count * change_rate * time_delta)

        # Add occasional spikes (raids, hosts, viral moments)
        if random.random() < 0.002:  # 0.2% chance per update
            spike = random.randint(50, 500)
            change += spike
            logger.info(f"Viewer spike: +{spike} viewers!")

        # Add occasional drops (technical issues, boring segment)
        if random.random() < 0.001:  # 0.1% chance per update
            drop = random.randint(20, 200)
            change -= drop
            logger.debug(f"Viewer drop: -{drop} viewers")

        self.current_count = max(10, self.current_count + change)

        # Slowly adjust trend towards zero (regression to mean)
        self.trend *= 0.99

        # Occasionally change trend
        if random.random() < 0.01:
            self.trend = random.gauss(0, 0.05)

        self.last_update = now
        return int(self.current_count)

    def get_chatter_count(self) -> int:
        """Get realistic chatter count (5-20% of viewers)"""
        ratio = random.uniform(0.05, 0.20)
        return max(1, int(self.current_count * ratio))


class TwitchMockProducer:
    """Main producer class for generating and sending mock Twitch data"""

    def __init__(self, config: ProducerConfig):
        self.config = config
        self.producer = None
        self.viewer_simulators: Dict[str, ViewerCountSimulator] = {}
        self.stream_ids: Dict[str, str] = {}
        self.stream_start_times: Dict[str, datetime] = {}
        self.message_counts = {topic: 0 for topic in TOPICS.values()}
        self.running = True

        # Initialize viewer simulators for each channel
        for channel in config.channels:
            base_viewers = random.randint(100, 2000)
            self.viewer_simulators[channel] = ViewerCountSimulator(base_viewers)
            self.stream_ids[channel] = f"stream_{random.randint(1000000000, 9999999999)}"
            self.stream_start_times[channel] = datetime.now(timezone.utc)

    def _delivery_callback(self, err, msg):
        """Callback for delivery reports"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            topic = msg.topic()
            self.message_counts[topic] += 1
            if self.message_counts[topic] % 100 == 0:
                logger.info(
                    f"Delivered {self.message_counts[topic]} messages to {topic} "
                    f"(partition {msg.partition()}, offset {msg.offset()})"
                )

    def _create_producer(self) -> Producer:
        """Create and configure Kafka producer"""
        conf = {
            'bootstrap.servers': self.config.kafka_bootstrap_servers,
            'client.id': f'twitch-mock-producer-{uuid.uuid4().hex[:8]}',
            'acks': 'all',
            'retries': 3,
            'compression.type': 'snappy',
            'linger.ms': 10,
            'batch.size': 16384,
        }

        logger.info(f"Creating Kafka producer with config: {conf}")
        return Producer(conf)

    def _ensure_topics_exist(self):
        """Create topics if they don't exist"""
        try:
            admin_client = AdminClient({
                'bootstrap.servers': self.config.kafka_bootstrap_servers
            })

            existing_topics = admin_client.list_topics(timeout=10).topics
            topics_to_create = []

            for topic_name in TOPICS.values():
                if topic_name not in existing_topics:
                    topics_to_create.append(
                        NewTopic(
                            topic=topic_name,
                            num_partitions=3,
                            replication_factor=1
                        )
                    )

            if topics_to_create:
                logger.info(f"Creating {len(topics_to_create)} topics...")
                fs = admin_client.create_topics(topics_to_create)

                for topic, f in fs.items():
                    try:
                        f.result()
                        logger.info(f"Topic {topic} created successfully")
                    except Exception as e:
                        logger.warning(f"Failed to create topic {topic}: {e}")
            else:
                logger.info("All topics already exist")

        except Exception as e:
            logger.warning(f"Could not ensure topics exist: {e}")

    def connect(self):
        """Connect to Kafka and initialize producer"""
        max_retries = 10
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Kafka at {self.config.kafka_bootstrap_servers} (attempt {attempt + 1}/{max_retries})")
                self.producer = self._create_producer()

                # Test connection by getting metadata
                self.producer.list_topics(timeout=10)

                logger.info("Successfully connected to Kafka")

                # Ensure topics exist
                self._ensure_topics_exist()

                return

            except KafkaException as e:
                logger.error(f"Kafka connection failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise

    def _send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Send a message to Kafka"""
        try:
            key_bytes = key.encode('utf-8') if key else None
            value_bytes = json.dumps(message).encode('utf-8')

            self.producer.produce(
                topic=topic,
                key=key_bytes,
                value=value_bytes,
                callback=self._delivery_callback
            )

        except BufferError:
            logger.warning(f"Local producer queue is full ({len(self.producer)} messages), waiting...")
            self.producer.poll(1.0)
            self._send_message(topic, message, key)
        except Exception as e:
            logger.error(f"Error sending message to {topic}: {e}")

    def generate_chat_message(self, channel: str) -> Dict[str, Any]:
        """Generate a realistic chat message"""
        username = random.choice(USERNAMES)
        user_id = f"user_{random.randint(100000, 9999999)}"

        # Select message template and add emotes
        template = random.choice(CHAT_TEMPLATES)
        emotes_in_msg = []
        message = template

        while "{emote}" in message:
            emote = random.choice(POPULAR_EMOTES)
            emotes_in_msg.append(emote)
            message = message.replace("{emote}", emote, 1)

        # Determine sentiment based on content
        sentiment_hints = ["positive", "neutral", "excited", "question"]
        weights = [0.5, 0.3, 0.15, 0.05]

        if "?" in message:
            sentiment = "question"
        elif any(word in message.lower() for word in ["love", "best", "amazing", "gg"]):
            sentiment = "positive"
        elif any(emote in emotes_in_msg for emote in ["POGGERS", "PogChamp", "Pog"]):
            sentiment = "excited"
        else:
            sentiment = random.choices(sentiment_hints, weights=weights)[0]

        # Assign badges
        badges = []
        if random.random() < 0.15:  # 15% are subscribers
            badges.append("subscriber")
        if random.random() < 0.02:  # 2% are moderators
            badges.append("moderator")
        if random.random() < 0.01:  # 1% are VIPs
            badges.append("vip")

        # Occasional bits in messages
        bits = 0
        if random.random() < 0.03:  # 3% of messages have bits
            bits = random.choice([1, 5, 10, 25, 50, 100, 500, 1000])
            message += f" (cheered {bits} bits)"

        return {
            "message_id": str(uuid.uuid4()),
            "channel": channel,
            "username": username,
            "user_id": user_id,
            "message": message,
            "emotes": list(set(emotes_in_msg)),
            "badges": badges,
            "is_action": random.random() < 0.05,
            "bits": bits,
            "sentiment_hint": sentiment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "client": random.choice(["web", "mobile", "desktop"]),
                "color": f"#{random.randint(0, 0xFFFFFF):06x}"
            }
        }

    def generate_viewer_update(self, channel: str) -> Dict[str, Any]:
        """Generate viewer count update"""
        simulator = self.viewer_simulators[channel]
        viewer_count = simulator.update()
        chatter_count = simulator.get_chatter_count()

        # Calculate stream uptime
        uptime = (datetime.now(timezone.utc) - self.stream_start_times[channel]).total_seconds()

        return {
            "event_id": str(uuid.uuid4()),
            "channel": channel,
            "viewer_count": viewer_count,
            "chatter_count": chatter_count,
            "follower_count": random.randint(10000, 500000),
            "subscriber_count": int(viewer_count * random.uniform(0.01, 0.05)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "peak_today": int(viewer_count * random.uniform(1.0, 1.5)),
                "stream_uptime_seconds": int(uptime)
            }
        }

    def generate_transaction(self, channel: str) -> Optional[Dict[str, Any]]:
        """Generate a transaction (donations, subs, bits)"""
        # Transactions are less frequent
        if random.random() > 0.05:  # Only 5% chance when called
            return None

        transaction_type = random.choices(
            ["donation", "subscription", "bits", "gift_sub", "subscription_renewal"],
            weights=[0.20, 0.30, 0.25, 0.15, 0.10]
        )[0]

        username = random.choice(USERNAMES)
        user_id = f"user_{random.randint(100000, 9999999)}"

        transaction = {
            "transaction_id": f"txn_{uuid.uuid4().hex[:16]}",
            "channel": channel,
            "username": username,
            "user_id": user_id,
            "transaction_type": transaction_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_anonymous": random.random() < 0.05,
            "currency": "USD",
        }

        if transaction_type == "donation":
            amount = random.choice([1.00, 2.00, 5.00, 10.00, 20.00, 50.00, 100.00, 500.00])
            transaction["amount"] = amount
            transaction["message"] = random.choice(DONATION_MESSAGES)

        elif transaction_type in ["subscription", "subscription_renewal"]:
            tier = random.choices(
                ["tier1", "tier2", "tier3", "prime"],
                weights=[0.60, 0.20, 0.15, 0.05]
            )[0]
            tier_amounts = {"tier1": 4.99, "tier2": 9.99, "tier3": 24.99, "prime": 0.00}
            transaction["amount"] = tier_amounts[tier]
            transaction["tier"] = tier
            transaction["months"] = random.randint(1, 60)
            transaction["streak_months"] = random.randint(0, transaction["months"])

        elif transaction_type == "gift_sub":
            transaction["amount"] = 4.99
            transaction["tier"] = "tier1"
            transaction["gift_count"] = random.choice([1, 5, 10, 20, 50, 100])
            transaction["amount"] *= transaction["gift_count"]

        elif transaction_type == "bits":
            bits_amount = random.choice([100, 500, 1000, 5000, 10000])
            transaction["amount"] = bits_amount
            transaction["message"] = random.choice(DONATION_MESSAGES)

        transaction["metadata"] = {
            "payment_method": random.choice(["credit_card", "paypal", "crypto", "gift_card"]),
            "refundable": transaction_type != "bits"
        }

        return transaction

    def generate_stream_meta(self, channel: str) -> Optional[Dict[str, Any]]:
        """Generate stream metadata event"""
        # Metadata events are rare
        if random.random() > 0.02:  # Only 2% chance when called
            return None

        event_type = random.choices(
            ["title_change", "category_change", "raid_incoming"],
            weights=[0.40, 0.40, 0.20]
        )[0]

        event = {
            "event_id": str(uuid.uuid4()),
            "channel": channel,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stream_id": self.stream_ids[channel],
            "language": "en",
            "is_mature": random.random() < 0.1,
        }

        if event_type == "title_change":
            title_template = random.choice(STREAM_TITLES)
            title = title_template.format(
                day=random.randint(1, 7),
                goal=random.choice(["1K", "5K", "10K"]),
                cause=random.choice(["St. Jude", "charity: water", "Red Cross"]),
                game=random.choice(STREAM_CATEGORIES[:10])
            )
            event["title"] = title

        elif event_type == "category_change":
            event["category"] = random.choice(STREAM_CATEGORIES)
            event["category_id"] = f"cat_{random.randint(100000, 9999999)}"
            event["tags"] = random.sample(
                ["English", "Competitive", "Casual", "Educational", "Speedrun"],
                k=random.randint(1, 3)
            )

        elif event_type == "raid_incoming":
            event["raid_data"] = {
                "from_channel": random.choice(USERNAMES),
                "viewer_count": random.randint(50, 5000)
            }
            logger.info(f"Raid incoming to {channel}! {event['raid_data']['viewer_count']} viewers!")

        event["metadata"] = {
            "stream_quality": random.choice(["source", "1080p60", "1080p", "720p60"]),
            "encoder": random.choice(["x264", "NVENC", "QuickSync"])
        }

        return event

    def produce_messages(self):
        """Main loop to produce messages"""
        logger.info("Starting message production...")
        logger.info(f"Target rate: {self.config.rate_per_sec} messages/second")
        logger.info(f"Channels: {', '.join(self.config.channels)}")

        # Calculate sleep time between messages
        sleep_time = 1.0 / self.config.rate_per_sec if self.config.rate_per_sec > 0 else 0.1

        # Send initial stream_start events
        if self.config.produce_stream_meta:
            for channel in self.config.channels:
                event = {
                    "event_id": str(uuid.uuid4()),
                    "channel": channel,
                    "event_type": "stream_start",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stream_id": self.stream_ids[channel],
                    "title": random.choice(STREAM_TITLES).format(
                        day=1, goal="5K", cause="charity", game="Gaming"
                    ),
                    "category": random.choice(STREAM_CATEGORIES),
                    "category_id": f"cat_{random.randint(100000, 9999999)}",
                    "language": "en",
                    "is_mature": False,
                    "tags": ["English", "Casual"],
                    "metadata": {
                        "stream_quality": "1080p60",
                        "encoder": "NVENC"
                    }
                }
                self._send_message(TOPICS["stream_meta"], event, channel)
                logger.info(f"Stream started for channel: {channel}")

        message_count = 0
        start_time = time.time()

        try:
            while self.running:
                # Select a random channel
                channel = random.choice(self.config.channels)

                # Determine what type of message to send (weighted distribution)
                message_type = random.choices(
                    ["chat", "viewer", "transaction", "meta"],
                    weights=[0.70, 0.20, 0.05, 0.05]
                )[0]

                # Generate and send message based on type
                if message_type == "chat" and self.config.produce_chat:
                    msg = self.generate_chat_message(channel)
                    self._send_message(TOPICS["chat"], msg, channel)

                elif message_type == "viewer" and self.config.produce_viewer:
                    msg = self.generate_viewer_update(channel)
                    self._send_message(TOPICS["viewer"], msg, channel)

                elif message_type == "transaction" and self.config.produce_transactions:
                    msg = self.generate_transaction(channel)
                    if msg:
                        self._send_message(TOPICS["transactions"], msg, channel)
                        logger.info(
                            f"Transaction: {msg['transaction_type']} "
                            f"${msg['amount']:.2f} from {msg['username']} to {channel}"
                        )

                elif message_type == "meta" and self.config.produce_stream_meta:
                    msg = self.generate_stream_meta(channel)
                    if msg:
                        self._send_message(TOPICS["stream_meta"], msg, channel)

                # Poll for delivery reports
                self.producer.poll(0)

                message_count += 1

                # Log statistics every 100 messages
                if message_count % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_rate = message_count / elapsed
                    logger.info(
                        f"Produced {message_count} messages | "
                        f"Actual rate: {actual_rate:.2f} msg/sec | "
                        f"Total by topic: {self.message_counts}"
                    )

                # Sleep to maintain target rate
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown the producer"""
        logger.info("Shutting down producer...")

        # Send stream_end events
        if self.config.produce_stream_meta and self.producer:
            for channel in self.config.channels:
                event = {
                    "event_id": str(uuid.uuid4()),
                    "channel": channel,
                    "event_type": "stream_end",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stream_id": self.stream_ids[channel],
                    "language": "en",
                    "metadata": {}
                }
                self._send_message(TOPICS["stream_meta"], event, channel)
                logger.info(f"Stream ended for channel: {channel}")

        if self.producer:
            logger.info("Flushing remaining messages...")
            self.producer.flush(timeout=30)
            logger.info("Producer shutdown complete")

        # Print final statistics
        total_messages = sum(self.message_counts.values())
        logger.info(f"Final statistics:")
        logger.info(f"  Total messages produced: {total_messages}")
        for topic, count in self.message_counts.items():
            logger.info(f"  {topic}: {count}")


def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("Twitch Mock Producer for Telemetra MVP")
    logger.info("=" * 80)

    # Load configuration
    config = ProducerConfig()

    # Create and run producer
    producer = TwitchMockProducer(config)

    try:
        producer.connect()
        producer.produce_messages()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
