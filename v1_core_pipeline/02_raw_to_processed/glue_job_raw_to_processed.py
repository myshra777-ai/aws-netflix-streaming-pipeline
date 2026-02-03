import sys
import json
import boto3

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F, Window

# ================== CONFIG (EDIT HERE) ==================

# Raw events written from Kinesis -> S3
RAW_PATH = "s3://myshr-netflix-datalake-ap-south-1/netflix/raw/"

# Processed events (Parquet, partitioned by event_type)
PROCESSED_PATH = "s3://myshr-netflix-datalake-ap-south-1/netflix/processed/"

# Dead-letter / quarantine bucket
DLQ_PATH = "s3://myshr-netflix-dlq-ap-south-1/netflix/events/"

# SNS topic for data-quality / circuit-breaker alerts
DATA_QUALITY_TOPIC_ARN = "arn:aws:sns:ap-south-1:462634386608:netflix-data-quality-alerts"

# If more than 10% of records are invalid, trip circuit breaker
INVALID_THRESHOLD = 0.10

# Allowed event types
VALID_EVENT_TYPES = ["PLAY_START", "PLAY_END", "PAUSE", "DELETE_USER"]

# ========================================================


def main():
    # Glue passes these automatically
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "JOB_RUN_ID"])

    sc = SparkContext()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    # 1) Read raw data from S3
    df = spark.read.json(RAW_PATH)

    # 2) Basic null handling / default values
    df = (
        df
        .withColumn("playback_position_sec", F.coalesce("playback_position_sec", F.lit(0)))
        .withColumn("total_duration_sec", F.coalesce("total_duration_sec", F.lit(0)))
    )

    # 3) Validation rules -> mark each row valid / invalid
    validated = df.withColumn(
        "is_valid",
        F.col("event_id").isNotNull()
        & F.col("user_id").isNotNull()
        & F.col("title_id").isNotNull()
        & F.col("event_type").isin(*VALID_EVENT_TYPES)
        & F.col("event_ts").isNotNull()
    )

    valid_df = validated.filter("is_valid").drop("is_valid")
    invalid_df = validated.filter("NOT is_valid").drop("is_valid")

    # 4) Per-run dedupe by event_id (keeps latest event_ts per id)
    w = Window.partitionBy("event_id").orderBy(F.col("event_ts").desc())
    valid_df = (
        valid_df
        .withColumn("rn", F.row_number().over(w))
        .filter("rn = 1")
        .drop("rn")
    )

    # 5) Write outputs
    #    - valid: partitioned Parquet in processed bucket
    #    - invalid: raw Parquet in DLQ bucket
    (
        valid_df
        .write
        .mode("append")
        .partitionBy("event_type")
        .parquet(PROCESSED_PATH)
    )

    (
        invalid_df
        .write
        .mode("append")
        .parquet(DLQ_PATH)
    )

    # 6) Circuit breaker metrics
    total_count = validated.count()
    invalid_count = invalid_df.count()
    invalid_ratio = (invalid_count / total_count) if total_count > 0 else 0.0

    print(f"[DQ] total={total_count}, invalid={invalid_count}, ratio={invalid_ratio}")

    # 7) If bad data too high -> push message to SNS + fail job
    if invalid_ratio > INVALID_THRESHOLD:
        sns = boto3.client("sns")

        payload = {
            "job_name": args["JOB_NAME"],
            "run_id": args["JOB_RUN_ID"],
            "invalid_ratio": invalid_ratio,
            "dlq_path": DLQ_PATH,
            "total_records": total_count,
            "invalid_records": invalid_count,
        }

        sns.publish(
            TopicArn=DATA_QUALITY_TOPIC_ARN,
            Message=json.dumps(payload),
            Subject="Netflix Glue Data Quality Circuit Breaker"
        )

        # Failing the job ensures downstream tables don't consume bad data
        raise Exception("Circuit breaker triggered: invalid_ratio above threshold")

    job.commit()


if __name__ == "__main__":
    main()
