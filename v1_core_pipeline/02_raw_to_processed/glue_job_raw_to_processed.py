import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from awsglue.data_quality import EvaluateDataQuality, DataQualityRuleset
from pyspark.sql.functions import col, from_unixtime, to_date

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# 1) Read from Glue catalog (raw_netflix_events_rootevents)
raw_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="netflix-streams-aws",
    table_name="raw_netflix_events_rootevents"
)

# 2) Convert to DataFrame for transformations
df = raw_dyf.toDF()

# 3) Core transformations (epoch -> date, type casting, etc.)
df = df.withColumn(
    "event_date",
    to_date(from_unixtime(col("event_ts")))
)

# TODO: add other casts / derived columns as needed
# e.g. df = df.withColumn("event_type", col("event_type").cast("string"))

# 4) Convert back to DynamicFrame
transformed_dyf = DynamicFrame.fromDF(df, glueContext, "transformed_dyf")

# 5) Optional: Data Quality checks (row-level outcomes collection)
# dq_ruleset = DataQualityRuleset(
#     ruleset="your_dq_ruleset_string_here"
# )
# dq_collection = EvaluateDataQuality().process(
#     glueContext,
#     frame=transformed_dyf,
#     ruleset=dq_ruleset,
#     publishing_options=None
# )
# from awsglue.dynamicframe import SelectFromCollection
# dq_results_dyf = SelectFromCollection.apply(
#     dfc=dq_collection,
#     key="rowLevelOutcomes"
# )

# 6) Write partitioned output to S3 processed layer
sink_dyf = transformed_dyf.repartition(1)  # optional

datasink = glueContext.getSink(
    path="s3://myshr-netflix-datalake-ap-south-1/netflix/processed_partitioned/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=["event_date"],
    enableUpdateCatalog=True,
    transformation_ctx="datasink"
)

datasink.setCatalogInfo(
    catalogDatabase="netflix-streams-aws",
    catalogTableName="processed_netflix_events"
)
datasink.setFormat("glueparquet", compression="snappy")
datasink.writeFrame(sink_dyf)

job.commit()
