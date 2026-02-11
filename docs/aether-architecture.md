                 ┌─────────────────────────────┐
                 │      Producer Services      │
                 │  (OLTP / Microservices)     │
                 └─────────────┬───────────────┘
                               │ events
                               ▼
                 ┌─────────────────────────────┐
                 │  Streaming Layer            │
                 │  (Kinesis / Kafka)         │
                 └─────────────┬───────────────┘
                               │ near real-time
                               ▼
──────────────────────── AETHER LAYER 1 – LANDING & METADATA ────────────────────────
                 ┌─────────────────────────────┐
                 │ Raw S3 (Landing)            │
                 │ s3://.../aether/raw/stream/ │
                 │ - Append-only objects       │
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │ Lambda A – Registrar        │
                 └─────────────┬───────────────┘
                               │ writes metadata
                               ▼
                 ┌─────────────────────────────┐
                 │ DynamoDB: BatchMetadata     │
                 │ - batch_id                  │
                 │ - stream_name, shard_id     │
                 │ - s3_prefix_raw             │
                 │ - expected_record_count     │
                 │ - initial_schema_hash       │
                 │ - schema_version_id         │
                 │ - status = "REGISTERED"     │
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │ Contract Registry (AQC)     │
                 │ s3://.../aether/contracts/  │
                 │ - AQC v1 for netflix_events │
                 │   (fields, types, enums,    │
                 │    time-window, meta keys)  │
                 └─────────────────────────────┘

──────────────────────── AETHER LAYER 2 – AUDIT & CONTRACT ENFORCEMENT ─────────────────
                 ┌─────────────────────────────┐
                 │ StepFn: Batch Orchestrator │
                 │ - wait buffer (2–6 min)    │
                 │ - trigger audit per batch  │
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │ Lambda B – Auditor          │
                 │ - recount S3 objects        │
                 │ - recompute schema hash     │
                 │ - look up AQC contract vN   │
                 │ - validate batch vs AQC     │
                 └─────────────┬───────────────┘
                  mismatches   │             matches
        ┌──────────────────────┘
        │
        │   ┌─────────────────────────────┐
        │   │ DLQ S3 – batch-level        │
        │   │ s3://.../aether/dlq/batch/  │
        │   └─────────────────────────────┘
        │   + DynamoDB: status="FAILED_DLQ"
        │
        └───────────────────────────────────────────────►
                               │
                               ▼
                 ┌─────────────────────────────┐
                 │ DynamoDB: BatchMetadata     │
                 │ status = "CONTRACT_OK"      │
                 └─────────────┬───────────────┘
                               ▼

──────────────────────── AETHER LAYER 3 – SHARD PROCESSING & ROW DLQ ──────────────────
                 ┌─────────────────────────────┐
                 │ Glue Job: Contract Enforcer │
                 │  (Raw → Analytics, 100k)   │
                 └─────────────┬───────────────┘
                               ▼
        ┌───────────────────────────────────────────────────────────────┐
        │ Inside job:                                                  │
        │ - read raw batch                                             │
        │ - apply AQC field rules:                                     │
        │   id not null & unique,                                      │
        │   event_type in enum,                                        │
        │   user_id regex,                                             │
        │   amount >= 0,                                               │
        │   ts ISO & within 24h,                                       │
        │   meta has device+region                                     │
        └───────────────────────────────────────────────────────────────┘
             │                             │
             │ clean rows                  │ row violations (with reason)
             ▼                             ▼
   ┌──────────────────────────────┐   ┌────────────────────────────────┐
   │ S3 Analytics (zero copy base)│   │ DLQ S3 – row-level             │
   │ s3://.../aether/analytics/   │   │ s3://.../aether/dlq/row-level/ │
   │ partitioned parquet          │   │   /null_or_missing_id/         │
   └─────────────┬────────────────┘   │   /bad_event_type/            │
                 │                    │   /late_ts/ ...               │
                 │                    └────────────────────────────────┘
                 ▼
      DynamoDB: status = "ANALYTICS_READY"
      + per-batch trust_score (0–100)

