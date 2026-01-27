# Streaming / Kinesis
KINESIS_STREAM_NAME = "dev-netflix-events-stream"
KINESIS_STREAM_ARN = "arn:aws:kinesis:ap-south-1:462634386608:stream/dev-netflix-events-stream"
KINESIS_REGION = "ap-south-1"

# Glue Data Catalog
GLUE_DATABASE_NAME = "netflix-streams-aws"
GLUE_RAW_TABLE = "netflix-streaming-aws-table"
GLUE_PROCESSED_TABLE = "processed_events"        # future use
GLUE_CURATED_TABLE = "curated_daily_metrics"    # future use

# Redshift (baad me fill karna)
REDSHIFT_WORKGROUP_NAME = "<FILL_ME_LATER>"
REDSHIFT_DATABASE = "netflix_warehouse"
REDSHIFT_IAM_ROLE_ARN = "<FILL_ME_LATER>"
