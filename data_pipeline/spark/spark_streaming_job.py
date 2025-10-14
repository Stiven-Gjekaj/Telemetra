#!/usr/bin/env python3
"""
Spark Structured Streaming Job for Telemetra
Reads from Kafka, performs windowed aggregations, detects anomalies, writes to Postgres
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, count, countDistinct, avg, sum as sql_sum,
    current_timestamp, lit, stddev, mean, when, abs as sql_abs, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    FloatType, TimestampType, BooleanType
)
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_spark_session():
    """Create Spark session with Kafka and Postgres dependencies"""
    return SparkSession.builder \
        .appName("Telemetra Streaming") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()


def get_postgres_properties():
    """Get Postgres connection properties"""
    return {
        "user": os.getenv("POSTGRES_USER", "telemetra_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "telemetra_pass"),
        "driver": "org.postgresql.Driver"
    }


def process_chat_stream(spark: SparkSession, kafka_bootstrap_servers: str, postgres_url: str):
    """Process chat stream with windowed aggregations"""

    # Define chat schema
    chat_schema = StructType([
        StructField("stream_id", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("username", StringType(), True),
        StructField("message", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("message_length", IntegerType(), True),
        StructField("has_emote", BooleanType(), True),
        StructField("user_type", StringType(), True)
    ])

    # Read from Kafka
    chat_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "chat") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON and extract timestamp
    parsed_chat = chat_df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), chat_schema).alias("data")) \
        .select("data.*")

    # Windowed aggregation (1-minute windows with 30-second watermark)
    chat_aggregated = parsed_chat \
        .withWatermark("timestamp", "30 seconds") \
        .groupBy(
            col("stream_id"),
            window(col("timestamp"), "1 minute")
        ) \
        .agg(
            count("*").alias("message_count"),
            countDistinct("username").alias("unique_chatters"),
            avg("message_length").alias("avg_message_length")
        ) \
        .select(
            col("stream_id"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("message_count"),
            col("unique_chatters"),
            col("avg_message_length")
        )

    # Write to Postgres
    def write_chat_to_postgres(batch_df, batch_id):
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=postgres_url,
                    table="chat_summary_minute",
                    mode="append",
                    properties=get_postgres_properties()
                )
            logger.info(f"Batch {batch_id}: Wrote {batch_df.count()} chat aggregations to Postgres")

    query = chat_aggregated \
        .writeStream \
        .foreachBatch(write_chat_to_postgres) \
        .outputMode("append") \
        .start()

    return query


def process_viewer_stream(spark: SparkSession, kafka_bootstrap_servers: str, postgres_url: str):
    """Process viewer count stream"""

    viewer_schema = StructType([
        StructField("stream_id", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("viewer_count", IntegerType(), True),
        StructField("timestamp", TimestampType(), True)
    ])

    # Read from Kafka
    viewer_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "viewer") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON
    parsed_viewer = viewer_df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), viewer_schema).alias("data")) \
        .select("data.*")

    # Write to Postgres
    def write_viewer_to_postgres(batch_df, batch_id):
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=postgres_url,
                    table="viewer_timeseries",
                    mode="append",
                    properties=get_postgres_properties()
                )
            logger.info(f"Batch {batch_id}: Wrote {batch_df.count()} viewer records to Postgres")

    query = parsed_viewer \
        .writeStream \
        .foreachBatch(write_viewer_to_postgres) \
        .outputMode("append") \
        .start()

    return query


def process_transaction_stream(spark: SparkSession, kafka_bootstrap_servers: str, postgres_url: str):
    """Process transaction stream"""

    transaction_schema = StructType([
        StructField("stream_id", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("transaction_type", StringType(), True),
        StructField("amount", FloatType(), True),
        StructField("username", StringType(), True),
        StructField("timestamp", TimestampType(), True)
    ])

    # Read from Kafka
    transaction_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "transactions") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON
    parsed_transaction = transaction_df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), transaction_schema).alias("data")) \
        .select("data.*")

    # Write to Postgres
    def write_transaction_to_postgres(batch_df, batch_id):
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=postgres_url,
                    table="transactions",
                    mode="append",
                    properties=get_postgres_properties()
                )
            logger.info(f"Batch {batch_id}: Wrote {batch_df.count()} transactions to Postgres")

    query = parsed_transaction \
        .writeStream \
        .foreachBatch(write_transaction_to_postgres) \
        .outputMode("append") \
        .start()

    return query


def process_anomaly_detection(spark: SparkSession, kafka_bootstrap_servers: str, postgres_url: str):
    """Detect anomalies in chat rate using z-score"""

    chat_schema = StructType([
        StructField("stream_id", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("username", StringType(), True),
        StructField("message", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("message_length", IntegerType(), True),
        StructField("has_emote", BooleanType(), True),
        StructField("user_type", StringType(), True)
    ])

    # Read from Kafka
    chat_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "chat") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON
    parsed_chat = chat_df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), chat_schema).alias("data")) \
        .select("data.*")

    # Compute rolling statistics (10-minute window)
    chat_rate = parsed_chat \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            col("stream_id"),
            window(col("timestamp"), "1 minute", "30 seconds")
        ) \
        .agg(
            count("*").alias("message_count")
        ) \
        .select(
            col("stream_id"),
            col("window.start").alias("window_start"),
            col("message_count")
        )

    # Calculate z-score over last 10 windows
    from pyspark.sql.window import Window

    window_spec = Window.partitionBy("stream_id").orderBy("window_start").rowsBetween(-10, 0)

    anomalies = chat_rate \
        .withColumn("avg_rate", avg("message_count").over(window_spec)) \
        .withColumn("stddev_rate", stddev("message_count").over(window_spec)) \
        .withColumn(
            "z_score",
            when(col("stddev_rate") > 0,
                 (col("message_count") - col("avg_rate")) / col("stddev_rate")
            ).otherwise(0.0)
        ) \
        .filter(sql_abs(col("z_score")) > 2.5) \
        .select(
            col("stream_id"),
            lit("anomaly").alias("moment_type"),
            col("window_start").alias("timestamp"),
            lit("chat_rate").alias("metric_name"),
            col("message_count").cast(FloatType()).alias("metric_value"),
            col("z_score"),
            expr("CONCAT('Chat rate anomaly detected: ', message_count, ' messages (z-score: ', ROUND(z_score, 2), ')')").alias("description")
        )

    # Write anomalies to Postgres
    def write_anomalies_to_postgres(batch_df, batch_id):
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=postgres_url,
                    table="moments",
                    mode="append",
                    properties=get_postgres_properties()
                )
            logger.info(f"Batch {batch_id}: Detected and wrote {batch_df.count()} anomalies to Postgres")

    query = anomalies \
        .writeStream \
        .foreachBatch(write_anomalies_to_postgres) \
        .outputMode("append") \
        .start()

    return query


def main():
    """Main entry point"""
    logger.info("Starting Telemetra Spark Streaming Job...")

    # Configuration
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_db = os.getenv("POSTGRES_DB", "telemetra")
    postgres_url = f"jdbc:postgresql://{postgres_host}:5432/{postgres_db}"

    logger.info(f"Kafka: {kafka_bootstrap_servers}")
    logger.info(f"Postgres: {postgres_url}")

    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # Start all streaming queries
    queries = []

    logger.info("Starting chat stream processing...")
    queries.append(process_chat_stream(spark, kafka_bootstrap_servers, postgres_url))

    logger.info("Starting viewer stream processing...")
    queries.append(process_viewer_stream(spark, kafka_bootstrap_servers, postgres_url))

    logger.info("Starting transaction stream processing...")
    queries.append(process_transaction_stream(spark, kafka_bootstrap_servers, postgres_url))

    logger.info("Starting anomaly detection...")
    queries.append(process_anomaly_detection(spark, kafka_bootstrap_servers, postgres_url))

    logger.info("All streaming queries started successfully")

    # Wait for all queries to terminate
    for query in queries:
        query.awaitTermination()


if __name__ == "__main__":
    main()
