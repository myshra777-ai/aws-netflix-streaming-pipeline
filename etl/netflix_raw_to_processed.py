import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsgluedq.transforms import EvaluateDataQuality

# ---- Config / arguments ----
args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_DATABASE", "RAW_TABLE", "OUTPUT_PATH"]
)

DEFAULT_DATA_QUALITY_RULESET = """
Rules = [
    ColumnCount > 0
]
"""

# ---- Glue boilerplate ----
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)

# ---- Read from Data Catalog ----
raw_dyf = glue_context.create_dynamic_frame.from_catalog(
    database=args["RAW_DATABASE"],
    table_name=args["RAW_TABLE"],
    transformation_ctx="raw_source",
)

# ---- Data quality check (simple) ----
EvaluateDataQuality().process_rows(
    frame=raw_dyf,
    ruleset=DEFAULT_DATA_QUALITY_RULESET,
    publishing_options={
        "dataQualityEvaluationContext": "netflix_raw_events_dq",
        "enableDataQualityResultsPublishing": True,
    },
    additional_options={
        "dataQualityResultsPublishing.strategy": "BEST_EFFORT",
        "observations.scope": "ALL",
    },
)

# ---- Write to S3 as Parquet + Snappy ----
sink = glue_context.getSink(
    path=args["OUTPUT_PATH"],
    connection_type="s3",
    updateBehavior="LOG",
    partitionKeys=[],  # future: ["event_type"] etc.
    enableUpdateCatalog=False,  # catalog separately handle
    transformation_ctx="processed_sink",
)

sink.setFormat("glueparquet", compression="snappy")
sink.writeFrame(raw_dyf)

job.commit()
