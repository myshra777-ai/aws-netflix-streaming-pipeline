# 01_dq_alerts_bedrock – Data Quality Alerts with Bedrock

## Goal

Use Amazon Bedrock to turn raw data quality results into human-friendly alerts and summaries, so issues are easy to understand and act on.

## High-level flow

1. v1 core pipeline runs the raw → processed ETL.
2. A Data Quality (DQ) job evaluates the processed data and produces metrics/results.
3. When the DQ job finishes, it publishes an event (via EventBridge or SNS).
4. Lambda `lambdas/netflix_bedrock_dq_handler.py` is triggered with the DQ result payload.
5. Lambda calls Bedrock to:
   - Summarize the main data quality issues.
   - Highlight impacted tables/partitions.
   - Optionally suggest next actions or severity.
6. Lambda sends the summary to notification channels (SNS email / Slack webhook).

## Key components

- Lambda:
  - File: `lambdas/netflix_bedrock_dq_handler.py`
  - Input: DQ result event (JSON with metrics, rule outcomes, partition info).
  - Output: AI-generated summary message sent to downstream channels.

- Triggers (planned):
  - EventBridge rule listening for Glue DQ job completion.
  - Or SNS topic where the DQ job publishes its result.

- Notification targets (planned):
  - SNS topic with email subscribers.
  - Slack or Teams via webhook.

## Future ideas

- Include DLQ statistics in the Bedrock summary (bad record counts, top error reasons).
- Add severity levels (INFO / WARN / CRITICAL) based on DQ scores.
- Track repeated failures over time and flag “chronic” data quality issues.
