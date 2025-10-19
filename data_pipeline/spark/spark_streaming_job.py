"""
Telemetra PySpark Streaming Job

This module implements a real-time streaming analytics pipeline that:
1. Consumes events from Kafka topics (chat, viewer)
2. Applies windowed aggregations with watermarking
3. Performs sentiment analysis and anomaly detection
4. Writes results to PostgreSQL via JDBC

Author: Telemetra Team
License: MIT
"""

import logging
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, window, count, countDistinct, avg, sum as spark_sum,
    collect_list, explode, split, regexp_extract, when, lit, stddev_pop,
    mean, current_timestamp, to_json, struct, expr, unix_timestamp,
    array_distinct, flatten, size, concat_ws, udf
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    TimestampType, DoubleType, ArrayType, LongType
)
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelemetraStreamingJob:
    """Main streaming job class for Telemetra analytics pipeline."""

    # Sentiment lexicons (simple baseline for MVP)
    POSITIVE_WORDS = {
        'love', 'great', 'awesome', 'amazing', 'excellent', 'good', 'best',
        'wonderful', 'fantastic', 'perfect', 'happy', 'thanks', 'lol', 'haha',
        'nice', 'cool', 'fun', 'enjoy', 'excited', 'pog', 'pogchamp', 'kekw'
    }

    NEGATIVE_WORDS = {
        'hate', 'bad', 'terrible', 'awful', 'worst', 'sucks', 'boring',
        'annoying', 'stupid', 'dumb', 'trash', 'cringe', 'fail', 'rip',
        'sad', 'angry', 'mad', 'disappointed', 'frustrated'
    }

    def __init__(self):
        """Initialize the streaming job with configuration from environment."""
        self.kafka_bootstrap_servers = os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
        )
        self.postgres_url = os.getenv(
            'POSTGRES_URL', 'jdbc:postgresql://postgres:5432/telemetra'
        )
        self.postgres_user = os.getenv('POSTGRES_USER', 'telemetra')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'telemetra')
        self.checkpoint_location = os.getenv(
            'CHECKPOINT_LOCATION', '/tmp/spark-checkpoints'
        )
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '3.0'))

        logger.info(f"Initialized with Kafka: {self.kafka_bootstrap_servers}")
        logger.info(f"Postgres URL: {self.postgres_url}")
        logger.info(f"Checkpoint location: {self.checkpoint_location}")

    def create_spark_session(self) -> SparkSession:
        """Create and configure Spark session with required packages."""
        logger.info("Creating Spark session...")

        spark = (SparkSession.builder
                 .appName("TelemetraStreamingAnalytics")
                 .config("spark.jars.packages",
                         "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                         "org.postgresql:postgresql:42.7.1")
                 .config("spark.sql.streaming.checkpointLocation",
                         self.checkpoint_location)
                 .config("spark.sql.streaming.schemaInference", "true")
                 .config("spark.sql.adaptive.enabled", "true")
                 .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                 .config("spark.streaming.stopGracefullyOnShutdown", "true")
                 .getOrCreate())

        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"Spark session created: {spark.version}")
        return spark

    @staticmethod
    def get_chat_schema() -> StructType:
        """Define schema for chat events."""
        return StructType([
            StructField("event_id", StringType(), False),
            StructField("timestamp", TimestampType(), False),
            StructField("stream_id", StringType(), False),
            StructField("user_id", StringType(), False),
            StructField("username", StringType(), False),
            StructField("message", StringType(), False),
            StructField("emotes", ArrayType(StringType()), True),
            StructField("badges", ArrayType(StringType()), True),
        ])

    @staticmethod
    def get_viewer_schema() -> StructType:
        """Define schema for viewer events."""
        return StructType([
            StructField("event_id", StringType(), False),
            StructField("timestamp", TimestampType(), False),
            StructField("stream_id", StringType(), False),
            StructField("viewer_count", IntegerType(), False),
        ])

    def read_kafka_stream(
        self, spark: SparkSession, topic: str, schema: StructType
    ) -> DataFrame:
        """
        Read and parse JSON messages from Kafka topic.

        Args:
            spark: Active Spark session
            topic: Kafka topic name
            schema: Schema for parsing JSON

        Returns:
            DataFrame with parsed events
        """
        logger.info(f"Reading from Kafka topic: {topic}")

        df = (spark.readStream
              .format("kafka")
              .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
              .option("subscribe", topic)
              .option("startingOffsets", "latest")
              .option("maxOffsetsPerTrigger", 10000)
              .option("failOnDataLoss", "false")
              .load())

        # Parse JSON value
        parsed_df = (df.selectExpr("CAST(value AS STRING) as json_value")
                     .select(from_json(col("json_value"), schema).alias("data"))
                     .select("data.*"))

        return parsed_df

    @staticmethod
    def compute_sentiment_score(message: str) -> float:
        """
        Compute simple sentiment score based on lexicon matching.

        Args:
            message: Chat message text

        Returns:
            Sentiment score between -1.0 and 1.0
        """
        if not message:
            return 0.0

        words = set(message.lower().split())
        positive_count = len(words & TelemetraStreamingJob.POSITIVE_WORDS)
        negative_count = len(words & TelemetraStreamingJob.NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    def enrich_with_sentiment(self, chat_df: DataFrame) -> DataFrame:
        """
        Add sentiment scores to chat messages.

        Args:
            chat_df: DataFrame with chat messages

        Returns:
            DataFrame with sentiment_score column
        """
        # Register UDF for sentiment computation
        sentiment_udf = udf(self.compute_sentiment_score, DoubleType())

        return chat_df.withColumn(
            "sentiment_score",
            sentiment_udf(col("message"))
        )

    def aggregate_chat_metrics(self, chat_df: DataFrame) -> DataFrame:
        """
        Compute windowed aggregations on chat stream.

        Applies:
        - 10-second watermark for late data
        - 1-minute tumbling windows with 10-second slide
        - Multiple aggregations: count, unique users, top emotes

        Args:
            chat_df: Enriched chat DataFrame

        Returns:
            Aggregated metrics per window
        """
        logger.info("Computing chat aggregations with windowing...")

        # Apply watermarking and windowing
        windowed = (chat_df
                    .withWatermark("timestamp", "10 seconds")
                    .groupBy(
                        window(col("timestamp"), "1 minute", "10 seconds"),
                        col("stream_id")
                    ))

        # Compute aggregations
        aggregated = windowed.agg(
            count("*").alias("chat_count"),
            countDistinct("user_id").alias("unique_chatters"),
            avg("sentiment_score").alias("avg_sentiment"),
            collect_list("emotes").alias("all_emotes_nested"),
            spark_sum(when(col("sentiment_score") > 0, 1).otherwise(0))
                .alias("positive_count"),
            spark_sum(when(col("sentiment_score") < 0, 1).otherwise(0))
                .alias("negative_count")
        )

        # Flatten and process emotes
        aggregated = aggregated.withColumn(
            "all_emotes",
            flatten(col("all_emotes_nested"))
        )

        # Get top emotes by frequency
        aggregated = aggregated.withColumn(
            "emote_list",
            expr("slice(array_sort(all_emotes), 1, 10)")  # Top 10 emotes
        )

        # Compute chat rate (messages per second)
        aggregated = aggregated.withColumn(
            "chat_rate",
            col("chat_count") / 60.0  # Per 60-second window
        )

        # Add window start/end as proper columns
        aggregated = (aggregated
                      .withColumn("window_start", col("window.start"))
                      .withColumn("window_end", col("window.end"))
                      .drop("window", "all_emotes_nested", "all_emotes"))

        return aggregated

    def aggregate_viewer_metrics(self, viewer_df: DataFrame) -> DataFrame:
        """
        Compute windowed aggregations on viewer stream.

        Args:
            viewer_df: Viewer count DataFrame

        Returns:
            Aggregated viewer metrics per window
        """
        logger.info("Computing viewer aggregations...")

        aggregated = (viewer_df
                      .withWatermark("timestamp", "10 seconds")
                      .groupBy(
                          window(col("timestamp"), "1 minute", "10 seconds"),
                          col("stream_id")
                      )
                      .agg(
                          avg("viewer_count").alias("avg_viewers"),
                          count("*").alias("viewer_events")
                      )
                      .withColumn("window_start", col("window.start"))
                      .withColumn("window_end", col("window.end"))
                      .drop("window"))

        return aggregated

    def join_metrics(
        self, chat_agg: DataFrame, viewer_agg: DataFrame
    ) -> DataFrame:
        """
        Join chat and viewer aggregations on window and stream_id.

        Args:
            chat_agg: Aggregated chat metrics
            viewer_agg: Aggregated viewer metrics

        Returns:
            Combined metrics DataFrame
        """
        logger.info("Joining chat and viewer metrics...")

        joined = chat_agg.join(
            viewer_agg,
            on=["stream_id", "window_start", "window_end"],
            how="left"
        )

        # Fill nulls for viewer metrics if no viewer data
        joined = joined.fillna({
            "avg_viewers": 0.0,
            "viewer_events": 0
        })

        return joined

    def detect_anomalies(self, metrics_df: DataFrame) -> DataFrame:
        """
        Detect anomalies using z-score method on chat_rate.

        Anomalies are identified when:
        z-score = (value - mean) / stddev > threshold

        Args:
            metrics_df: Combined metrics DataFrame

        Returns:
            DataFrame with anomaly flag and z-score
        """
        logger.info(f"Detecting anomalies (threshold: {self.anomaly_threshold})...")

        # Define window for z-score calculation (last 10 windows per stream)
        window_spec = (Window
                       .partitionBy("stream_id")
                       .orderBy(col("window_start"))
                       .rowsBetween(-10, 0))

        # Calculate rolling statistics
        with_stats = (metrics_df
                      .withColumn("chat_rate_mean", mean("chat_rate").over(window_spec))
                      .withColumn("chat_rate_stddev", stddev_pop("chat_rate").over(window_spec)))

        # Compute z-score and flag anomalies
        with_anomaly = (with_stats
                        .withColumn(
                            "z_score",
                            when(col("chat_rate_stddev") > 0,
                                 (col("chat_rate") - col("chat_rate_mean")) / col("chat_rate_stddev"))
                            .otherwise(0.0)
                        )
                        .withColumn(
                            "is_anomaly",
                            when(col("z_score") > self.anomaly_threshold, True)
                            .otherwise(False)
                        ))

        return with_anomaly

    def prepare_summary_output(self, metrics_df: DataFrame) -> DataFrame:
        """
        Prepare final schema for chat_summary_minute table.

        Args:
            metrics_df: Metrics with anomaly detection

        Returns:
            DataFrame ready for JDBC write
        """
        return metrics_df.select(
            col("stream_id"),
            col("window_start"),
            col("window_end"),
            col("chat_count").cast(IntegerType()),
            col("unique_chatters").cast(IntegerType()),
            col("avg_sentiment").cast(DoubleType()),
            col("positive_count").cast(IntegerType()),
            col("negative_count").cast(IntegerType()),
            col("chat_rate").cast(DoubleType()),
            col("avg_viewers").cast(DoubleType()),
            col("emote_list").alias("top_emotes"),
            col("z_score").cast(DoubleType()),
            col("is_anomaly").cast("boolean"),
            current_timestamp().alias("processed_at")
        )

    def prepare_moments_output(self, metrics_df: DataFrame) -> DataFrame:
        """
        Extract anomalous moments for moments table.

        Args:
            metrics_df: Metrics with anomaly detection

        Returns:
            DataFrame with detected moments
        """
        moments = (metrics_df
                   .filter(col("is_anomaly") == True)
                   .select(
                       col("stream_id"),
                       col("window_start").alias("timestamp"),
                       lit("chat_spike").alias("moment_type"),
                       concat_ws(", ",
                                 concat_ws(": ", lit("chat_rate"), col("chat_rate").cast("string")),
                                 concat_ws(": ", lit("z_score"), col("z_score").cast("string")),
                                 concat_ws(": ", lit("chat_count"), col("chat_count").cast("string"))
                       ).alias("description"),
                       col("chat_rate").alias("intensity"),
                       struct(
                           col("chat_count"),
                           col("unique_chatters"),
                           col("avg_viewers"),
                           col("z_score")
                       ).alias("metadata"),
                       current_timestamp().alias("detected_at")
                   ))

        # Convert metadata struct to JSON string
        moments = moments.withColumn(
            "metadata",
            to_json(col("metadata"))
        )

        return moments

    def write_to_postgres(
        self,
        df: DataFrame,
        table_name: str,
        checkpoint_suffix: str
    ):
        """
        Write streaming DataFrame to PostgreSQL using JDBC.

        Args:
            df: DataFrame to write
            table_name: Target PostgreSQL table
            checkpoint_suffix: Unique suffix for checkpoint directory
        """
        logger.info(f"Setting up write to PostgreSQL table: {table_name}")

        def write_batch(batch_df: DataFrame, batch_id: int):
            """Batch write function for foreachBatch."""
            try:
                logger.info(f"Writing batch {batch_id} to {table_name} "
                           f"({batch_df.count()} records)")

                (batch_df.write
                 .format("jdbc")
                 .option("url", self.postgres_url)
                 .option("dbtable", table_name)
                 .option("user", self.postgres_user)
                 .option("password", self.postgres_password)
                 .option("driver", "org.postgresql.Driver")
                 .mode("append")
                 .save())

                logger.info(f"Batch {batch_id} written successfully")
            except Exception as e:
                logger.error(f"Error writing batch {batch_id} to {table_name}: {e}")
                raise

        checkpoint_path = f"{self.checkpoint_location}/{checkpoint_suffix}"

        query = (df.writeStream
                 .foreachBatch(write_batch)
                 .outputMode("update")
                 .option("checkpointLocation", checkpoint_path)
                 .trigger(processingTime="10 seconds"))

        return query

    def run(self):
        """Main execution method for the streaming job."""
        logger.info("Starting Telemetra Streaming Job...")

        try:
            # Create Spark session
            spark = self.create_spark_session()

            # Read streams
            chat_stream = self.read_kafka_stream(
                spark, "telemetra.events.chat", self.get_chat_schema()
            )
            viewer_stream = self.read_kafka_stream(
                spark, "telemetra.events.viewer", self.get_viewer_schema()
            )

            # Enrich chat with sentiment
            chat_enriched = self.enrich_with_sentiment(chat_stream)

            # Compute aggregations
            chat_agg = self.aggregate_chat_metrics(chat_enriched)
            viewer_agg = self.aggregate_viewer_metrics(viewer_stream)

            # Join metrics
            combined_metrics = self.join_metrics(chat_agg, viewer_agg)

            # Detect anomalies
            metrics_with_anomalies = self.detect_anomalies(combined_metrics)

            # Prepare outputs
            summary_output = self.prepare_summary_output(metrics_with_anomalies)
            moments_output = self.prepare_moments_output(metrics_with_anomalies)

            # Start streaming queries
            logger.info("Starting streaming queries...")

            summary_query = self.write_to_postgres(
                summary_output,
                "chat_summary_minute",
                "chat_summary_checkpoint"
            )

            moments_query = self.write_to_postgres(
                moments_output,
                "moments",
                "moments_checkpoint"
            )

            summary_stream = summary_query.start()
            moments_stream = moments_query.start()

            logger.info("Streaming queries started successfully")
            logger.info("Waiting for termination...")

            # Wait for all streams to complete
            spark.streams.awaitAnyTermination()

        except Exception as e:
            logger.error(f"Fatal error in streaming job: {e}", exc_info=True)
            raise
        finally:
            logger.info("Shutting down streaming job...")


def main():
    """Entry point for the streaming job."""
    logger.info("="*60)
    logger.info("Telemetra PySpark Streaming Analytics")
    logger.info("="*60)

    job = TelemetraStreamingJob()
    job.run()


if __name__ == "__main__":
    main()