──────────────────────── AETHER LAYER 4 – TRUST & APPROVAL (ZERO COPY) ─────────────────
                 ┌─────────────────────────────┐
                 │ Aether Control Console     │
                 │ - shows per-batch:         │
                 │   counts, DLQ %            │
                 │   trust_score              │
                 │ - bulk select batches      │
                 │   trust_score>=T → suggest │
                 │   auto-approve             │
                 └─────────────┬───────────────┘
                      manual   │      auto
                      approve  │      rule
                               ▼
                 ┌─────────────────────────────┐
                 │ DynamoDB: BatchMetadata     │
                 │ status ∈ {WAREHOUSED,      │
                 │          REJECTED,         │
                 │          IDLE_PENDING}     │
                 │ + actor, timestamp, reason │
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │ Audit Log (S3/DynamoDB)     │
                 │ - who approved/rejected     │
                 │ - which contract version    │
                 │ - trust score at decision   │
                 └─────────────────────────────┘

──────────────────────── AETHER LAYER 5 – ZERO-COPY WAREHOUSE VIEWS ────────────────────
                 ┌─────────────────────────────┐
                 │ Logical Warehouse (Athena/ │
                 │ Redshift/Snowflake view)   │
                 │ - points to analytics S3   │
                 │ - filters: status='WAREH.' │
                 │   from BatchMetadata       │
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │ Consumers (BI, ML, APIs)    │
                 │ - read only “approved”      │
                 │   contract-compliant data   │
                 └─────────────────────────────┘

──────────────────────── CROSS-CUTTING – TRUST SCORE & ALERTS ──────────────────────────
- Trust Score Engine (Lambda / Glue Metrics)
  - computes per-batch score from DQ dimensions.
  - auto-approval threshold (e.g. ≥ 99.9%). [web:412][web:415]

- Alerts (Slack / Email)
  - trigger on FAILED_DLQ, low trust score, contract violations, or manual REJECT.


