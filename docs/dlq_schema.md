# DLQ Schema – Netflix Streaming Pipeline

This document defines the JSON structure for all failure records written to the DLQ bucket:

- Bucket: `myshr-netflix-dlq-ap-south-1`
- Base prefix: `glue-failures/`
- Typical full key pattern:

`glue-failures/pipeline=netflix-streaming/stage=processed-to-redshift/ingest_year=YYYY/ingest_month=MM/ingest_day=DD/{failure_id}.json`

---

## Top-level JSON fields

Each DLQ file is a single JSON object with the following fields:

```json
{
  "failure_id": "uuid-1234-5678-90ab-cdef12345678",
  "timestamp_utc": "2026-02-05T11:22:33.123456Z",

  "pipeline": "netflix-streaming",
  "pipeline_stage": "processed-to-redshift",
  "failure_source": "GLUE_JOB",
  "failure_category": "DQ_GUARDRAIL",

  "job_name": "netflix-processed-to-redshift",
  "job_run_id": "jr_1234567890abcdef",
  "job_run_state": "FAILED",

  "dq_failure_type": "COLUMN_COUNT_ZERO",
  "error_message": "DQ_FAILURE: ColumnCount == 0, aborting job to protect warehouse.",
  "stacktrace_snippet": null,

  "source_s3_paths": [
    "s3://myshr-netflix-datalake-ap-south-1/processed/events/"
  ],

  "step_functions": {
    "execution_arn": "arn:aws:states:ap-south-1:123456789012:execution:netflix-orchestrator-dev-ai-recovery:xyz",
    "state_machine": "netflix-orchestrator-dev-ai-recovery"
  },

  "bedrock_analysis": {
    "request": {
      "summary": "Glue job failed in Netflix pipeline",
      "high_level_reason": "States.TaskFailed",
      "dq_or_script_error": "DQ_FAILURE: ColumnCount == 0, aborting job to protect warehouse.",
      "glue_job_metadata": {
        "JobName": "netflix-processed-to-redshift",
        "JobRunId": "jr_1234567890abcdef",
        "JobRunState": "FAILED",
        "LogGroupName": "/aws-glue/jobs/output"
      },
      "suggested_next_action": "inspect_logs_and_decide_dlq_or_retry"
    },
    "response": null
  },

  "raw_event": {
    "original_payload": "full Step Functions / Glue failure event for forensics"
  }
}
