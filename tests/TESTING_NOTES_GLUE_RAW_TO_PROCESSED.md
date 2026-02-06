`TESTING_NOTES_GLUE_RAW_TO_PROCESSED.md`:

***

## Overview

- Glue job: `netflix-raw-to-processed-v2`  
- Bucket: `s3://myshr-netflix-datalake-ap-south-1/`  
- Layers inside the same bucket: `netflix/raw/` and `netflix/processed/`.  
- Total attempts in this debugging session: ~14 failed runs, then 1 minimal success baseline, plus follow‑up tests.

***

## Error log timeline

### 1. Data Quality `.process` attribute error

- Error:  
  `INVALID_ARGUMENT_ERROR; AttributeError: 'EvaluateDataQuality' object has no attribute 'process'`  
- Context: In a Glue 5.0 job, I tried to call `EvaluateDataQuality().process(...)`.  
- Root cause:  
  The Glue 5.0 Data Quality API uses the `apply` method instead of `process`. [docs.aws.amazon](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-data-quality-api.html)
- Fix:

  ```python
  dq_results = EvaluateDataQuality.apply(
      frame=processed_dyf,
      ruleset=dq_ruleset,
      ...
  )
  ```

***

### 2. Invalid caching option in Data Quality

- Error:  
  `UNCLASSIFIED_ERROR; Caching option AUTO is not valid. Valid values: CachingOptions.ValueSet(CACHE_NOTHING, CACHE_INPUT)`  
- Context: I passed `additional_options={"performanceTuning.caching": "AUTO"}` into the DQ call.  
- Root cause:  
  AWS Glue Data Quality only accepts `"CACHE_NOTHING"` or `"CACHE_INPUT"` for this option; `"AUTO"` is not valid. [docs.aws.amazon](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-data-quality-api.html)
- Fix:

  ```python
  additional_options={"performanceTuning.caching": "CACHE_INPUT"}
  ```

***

### 3. CloudWatch permission missing (DQ metrics)

- Error:  
  `UNCLASSIFIED_ERROR; ... is not authorized to perform: cloudwatch:PutMetricData ... Status Code: 403`  
- Context: The DQ call was configured with `enableDataQualityCloudWatchMetrics=True`.  
- Root cause:  
  The Glue service role `netflix-streaming-AWSglue` did not have `cloudwatch:PutMetricData` permissions to publish Data Quality metrics. [docs.aws.amazon](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/permissions-reference-cw.html)
- Fix options:  
  - Short term: Commented out the DQ block so the job could run without emitting CloudWatch metrics.  
  - Long term: Added the following policy statement to the Glue role:

    ```json
    {
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
      "Resource": "*",
      "Condition": {
        "StringEquals": { "cloudwatch:namespace": "GlueDataQuality" }
      }
    }
    ```

***

### 4. Data Quality result handling – `.get` on DynamicFrame

- Error:  
  `INVALID_ARGUMENT_ERROR; AttributeError: 'DynamicFrame' object has no attribute 'get'`  
- Context:

  ```python
  dq_result = EvaluateDataQuality.apply(...)
  dq_df = dq_result.get("dataQualityResults").toDF()
  ```

- Root cause:  
  In Glue 5.0, `EvaluateDataQuality.apply` returns a DynamicFrame directly, which does not expose `.get()`.  
- Fix:

  ```python
  dq_results = EvaluateDataQuality.apply(...)
  dq_df = dq_results.toDF()
  ```

***

### 5. Empty schema / Parquet write failure

- Error:  
  `QUERY_ERROR; AnalysisException: Datasource does not support writing empty or nested empty schemas.`  
