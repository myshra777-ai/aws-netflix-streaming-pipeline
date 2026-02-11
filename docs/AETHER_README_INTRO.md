1. Project overview
Name: Aether – Fail‑Safe Streaming Data Platform on AWS

Goal: Netflix‑style event pipeline jisme raw stream se lekar warehouse tak data jaye, but bad data hamesha DLQ / quarantine me रहे, warehouse sirf human‑approved clean data le.

Core principles:

Fail‑closed for quality (bad ya doubtful data → DLQ; warehouse me nahi).

Small, replayable batches (100k shard limit).

Strong audit trail + user accountability (manual approval with IAM log).

2. Current AWS resources (Phase‑0 / Happy Path)
2.1 S3 bucket layout
Bucket: myshr-netflix-datalake-ap-south-1

text
s3://myshr-netflix-datalake-ap-south-1/aether/
│
├── raw/
│   ├── happy_path/          # sample JSON events for tests
│   ├── edge_null_ids/       # future test data
│   ├── edge_bad_event_type/
│   ├── edge_huge_payload/
│   └── edge_late_events/
│
├── processed/
│   └── events/              # Glue job 1 output (Parquet, Snappy)
│
└── warehouse/
    └── netflix_events/      # Glue job 2 output (curated Parquet)
Example processed file:
s3://.../aether/processed/events/run-...-snappy.parquet
Example warehouse file:
s3://.../aether/warehouse/netflix_events/run-...-snappy.parquet

2.2 Glue jobs (happy path)
Job 1 – Raw → Processed (events)

Source: s3://.../aether/raw/happy_path/ (JSON, multiline=false).

DQ: default ruleset ColumnCount > 0 (Glue Data Quality).​

Output: Parquet (Snappy) to s3://.../aether/processed/events/.

Purpose: basic schema enforcement + file‑format upgrade.

Job 2 – Processed → Warehouse (netflix_events)

Source: s3://.../aether/processed/events/ (Parquet).

DQ: same minimal guard now; future: stronger rules.

Output: Parquet (Snappy) to s3://.../aether/warehouse/netflix_events/.

Purpose: curated, query‑ready layer.

2.3 Athena
Database: netflix_analytics (to be created).

Table (planned):

sql
CREATE EXTERNAL TABLE netflix_analytics.netflix_events (
  event_id      string,
  user_id       string,
  title_id      string,
  event_type    string,
  watch_seconds int,
  event_ts      timestamp
)
STORED AS PARQUET
LOCATION 's3://myshr-netflix-datalake-ap-south-1/aether/warehouse/netflix_events/';
3. Big‑picture architecture (Aether final model)
Text diagram (final version):

text
[Producer Services]
      │  (events)
      ▼
[Streaming Layer: Kinesis / Kafka]
      │  (near real-time)
      ▼
────────────────────────────────────────
          LANDING & METADATA
────────────────────────────────────────
[Raw S3 Bucket: s3://.../aether/raw/stream/]
      │  (stream → S3 sink; append-only)
      ▼
[Lambda A: Batch Registration]
      ├─► DynamoDB[BatchMetadata]
      │       - batch_id
      │       - stream_name, shard_id
      │       - s3_prefix_raw
      │       - expected_record_count
      │       - initial_schema_hash
      │       - status = "REGISTERED"
      ▼
[Step Functions: Batch Orchestrator]
      ├─ wait ~2 minutes (S3 settle)
      ▼
────────────────────────────────────────
         VALIDATION & DLQ LAYER
────────────────────────────────────────
[Lambda B: S3 Count & Schema Check]
      │  - recount records
      │  - infer schema / Glue DQ
      │  - write actual_count, actual_schema_hash
      ├─ if mismatch
      │      ├─► DLQ S3 (batch-level): s3://.../aether/dlq/batch-level/
      │      └─► DynamoDB: status = "FAILED_DLQ"
      └─ else
             └─► DynamoDB: status = "VALIDATED"
────────────────────────────────────────
          PROCESSING (SHARD JOBS)
────────────────────────────────────────
[Glue Job: Raw → Analytics (100k-record shard)]
      │  - input: batch_id + s3_prefix_raw
      │  - strict schema + row-level DQ
      │  - bad rows → DLQ S3 (row-level): s3://.../aether/dlq/row-level/
      │  - good rows → Analytics: s3://.../aether/analytics/events/
      └─► DynamoDB: status = "PROCESSED_ANALYTICS"
────────────────────────────────────────
        MANUAL APPROVAL → WAREHOUSE
────────────────────────────────────────
[User Console / CLI]
      │  - show batch metadata, DQ stats, DLQ summaries
      │  - prompt: "I have manually verified analytics data for this period"
      └─► on "Approve"
             ├─► Audit Log (S3/DynamoDB)
             │      - approval_id, user_iam_arn, batch_ids, approved_at
             ▼
[Glue Job: Analytics → Warehouse]
      │  - input: approved_batch_ids only
      └─► Warehouse: s3://.../aether/warehouse/netflix_events/
             + DynamoDB: status = "WAREHOUSED"
4. IAM philosophy (lab vs client)
Lab (current):

Glue execution role can have broad s3:* on this bucket + glue:* in account to avoid wasting time on IAM debugging.

Design for clients:

Role per pipeline (e.g. AetherDataPipelineRole) with least‑privilege:

S3 access only to specific prefixes (aether/raw/*, aether/analytics/*, etc.).

Glue rights limited to specific jobs, databases, tables.

All user actions use user‑provided IAM role ARN so audit trail is clear.

5. Data‑quality & DLQ strategy
Goal: external claim 90%+ clean warehouse data, internal target ~99.9%; DLQ me kuch good data jaana acceptable, lekin bad data warehouse tak kabhi nahi.

Types of checks:

Schema drift (column names/types vs contract).

Mandatory fields (user_id, title_id, event_type, etc.).

Range and enum checks (watch_seconds >= 0, allowed event types).

Volume sanity (record count vs metadata).

DLQ layers:

Batch‑level DLQ (whole batch broken → send aside, main pipeline continues).

Row‑level DLQ (individual bad rows from otherwise good batch).

6. What’s already done vs planned
Done (Phase‑0 / Happy Path)
S3 lake structure (raw/, processed/, warehouse/ + edge folders).

Sample JSON events uploaded to raw/happy_path/.

Glue job 1 (JSON → Parquet processed).

Glue job 2 (processed→warehouse).

Warehouse files visible in S3.

Planned next (near term)
Create Athena DB + netflix_events table and run sample queries.

Write aether_architecture.md with:

Above diagram, DQ philosophy, IAM notes, and sample run log.

Start designing DLQ prefixes + minimal DynamoDB BatchMetadata table.

Add edge‑case data: null IDs, bad event_type, huge payload, late events, and see how DQ + DLQ should behave.

Later phases
Implement full Step Functions orchestrator + Lambda A/B.

Implement batch‑level and row‑level DLQ flows with replay support.

Build simple CLI / console for manual approval + audit logging.

Package infra as code (CDK/Terraform) so solution sellable / reusable ho.

Is summary ko next tab ke top par daal de; koi bhi new session yeh ek file padh ke turant samajh jayega hum kya kar rahe hain, kahan tak aaye hain, aur aage ka roadmap kya hai.

Follow-ups

Schema drift detection in Glue ko implement kaise karein step by step

IAM policies for S3 bucket strict controls ka example

Producer services se events ka flow diagram banao

Next testing steps kya rahenge is data lake project ke liye

Aether architecture MD file ka template kaisa hona chahiye
