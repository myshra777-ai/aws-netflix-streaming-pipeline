from pyspark.sql import SparkSession, DataFrame


def read_csv(spark: SparkSession, path: str, header: bool = True,
             infer_schema: bool = True) -> DataFrame:
    return (
        spark.read
        .option("header", str(header).lower())
        .option("inferSchema", str(infer_schema).lower())
        .csv(path)
    )
