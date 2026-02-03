# 01_dq_alerts_bedrock – Data Quality Alerts with Bedrock

## Goal

Use AI (Amazon Bedrock) to turn raw data quality results into human-friendly alerts and summaries.

## High-level flow

1. v1 pipeline runs the core ETL (raw -> processed).
2. A Data Quality (DQ) job evaluates the processed data and produces metrics/results.
3. An event is published when the DQ job finishes (EventBridge / SNS).
4. Lambda `lambdas/netflix_bedrock_dq_handler.py` is triggered with the DQ result payload.
5. Lambda calls Bedrock to:
   - Summarize the key data quality issues.
   - Highlight impacted tables/partitions.
   - Optionally suggest next actions.
6. Lambda sends the summary to notification channels (SNS / email / Slack).

## Key components

- Lambda:
  - File: `lambdas/netflix_bedrock_dq_handler.py`
  - Input: DQ result event (JSON).
  - Output: AI-generated summary message sent to downstream channels.

- Triggers (planned):
  - EventBridge rule listening for Glue DQ job completion.
  - Or SNS topic where DQ job publishes results.

- Notification targets (planned):
  - SNS email subscription.
  - Or Slack webhook for data engineering alerts.

## Future ideas

- Include DLQ statistics in the Bedrock summary (count of bad records, top error reasons).
- Add severity levels (INFO/WARN/CRITICAL) based on DQ scores.
- Correlate repeated failures over time and flag “chronic” data quality issues.