- Context: After reading JSON, the job attempted to write to Parquet, but Spark failed to infer a valid schema.  
- Root cause:  
  Schema inference on the JSON either failed or produced an empty result, which led to an empty DataFrame schema that Parquet cannot write. [stackoverflow](https://stackoverflow.com/questions/48590936/aws-glue-error-path-does-not-exist)
- Fix:  
  - Defined an explicit schema and enforced it at read time:

    ```python
    schema = StructType([
        StructField("user_id", StringType(), True),
        ...
        StructField("total_duration_sec", IntegerType(), True),
    ])
    raw_df = spark.read.schema(schema).json(raw_file_path)
    ```

  - Verified the NDJSON content so that each line was a valid JSON object matching this schema.

***

### 6. `PATH_NOT_FOUND` for raw JSON (read path)

- Error:  
  `RESOURCE_NOT_FOUND_ERROR; PATH_NOT_FOUND; Path does not exist: s3://.../netflix/raw/events/.../test-events-2026-01-27-08.json`  
- Context: `spark.read.json(raw_file_path)` or DynamicFrame read failed even though the file appeared in the S3 console.  
- Root cause (combination):  
  - The file had been renamed or moved in S3, but the script still referenced the old path.  
  - In some attempts, string concatenation or hidden characters could also have caused subtle path mismatches. [stackoverflow](https://stackoverflow.com/questions/48590936/aws-glue-error-path-does-not-exist)
- Final fix:  
  - Copied the exact S3 URI from the console (“Copy S3 URI”) and used it as a literal:

    ```python
    raw_file_path = "s3://myshr-netflix-datalake-ap-south-1/netflix/raw/test-temp/backup-test-event.json"
    ```

  - Confirmed the file existed under the correct prefix and planned to later move to a directory‑based read (`raw_path` + `recurse=True`) for the full pipeline.

***

### 7. S3 `PutObject` `AccessDenied` on processed path

- Error:

  ```text
  PERMISSION_ERROR; ... is not authorized to perform: s3:PutObject on resource:
  arn:aws:s3:::myshr-netflix-datalake-ap-south-1/netflix/processed/events/part-...
  Error Code: AccessDenied; Status Code: 403
  ```

- Context: Even a minimal in‑memory DataFrame write to the processed Parquet path failed.  
- Root cause:  
  The `netflix-streaming-AWSglue` role did not have `s3:PutObject` permissions on `myshr-netflix-datalake-ap-south-1/netflix/*`. [stackoverflow](https://stackoverflow.com/questions/68446295/aws-an-error-occurred-accessdenied-when-calling-the-putmetricdata-operation/68446436)
- Fix:  
  Added (and later slightly broadened) an inline S3 policy for the Glue role:

  ```json
  {
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ],
    "Resource": "arn:aws:s3:::myshr-netflix-datalake-ap-south-1/netflix/*"
  }
  ```

  and also allowed `s3:ListBucket` on the bucket ARN for listing operations.

***

### 8. Minimal in‑memory Glue job success

- Script (final working baseline):

  ```python
  data = [("user_001", "movie_1001"), ("user_002", "show_2001_s1e1")]
  df = spark.createDataFrame(data, ["user_id", "title_id"])
  dyf = DynamicFrame.fromDF(df, glueContext, "from_local")

  processed_path = "s3://myshr-netflix-datalake-ap-south-1/netflix/processed/events/"

  glueContext.write_dynamic_frame.from_options(
      frame=dyf,
      connection_type="s3",
      connection_options={"path": processed_path},
      format="parquet",
      format_options={"compression": "snappy"},
      transformation_ctx="processed_events",
  )
  ```

- Result:  
  - Job status: `SUCCEEDED`.  
  - S3 path populated with Parquet files under `netflix/processed/events/` (multiple `part-0000*-*.snappy.parquet` objects visible in the console).  
- Meaning:  
  - IAM, Glue job configuration, and the S3 write path are now confirmed as a good baseline for the rest of the pipeline.

***

## Attempts summary

Approximate breakdown for this debugging session:

- Data Quality API / caching / result handling errors: ~4–5 runs.  
- CloudWatch permission 403 (`PutMetricData`): ~2 runs.  
- Empty schema / Parquet write failure: ~1–2 runs.  
- `PATH_NOT_FOUND` on JSON file: multiple runs while files were being moved/renamed.  
- S3 `PutObject` `AccessDenied` on processed path: ~2–3 runs.  
- Minimal in‑memory job: 1 final **successful** run.

Total failed runs: ~14.  
First clearly successful run: minimal job writing Parquet to `netflix/processed/events/` using in‑memory data.

***

## How this appears in the repo

You can drop this into a file like:

- `docs/TESTING_NOTES_GLUE_RAW_TO_PROCESSED.md`  

And link it from `README.md` under a “Testing & Troubleshooting” section, e.g.:

> For a detailed breakdown of Glue 5.0, IAM, and DQ failures during development, see `docs/TESTING_NOTES_GLUE_RAW_TO_PROCESSED.md`.

