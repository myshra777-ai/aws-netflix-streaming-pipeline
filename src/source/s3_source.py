from pyspark.sql import SparkSession, DataFrame
from config.paths import RAW_BUCKET, RAW_EVENTS_PREFIX

# Default raw S3 path for Netflix events
RAW_EVENTS_PATH = f"s3://{RAW_BUCKET}/{RAW_EVENTS_PREFIX}"


def read_json_from_s3(spark: SparkSession, path: str = RAW_EVENTS_PATH) -> DataFrame:
    """
    Read raw JSON events from S3 path.

    Default path: RAW_EVENTS_PATH from config.
    """
    return spark.read.json(path)


def read_parquet_from_s3(spark: SparkSession, path: str) -> DataFrame:
    """
    Read processed/curated parquet data from S3 path.
    """
    return spark.read.parquet(path)
