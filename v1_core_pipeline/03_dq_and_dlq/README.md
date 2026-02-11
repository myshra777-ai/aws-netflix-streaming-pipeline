# 03_dq_and_dlq – Data Quality & DLQ

Goal:
- Run data quality checks on processed data.
- Route failed / bad records into a DLQ S3 prefix.

DLQ behavior (current reality):
- Right now, almost all data is already clean, so DLQ is expected to be mostly empty.
- In future, we will generate controlled bad data (Faker) to validate DLQ behavior.

Planned rules (examples):
- Drop to DLQ if `profile_id` is null.
- Drop to DLQ if `event_timestamp` cannot be parsed.
- Drop to DLQ if `title_id` is missing.

Planned DLQ path:
- `s3://<bucket>/netflix/dlq/`

Testing idea:
- Use a Faker-based producer to generate ~100 events/sec with 10–20% intentionally bad records.
- Run DQ/DLQ job and verify that only bad records land in DLQ.
