"""
Unit tests for Telemetra Spark Streaming Job

Tests core functionality including:
- Sentiment scoring
- Schema definitions
- Data transformations
- Utility functions

Run with: pytest test_spark_job.py -v
"""

import pytest
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType, ArrayType

from spark_streaming_job import TelemetraStreamingJob


@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing."""
    spark = (SparkSession.builder
             .appName("TelemetraTests")
             .master("local[2]")
             .config("spark.sql.shuffle.partitions", "2")
             .getOrCreate())

    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()


@pytest.fixture
def job():
    """Create a TelemetraStreamingJob instance."""
    import os
    # Set test environment variables
    os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
    os.environ['POSTGRES_URL'] = 'jdbc:postgresql://localhost:5432/test'
    os.environ['POSTGRES_USER'] = 'test'
    os.environ['POSTGRES_PASSWORD'] = 'test'
    os.environ['CHECKPOINT_LOCATION'] = '/tmp/test-checkpoints'

    return TelemetraStreamingJob()


class TestSentimentScoring:
    """Test suite for sentiment analysis functionality."""

    def test_positive_sentiment(self, job):
        """Test positive sentiment scoring."""
        message = "This stream is awesome and amazing! Love it!"
        score = job.compute_sentiment_score(message)
        assert score > 0, "Should return positive score"
        assert -1.0 <= score <= 1.0, "Score should be between -1 and 1"

    def test_negative_sentiment(self, job):
        """Test negative sentiment scoring."""
        message = "This is terrible and boring, hate it"
        score = job.compute_sentiment_score(message)
        assert score < 0, "Should return negative score"
        assert -1.0 <= score <= 1.0, "Score should be between -1 and 1"

    def test_neutral_sentiment(self, job):
        """Test neutral sentiment scoring."""
        message = "The stream started at 3pm today"
        score = job.compute_sentiment_score(message)
        assert score == 0.0, "Should return neutral score for no sentiment words"

    def test_mixed_sentiment(self, job):
        """Test mixed sentiment scoring."""
        message = "The game is great but the lag is terrible"
        score = job.compute_sentiment_score(message)
        assert -1.0 <= score <= 1.0, "Score should be between -1 and 1"

    def test_empty_message(self, job):
        """Test empty message handling."""
        score = job.compute_sentiment_score("")
        assert score == 0.0, "Empty message should return neutral score"

    def test_case_insensitive(self, job):
        """Test that sentiment scoring is case-insensitive."""
        message_lower = "this is awesome"
        message_upper = "THIS IS AWESOME"
        score_lower = job.compute_sentiment_score(message_lower)
        score_upper = job.compute_sentiment_score(message_upper)
        assert score_lower == score_upper, "Scoring should be case-insensitive"


class TestSchemaDefinitions:
    """Test suite for schema definitions."""

    def test_chat_schema_structure(self, job):
        """Test chat event schema has all required fields."""
        schema = job.get_chat_schema()

        assert isinstance(schema, StructType)
        field_names = [field.name for field in schema.fields]

        required_fields = [
            'event_id', 'timestamp', 'stream_id', 'user_id',
            'username', 'message', 'emotes', 'badges'
        ]

        for field in required_fields:
            assert field in field_names, f"Missing required field: {field}"

    def test_chat_schema_types(self, job):
        """Test chat event schema has correct field types."""
        schema = job.get_chat_schema()
        field_types = {field.name: type(field.dataType).__name__ for field in schema.fields}

        assert field_types['event_id'] == 'StringType'
        assert field_types['timestamp'] == 'TimestampType'
        assert field_types['stream_id'] == 'StringType'
        assert field_types['user_id'] == 'StringType'
        assert field_types['username'] == 'StringType'
        assert field_types['message'] == 'StringType'
        assert field_types['emotes'] == 'ArrayType'
        assert field_types['badges'] == 'ArrayType'

    def test_viewer_schema_structure(self, job):
        """Test viewer event schema has all required fields."""
        schema = job.get_viewer_schema()

        assert isinstance(schema, StructType)
        field_names = [field.name for field in schema.fields]

        required_fields = ['event_id', 'timestamp', 'stream_id', 'viewer_count']

        for field in required_fields:
            assert field in field_names, f"Missing required field: {field}"

    def test_viewer_schema_types(self, job):
        """Test viewer event schema has correct field types."""
        schema = job.get_viewer_schema()
        field_types = {field.name: type(field.dataType).__name__ for field in schema.fields}

        assert field_types['event_id'] == 'StringType'
        assert field_types['timestamp'] == 'TimestampType'
        assert field_types['stream_id'] == 'StringType'
        assert field_types['viewer_count'] == 'IntegerType'


class TestDataTransformations:
    """Test suite for data transformation operations."""

    def test_enrich_with_sentiment(self, spark, job):
        """Test sentiment enrichment adds correct column."""
        # Create sample data
        data = [
            ("msg1", "2024-10-16 10:00:00", "stream1", "user1", "Great stream!"),
            ("msg2", "2024-10-16 10:00:01", "stream1", "user2", "This is terrible"),
            ("msg3", "2024-10-16 10:00:02", "stream1", "user3", "Hello everyone"),
        ]

        df = spark.createDataFrame(data, ["event_id", "timestamp", "stream_id", "user_id", "message"])
        df = df.withColumn("timestamp", df["timestamp"].cast("timestamp"))
        df = df.withColumn("emotes", df.sql.functions.array())
        df = df.withColumn("badges", df.sql.functions.array())

        # Enrich with sentiment
        enriched = job.enrich_with_sentiment(df)

        # Verify sentiment_score column exists
        assert "sentiment_score" in enriched.columns

        # Collect results
        results = enriched.select("message", "sentiment_score").collect()

        # Check sentiment scores are in valid range
        for row in results:
            assert -1.0 <= row.sentiment_score <= 1.0


class TestConfiguration:
    """Test suite for configuration and initialization."""

    def test_default_configuration(self, job):
        """Test default configuration values."""
        assert job.kafka_bootstrap_servers is not None
        assert job.postgres_url is not None
        assert job.postgres_user is not None
        assert job.postgres_password is not None
        assert job.checkpoint_location is not None
        assert job.anomaly_threshold > 0

    def test_anomaly_threshold_type(self, job):
        """Test anomaly threshold is float."""
        assert isinstance(job.anomaly_threshold, float)

    def test_checkpoint_location_set(self, job):
        """Test checkpoint location is configured."""
        assert len(job.checkpoint_location) > 0


class TestSparkSession:
    """Test suite for Spark session creation."""

    def test_spark_session_creation(self, job):
        """Test Spark session can be created."""
        spark = job.create_spark_session()
        assert spark is not None
        assert spark.sparkContext is not None
        spark.stop()

    def test_spark_configuration(self, job):
        """Test Spark session has required configuration."""
        spark = job.create_spark_session()

        # Check important configs are set
        conf = spark.sparkContext.getConf()
        assert conf.get("spark.app.name") == "TelemetraStreamingAnalytics"

        spark.stop()


class TestLexicons:
    """Test suite for sentiment lexicons."""

    def test_positive_words_exist(self):
        """Test positive word lexicon is not empty."""
        assert len(TelemetraStreamingJob.POSITIVE_WORDS) > 0

    def test_negative_words_exist(self):
        """Test negative word lexicon is not empty."""
        assert len(TelemetraStreamingJob.NEGATIVE_WORDS) > 0

    def test_no_overlap_in_lexicons(self):
        """Test positive and negative lexicons don't overlap."""
        overlap = (TelemetraStreamingJob.POSITIVE_WORDS &
                  TelemetraStreamingJob.NEGATIVE_WORDS)
        assert len(overlap) == 0, f"Overlapping words found: {overlap}"

    def test_lexicon_format(self):
        """Test lexicons contain only lowercase strings."""
        for word in TelemetraStreamingJob.POSITIVE_WORDS:
            assert isinstance(word, str)
            assert word.islower()

        for word in TelemetraStreamingJob.NEGATIVE_WORDS:
            assert isinstance(word, str)
            assert word.islower()


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring actual services (marked for optional running)."""

    def test_kafka_connection(self, job):
        """Test Kafka connectivity (requires running Kafka)."""
        pytest.skip("Requires running Kafka instance")

    def test_postgres_connection(self, job):
        """Test PostgreSQL connectivity (requires running database)."""
        pytest.skip("Requires running PostgreSQL instance")

    def test_end_to_end_processing(self, job):
        """Test complete pipeline (requires all services)."""
        pytest.skip("Requires complete infrastructure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
