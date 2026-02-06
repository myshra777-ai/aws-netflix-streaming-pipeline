import json
import uuid
from datetime import datetime, timezone

import boto3

# Reuse S3 client across invocations (Lambda best practice)
s3 = boto3.client("s3")

DLQ_BUCKET = "myshr-netflix-dlq-ap-south-1"
DLQ_PREFIX = "glue-failures"
PIPELINE_NAME = "netflix-streaming"
PIPELINE_STAGE = "processed-to-redshift"


def handler(event, context):
    """
    HandleFailure Lambda for Netflix pipeline:
    - Normalizes Glue/Step Functions failure event
    - Builds a DLQ record following docs/dlq_schema.md
    - Writes JSON to S3 DLQ bucket
    - Returns a small summary payload to Step Functions
    """

    # 1) Extract high-level error from Step Functions
    error = event.get("error", {})
    cause_str = error.get("Cause", "{}")

    try:
        parsed_cause = json.loads(cause_str)
    except Exception:
        parsed_cause = {}

    # 2) Build prompt_payload (AI-friendly summary) – same idea as before
    dq_or_script_error = parsed_cause.get("ErrorMessage", cause_str)

    glue_job_metadata = {
        "JobName": parsed_cause.get("JobName", event.get("JobName")),
        "JobRunId": parsed_cause.get("JobRunId"),
        "JobRunState": event.get("JobRunState"),
        "LogGroupName": parsed_cause.get("LogGroupName"),
    }

    prompt_payload = {
        "summary": "Glue job failed in Netflix pipeline",
        "high_level_reason": error.get("Error"),
        "dq_or_script_error": dq_or_script_error,
        "glue_job_metadata": glue_job_metadata,
        "suggested_next_action": "inspect_logs_and_decide_dlq_or_retry",
    }

    # 3) Build DLQ record according to docs/dlq_schema.md
    now = datetime.now(timezone.utc)
    failure_id = str(uuid.uuid4())

    ingest_year = now.strftime("%Y")
    ingest_month = now.strftime("%m")
    ingest_day = now.strftime("%d")

    # Try to find source S3 paths from Glue arguments, if present
    arguments = parsed_cause.get("Arguments", {})
    processed_path = arguments.get("--PROCESSED_EVENTS_PATH")
    source_s3_paths = []
    if processed_path:
        source_s3_paths.append(processed_path)

    dlq_record = {
        "failure_id": failure_id,
        "timestamp_utc": now.isoformat(),

        "pipeline": PIPELINE_NAME,
        "pipeline_stage": PIPELINE_STAGE,
        "failure_source": "GLUE_JOB",
        "failure_category": "DQ_GUARDRAIL",

        "job_name": glue_job_metadata.get("JobName"),
        "job_run_id": glue_job_metadata.get("JobRunId"),
        "job_run_state": glue_job_metadata.get("JobRunState"),

        # For now we know this Lambda is wired to DQ guardrail failure
        "dq_failure_type": "COLUMN_COUNT_ZERO",
        "error_message": dq_or_script_error,
        "stacktrace_snippet": parsed_cause.get("StackTrace"),

        "source_s3_paths": source_s3_paths,

        "step_functions": {
            "execution_arn": event.get("ExecutionArn"),
            "state_machine": event.get("StateMachineName"),
        },

        "bedrock_analysis": {
            "request": prompt_payload,
            "response": None,
        },

        # Keep original event for full forensics
        "raw_event": event,
    }

    # 4) Compute S3 key and write DLQ record
    key = (
        f"{DLQ_PREFIX}/"
        f"pipeline={PIPELINE_NAME}/"
        f"stage={PIPELINE_STAGE}/"
        f"ingest_year={ingest_year}/"
        f"ingest_month={ingest_month}/"
        f"ingest_day={ingest_day}/"
        f"{failure_id}.json"
    )

    body = json.dumps(dlq_record, default=str).encode("utf-8")

    s3.put_object(
        Bucket=DLQ_BUCKET,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    # 5) Small summary back to Step Functions
    return {
        "status": "dlq_written",
        "dlq_s3_key": key,
        "prompt_payload": prompt_payload,
    }
