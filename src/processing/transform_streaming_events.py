from pyspark.sql import DataFrame, functions as F

def transform_raw_events(df: DataFrame) -> DataFrame:
    # Example minimal transform
    return (
        df
        .withColumn("event_ts", F.col("event_ts").cast("timestamp"))
        .withColumn("duration_sec", F.col("duration_sec").cast("int"))
    )
