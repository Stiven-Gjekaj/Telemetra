"""
Spark Structured Streaming Job for Telemetra

Consumes Twitch data from Kafka topics, performs windowed aggregations,
and writes results to PostgreSQL for the analytics dashboard.
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, count, countDistinct,
    to_timestamp, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    BooleanType, TimestampType, IntegerType
)


# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
CHAT_TOPIC = os.getenv("CHAT_TOPIC", "twitch-chat")
VIEWER_TOPIC = os.getenv("VIEWER_TOPIC", "twitch-viewers")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "telemetra")
POSTGRES_USER = os.getenv("POSTGRES_USER", "telemetra_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "telemetra_pass")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints")


# Define schemas for Kafka messages
chat_schema = StructType([
    StructField("stream_id", StringType(), False),
    StructField("user", StringType(), False),
    StructField("message", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("is_subscription", BooleanType(), False),
    StructField("is_moderator", BooleanType(), False)
])

viewer_schema = StructType([
    StructField("stream_id", StringType(), False),
    StructField("viewer_count", IntegerType(), False),
    StructField("timestamp", StringType(), False)
])


def create_spark_session():
    """Create and configure Spark session with Kafka and JDBC support."""
    return SparkSession.builder \
        .appName("Telemetra-Streaming") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.7.1") \
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR) \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()


def read_kafka_stream(spark, topic, schema):
    """Read and parse Kafka stream for a given topic."""
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    # Parse JSON value and extract fields
    parsed_df = df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp")))

    return parsed_df


def aggregate_chat_metrics(chat_df):
    """Aggregate chat messages into 1-minute windows."""
    aggregated = chat_df \
        .withWatermark("timestamp", "2 minutes") \
        .groupBy(
            col("stream_id"),
            window(col("timestamp"), "1 minute")
        ) \
        .agg(
            count("*").alias("message_count"),
            countDistinct("user").alias("unique_chatters")
        ) \
        .select(
            col("stream_id"),
            col("window.start").alias("window_start"),
            col("message_count"),
            col("unique_chatters")
        )

    return aggregated


def write_to_postgres(df, table_name, checkpoint_suffix):
    """Write streaming DataFrame to PostgreSQL."""
    jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    def foreach_batch_function(batch_df, batch_id):
        """Write each micro-batch to Postgres."""
        if not batch_df.isEmpty():
            batch_df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", table_name) \
                .option("user", POSTGRES_USER) \
                .option("password", POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()

            print(f"✓ Batch {batch_id} written to {table_name}: {batch_df.count()} rows")

    query = df.writeStream \
        .foreachBatch(foreach_batch_function) \
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/{checkpoint_suffix}") \
        .outputMode("append") \
        .start()

    return query


def main():
    """Main streaming job execution."""
    print("=" * 70)
    print("Telemetra Spark Structured Streaming Job")
    print("=" * 70)
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Chat Topic: {CHAT_TOPIC}")
    print(f"Viewer Topic: {VIEWER_TOPIC}")
    print(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"Checkpoint Directory: {CHECKPOINT_DIR}")
    print("=" * 70)

    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("\n✓ Spark session created")

    # Read chat stream
    print(f"📖 Reading chat stream from topic: {CHAT_TOPIC}")
    chat_stream = read_kafka_stream(spark, CHAT_TOPIC, chat_schema)

    # Aggregate chat metrics
    print("🔄 Configuring chat aggregation (1-minute windows)")
    chat_metrics = aggregate_chat_metrics(chat_stream)

    # Write chat metrics to Postgres
    print("💾 Starting chat metrics writer to PostgreSQL")
    chat_query = write_to_postgres(
        chat_metrics,
        "chat_metrics",
        "chat-checkpoint"
    )

    # Read viewer stream
    print(f"📖 Reading viewer stream from topic: {VIEWER_TOPIC}")
    viewer_stream = read_kafka_stream(spark, VIEWER_TOPIC, viewer_schema)

    # Prepare viewer metrics (no aggregation needed)
    viewer_metrics = viewer_stream.select(
        col("stream_id"),
        col("timestamp"),
        col("viewer_count")
    )

    # Write viewer metrics to Postgres
    print("💾 Starting viewer metrics writer to PostgreSQL")
    viewer_query = write_to_postgres(
        viewer_metrics,
        "viewer_metrics",
        "viewer-checkpoint"
    )

    print("\n🚀 Streaming job started successfully!")
    print("📊 Processing data from Kafka → PostgreSQL")
    print("Press Ctrl+C to stop...\n")

    # Wait for termination
    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping streaming job...")
        chat_query.stop()
        viewer_query.stop()
        spark.stop()
        print("✓ Streaming job stopped cleanly")


if __name__ == "__main__":
    main()
