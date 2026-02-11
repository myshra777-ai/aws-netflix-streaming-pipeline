from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import DataFrame

def get_kinesis_stream_df(glue_context: GlueContext, stream_arn: str) -> DataFrame:
    # TODO: fill correct options later
    return glue_context \
        .create_data_frame_from_options(
            connection_type="kinesis",
            connection_options={
                "streamARN": stream_arn,
                "startingPosition": "TRIM_HORIZON"
            },
            format="json"
        )
