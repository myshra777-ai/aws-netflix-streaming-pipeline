import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame

import pyspark.sql.functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

RAW_DB = "netflix-streams-aws"
RAW_TABLE = "raw_netflix_raw_events"

PROCESSED_S3_PATH = "s3://myshr-netflix-datalake-ap-south-1/netflix/processed/events/"

# 1) Read raw events from Glue Catalog
raw_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=RAW_DB,
    table_name=RAW_TABLE,
    transformation_ctx="raw_dyf",
)

raw_df = raw_dyf.toDF()

# 2) Basic transformations / enrichment
# - derive event_date from event_timestamp (or ingestion date fallback)
# - derive is_completed flag
# - normalize device_type

# If event_timestamp is string, cast to timestamp; adjust column name if needed
if "event_timestamp" in raw_df.columns:
    ts_col = "event_timestamp"
else:
    # fallback if your column is named differently
    ts_col = "event_time"

df_tr = raw_df

# Cast timestamp if needed
df_tr = df_tr.withColumn(
    "event_ts",
    F.to_timestamp(F.col(ts_col))
)

# Event date (for partitioning)
df_tr = df_tr.withColumn(
    "event_date",
    F.to_date(F.col("event_ts"))
)

# is_completed flag
df_tr = df_tr.withColumn(
    "is_completed",
    F.when(F.col("event_type") == F.lit("complete"), F.lit(1)).otherwise(F.lit(0))
)

# Normalize device_type (example: lowercase + trim)
if "device_type" in df_tr.columns:
    df_tr = df_tr.withColumn(
        "device_type_norm",
        F.trim(F.lower(F.col("device_type")))
    )
else:
    df_tr = df_tr.withColumn("device_type_norm", F.lit(None).cast("string"))

# (Optional) Simple aggregation per user/title/date
# Comment out if you prefer row-level data only
agg_df = (
    df_tr.groupBy(
        "event_date",
        "user_id",
        "title_id",
    )
    .agg(
        F.count("*").alias("event_count"),
        F.sum("is_completed").alias("complete_events"),
        F.max("event_ts").alias("last_event_ts"),
        F.max("device_type_norm").alias("last_device_type_norm"),
    )
)

# 3) Write processed data back to S3 as partitioned Parquet
processed_dyf = DynamicFrame.fromDF(agg_df, glueContext, "processed_dyf")

sink = glueContext.getSink(
    path=PROCESSED_S3_PATH,
    connection_type="s3",
    updateBehavior="LOG",
    partitionKeys=["event_date"],
    enableUpdateCatalog=True,
    transformation_ctx="processed_sink",
)

sink.setCatalogInfo(
    catalogDatabase=RAW_DB,
    catalogTableName="processed_netflix_events",
)

sink.setFormat("glueparquet", compression="snappy")

sink.writeFrame(processed_dyf)

job.commit()
