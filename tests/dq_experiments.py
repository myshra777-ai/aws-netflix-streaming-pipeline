import sys
from awsglue.transforms import EvaluateDataQuality
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# -------------------------------
# Job setup
# -------------------------------
args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# -------------------------------
# Create tiny DataFrame in code
# -------------------------------
data = [
    ("user_001", "movie_1001"),
    ("user_002", "show_2001_s1e1"),
]
columns = ["user_id", "title_id"]
df = spark.createDataFrame(data, columns)

dyf = DynamicFrame.fromDF(df, glueContext, "from_local")

# -------------------------------
# Data Quality on processed data
# -------------------------------
dq_ruleset = """
Rules = [
  IsComplete "user_id",
  IsComplete "title_id",
  IsNotNull "user_id",
  IsNotNull "title_id"
]
"""

dq_results_dyf = EvaluateDataQuality.apply(
    frame=dyf,
    ruleset=dq_ruleset,
    publishing_options={           # <-- snake_case correct name
        "dataQualityEvaluationContext": "netflix_processed_events",
        "enableDataQualityMetrics": True,
        "enableDataQualityResultsPublishing": True,
        "resultsS3Prefix": "s3://myshr-netflix-datalake-ap-south-1/netflix/dq_results/events/"
    },
    additional_options={           # optional; can remove if issues
        "performanceTuning.caching": "CACHE_INPUT"
    },
)

dq_results_df = dq_results_dyf.toDF()
dq_results_df.show(truncate=False)

failed_rules = dq_results_df.filter("evaluation_passed = false").count()
if failed_rules > 0:
    # Uncomment to hard‑fail on DQ
    # raise Exception(f"Data Quality failed for {failed_rules} rule(s). Aborting Glue job.")
    pass

# -------------------------------
# Write to processed S3
# -------------------------------
processed_path = "s3://myshr-netflix-datalake-ap-south-1/netflix/processed/events/"

glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={
        "path": processed_path,
    },
    format="parquet",
    format_options={"compression": "snappy"},
    transformation_ctx="processed_events",
)

job.commit()