Use this as your master doc; copy‑paste into `AETHER_SYSTEM_DESIGN_PHASE1.md` or similar. It captures contract, pipeline, and breakthroughs so next tab me context zero loss hoga. [datacontract](https://datacontract.com)

***

## 1. Aether Overview

Aether is a **contract‑driven, zero‑copy streaming data platform** for Netflix‑style events on AWS. It ingests events from producers, enforces a strict data quality contract, and exposes only **approved, human‑audited** data to analytics and ML. [redpanda](https://www.redpanda.com/guides/fundamentals-of-data-engineering-streaming-data-pipeline)

Core principles:

- **Contract first**: “Good data” is defined explicitly in a data contract (AQC), not implicitly by lack of errors. [atlan](https://atlan.com/data-contracts/)
- **Zero‑copy promotion**: Data lands once in S3; promotion to “warehouse” is done via metadata (status + views), not by copying files. [cloudthat](https://www.cloudthat.com/resources/blog/data-lake-architecture-using-aws-glue-s3-and-athena/)
- **Fail‑closed for quality**: Anything that violates the contract goes to DLQ/quarantine; warehouse only sees contract‑compliant batches. [clicdata](https://www.clicdata.com/blog/scalable-data-quality-framework-automated-validation/)
- **Human‑in‑the‑loop**: Even “clean” data passes through an accountability gate, with trust scores and manual/auto approval. [clicdata](https://www.clicdata.com/blog/scalable-data-quality-framework-automated-validation/)

***

## 2. Aether Quality Contract (AQC v1)

This is the **frozen layer**. Implementation can change; this contract cannot, except via versioning.

### 2.1 Contract metadata

Stored as YAML/JSON file:

`aether/contracts/netflix_events_v1.yaml`

Fields:

- `version: v1`  
- `status: active`  
- `dataset: netflix_events`  
- `effective_from: 2026-02-10`  
- `owner: data-platform-team`  
- `description: Contract for clean Netflix-style user events.` [github](https://github.com/datacontract/datacontract-specification/blob/main/README.md)

### 2.2 Record‑level schema

Logical fields for `netflix_events`:

- `id: string`  
  - Business identity (UUID or stable string).  
- `event_type: string`  
- `user_id: string`  
- `amount: double (nullable)`  
- `ts: string` (ISO‑8601 timestamp string at storage layer)  
- `meta.device: string`  
- `meta.region: string`  

Storage note: in early phases, Glue writes everything as strings in Parquet; typing is enforced logically by contract + DQ rules, not purely by Parquet schema. [dqops](https://dqops.com/docs/dqo-concepts/configuring-data-quality-checks-and-rules/)

### 2.3 Field‑level quality rules

For a record to be **AQC‑clean**:

- `id`  
  - Not null, not empty, present in payload.  
  - Unique within a batch.  
  - Purpose: deduplication and traceability. [dataqualitypro](https://www.dataqualitypro.com/blog/data-quality-rules-attribute-domain-constraints-arkady-maydanchik)

- `event_type`  
  - Must be one of `['click', 'play', 'pause', 'stop']` (closed enum v1).  
  - No “UNKNOWN”, no arbitrary string or numeric types. [dqops](https://dqops.com/docs/dqo-concepts/configuring-data-quality-checks-and-rules/)

- `user_id`  
  - Length > 5 characters.  
  - Regex: `[A-Za-z0-9\-_]+`.  
  - Prevent obviously fake/bot IDs. [ovaledge](https://www.ovaledge.com/blog/data-quality-metrics)

- `amount` (if present)  
  - Must parse as numeric.  
  - `>= 0`, scale 2 (precision 10,2).  
  - Any negative, NaN, or malformed value is a violation. [ovaledge](https://www.ovaledge.com/blog/data-quality-metrics)

- `ts` (timestamp string)  
  - Valid ISO‑8601 format.  
  - Converted timestamp must lie within **lateness window** (see 2.4). [ibm](https://www.ibm.com/think/topics/data-quality-dimensions)

- `meta`  
  - Must be a struct/object.  
  - Must contain keys `device` and `region`, both non‑empty strings.  
  - Ensures minimum analytics context (device mix, geography). [icedq](https://icedq.com/6-data-quality-dimensions)

### 2.4 Freshness and lateness windows

Aether distinguishes freshness as part of the contract:

- `fresh`: `ts ∈ [now − 6h, now + 5m]`  
  - Counts toward real‑time dashboards.  
- `late`: `ts ∈ (now − 24h, now − 6h]`  
  - Valid but delayed; written to a special **late‑arrival** prefix and surfaced with warnings.  
- `stale/suspicious`: `ts < now − 24h` or unparsable  
  - Routed to DLQ (`late_ts_stale`) for investigation. [ibm](https://www.ibm.com/think/topics/data-quality-dimensions)

Only `fresh` + `late` records can ever be considered “clean”; `stale` is always treated as suspicious.

### 2.5 Batch‑level rules

Each batch (shard) has metadata and quality rules:

- `max_records_per_batch: 100000`  
- `schema_version_id: v1` required  
- `expected_record_count` vs actual count must be within a tight tolerance (exact match in v1).  
- **Contract version match**:  
  - If batch advertises a schema version that doesn’t exist in the contract registry, batch is rejected even if the raw schema hash matches. [confluent](https://www.confluent.io/blog/data-contracts-confluent-schema-registry/)

***

## 3. Architecture Overview (Aether v2)

High‑level: contract‑driven, zero‑copy streaming pipeline on AWS.

### 3.1 Layers

1. **Landing & Metadata** – captures raw S3 files and batch metadata.  
2. **Audit & Contract Enforcement** – verifies counts, schema, and contract version.  
3. **Shard Processing & Row‑Level DLQ** – applies AQC rules to each record.  
4. **Trust & Approval** – computes trust score, supports manual and auto approvals.  
5. **Zero‑Copy Warehouse Views** – surfaces only approved data via logical views. [rudderstack](https://www.rudderstack.com/blog/data-pipeline-architecture/)

### 3.2 Text architecture map

(Short version; long map already defined earlier.)

- Producer Services → Streaming Layer (Kinesis/Kafka) → Raw S3 landing.  
- **Lambda A – Registrar**  
  - On new raw batch, writes `BatchMetadata` to DynamoDB:  
    - `batch_id`, `stream_name`, `shard_id`, `s3_prefix_raw`, `expected_record_count`, `initial_schema_hash`, `schema_version_id`, `status='REGISTERED'`.  
- **Contract Registry**  
  - S3 folder containing contract files (`netflix_events_v1.yaml`, etc.) with schemas and rules. [datacontract](https://datacontract.com)

- **Step Functions Orchestrator**  
  - Waits 2–6 minutes to let S3 stabilize.  
  - Triggers **Lambda B** for each batch.  

- **Lambda B – Auditor**  
  - Lists S3 prefix, recomputes counts and schema hash.  
  - Loads appropriate contract version (based on `schema_version_id`).  
  - If hash mismatch or contract not found → Batch DLQ:  
    - Writes batch‑level error to `aether/dlq/batch/` and sets `status='FAILED_DLQ'`. [clicdata](https://www.clicdata.com/blog/scalable-data-quality-framework-automated-validation/)
  - If OK → `status='CONTRACT_OK'`.  

- **Glue Job – Contract Enforcer (Raw → Analytics)**  
  - Processes up to 100k records per shard.  
  - Reads raw JSON, normalizes columns (currently cast to string in Parquet).  
  - Applies AQC field‑level rules; logically splits into:  
    - `clean_rows` (all rules passed).  
    - `violations` grouped by reason: `null_or_missing_id`, `bad_event_type`, `bad_user_id`, `negative_amount`, `late_ts`, etc.  
  - Writes:  
    - Clean rows → `s3://.../aether/analytics/events/` (Parquet).  
    - Violations → `s3://.../aether/dlq/row-level/<reason>/`.  
  - Updates `BatchMetadata`: `status='ANALYTICS_READY'`, plus per‑batch quality stats (`dq_pass_count`, `dq_fail_count`, `dq_rate`, `contract_version`). [dqops](https://dqops.com/docs/dqo-concepts/configuring-data-quality-checks-and-rules/)

- **Trust Score Engine**  
  - Converts quality stats into a `trust_score` (0–100).  
  - Example components: failure rate, proportion of late arrivals, schema drift incidents, historical reliability of this producer. [firsteigen](https://firsteigen.com/data-pipeline/)

- **Aether Control Console (Manual/Auto approval)**  
  - UI/CLI lists batches with: counts, DLQ %, trust_score, lateness flags.  
  - Supports:  
    - Manual approval (“I have verified analytics data for this period”).  
    - Manual reject / idle.  
    - Bulk auto‑approval for batches with `trust_score >= threshold` (e.g. 99.9%). [firsteigen](https://firsteigen.com/data-pipeline/)
  - Decisions are written to DynamoDB (`status='WAREHOUSED'/'REJECTED'/'IDLE_PENDING'`) and to an **AuditLog** store (user, time, reason).  

- **Zero‑Copy Warehouse (Views)**  
  - Instead of copying files, “warehouse” is a **logical view** over analytics S3, filtered by batch metadata:  
    - `WHERE BatchMetadata.status = 'WAREHOUSED'`.  
  - Athena / Redshift Spectrum / Snowflake external tables point directly at `aether/analytics/events/` but join or filter using batch IDs allowed by Aether. [databend](https://www.databend.com/blog/category-product/2025-08-13-attach-table)

***

## 4. Breakthroughs and Design Decisions

This section captures the key conceptual breakthroughs that shaped the design.

### 4.1 Clean data is “contract‑compliant”, not “no error”

- Earlier design focused on enumerating edge cases (null IDs, bad enums, etc.).  
- New design defines a **positive contract** (AQC) describing what “good” looks like; edge cases are simply anything that violates AQC and get routed to DLQ. [soda](https://soda.io/blog/guide-to-data-contracts)

### 4.2 Late‑arriving data paradox

- Problem: mixing 2‑day‑old data in today’s batch silently restates historical dashboards.  
- Solution: define **lateness windows** in contract: `fresh`, `late`, `stale`, and have separate S3 prefixes and UI indicators for late vs stale. [icedq](https://icedq.com/6-data-quality-dimensions)

### 4.3 Cost‑performance curve (Glue shard tuning)

- Observation: Glue job cost has fixed overhead (cold start, shuffle), so tiny shards are wasteful and very large shards risk OOM. [cloudthat](https://www.cloudthat.com/resources/blog/data-lake-architecture-using-aws-glue-s3-and-athena/)
- Design: use batch metadata (`record_count`, historical runtime and DPU metrics) to choose DPU count and shard splitting strategy dynamically per batch.  

### 4.4 Cross‑batch “impossible” events (stateful audit)

- Example: user logs in from India in batch 1092, then from USA 10 minutes later in batch 1093 – individually clean, jointly suspicious.  
- Design: maintain a `LastKnownState` store (e.g., DynamoDB) with fields like `user_id, last_region, last_ts`. During validation, cross‑check new events against this state to flag physically impossible or anomalous transitions. [ovaledge](https://www.ovaledge.com/blog/data-quality-metrics)

***

## 5. Implementation Status (Phase 1 Lab)

Current lab state (February 2026):

- S3 structure:  
  - `aether/raw/happy_path/` – includes `sample_events.json` and `test_batch.json` (mixed good + bad records).  
  - `aether/processed/events/` – Parquet outputs from Raw→Processed Glue job.  
  - `aether/warehouse/netflix_events/` – happy‑path warehouse Parquet.  
- Glue Raw→Processed job:  
  - Reads JSON from `raw/happy_path/`.  
  - Casts all key columns to string to avoid schema choice errors.  
  - Runs minimal `ColumnCount > 0` DQ rule.  
  - Writes Parquet to `processed/events/`. [cloudthat](https://www.cloudthat.com/resources/blog/data-lake-architecture-using-aws-glue-s3-and-athena/)
- Glue Processed→Warehouse job:  
  - Converts processed Parquet into curated warehouse files with the initial simple schema (`event_id`, `user_id`, `title_id`, `event_type`, `watch_seconds`).  
- Athena:  
  - Database `netflix_analytics`.  
  - Table `netflix_events` pointing to warehouse layer; basic queries (`SELECT *`, `GROUP BY event_type`) succeed. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/100059641/edf20ba8-5c21-413c-8edb-17c295f21167/image.jpg)

Known lab learnings (recorded as failure modes):

- Glue “choice type” errors when fields have mixed types; solved via explicit casting to string. [cloudthat](https://www.cloudthat.com/resources/blog/data-lake-architecture-using-aws-glue-s3-and-athena/)
- Parquet vs Athena schema mismatches (e.g., binary vs timestamp); solved by storing timestamps as string and parsing in queries. [docs.aws.amazon](https://docs.aws.amazon.com/athena/latest/ug/tables-location-format.html)

***

## 6. Next Steps (when you resume)

When you open a new tab and want to continue, you can start from this checklist:

1. **Finalize AQC v1 file**  
   - Implement `netflix_events_v1.yaml` with schema, field rules, lateness windows, batch rules, and version metadata.

2. **Wire contract into Glue Raw→Processed job**  
   - Load AQC v1 from S3 at job start (even if you only log the version for now).  
   - Gradually implement AQC rules (e.g., `IsComplete(id)`, enum check on `event_type`) and route violations to DLQ prefixes (`aether/dlq/row-level/<reason>/`). [dqops](https://dqops.com/docs/dqo-concepts/configuring-data-quality-checks-and-rules/)

3. **Define DLQ layout**  
   - `aether/dlq/batch/` for batch‑level failures.  
   - `aether/dlq/row-level/{null_id,bad_event_type,late_ts,...}` for record‑level violations. [clicdata](https://www.clicdata.com/blog/scalable-data-quality-framework-automated-validation/)

4. **Extend BatchMetadata table**  
   - Add fields: `schema_version_id`, `contract_version`, `dq_pass_count`, `dq_fail_count`, `trust_score`.  

5. **Design the first version of the Control Console**  
   - CLI or simple UI that reads BatchMetadata and shows: counts, DLQ %, trust_score, status, and AQC version.  
   - Allow manual `approve/skip/reject` operations, writing to AuditLog. [firsteigen](https://firsteigen.com/data-pipeline/)

This document + the previous architecture map should give any future session full context so that development can resume without re‑figuring the design.