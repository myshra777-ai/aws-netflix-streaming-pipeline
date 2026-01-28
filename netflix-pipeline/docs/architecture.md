
***

## 2) `netflix-pipeline/docs/architecture.md`

This can reference top-level docs but scoped to the “app”:

```markdown
# Application Architecture

This document summarizes the application-level architecture of the Netflix streaming pipeline as implemented in this repository. For a more detailed platform view, see the top-level `docs/architecture.md` and `docs/data_model.md`.[web:71][web:74]

## Layers

1. **Ingestion Layer**
   - Event producers (synthetic or real) send Netflix-style clickstream events.
   - Kinesis Data Firehose delivers events into S3 `netflix/ingest_year=2026/`.

2. **Storage Layer**
   - Raw zone: S3 prefix `netflix/ingest_year=2026/`.
   - Processed zone: S3 prefix `netflix/processed_partitioned/` partitioned by `event_date`.

3. **Processing Layer**
   - AWS Glue job `netflix-raw-to-processed` performs:
     - Type conversions and derived fields.
     - Epoch-to-date conversion.
     - Optional data quality checks.

4. **Analytics Layer**
   - Glue Catalog tables:
     - `raw_netflix_events_rootevents`
     - `processed_netflix_events`
   - Amazon Athena provides SQL access for analysis and reporting.

## Code Modules (Logical)

- `glue-scripts/netflix-raw-to-processed.py` – main ETL job.
- `src/source/` – ingestion helpers (CSV, S3, Kinesis).
- `src/processing/` – transformation logic and utilities.
- `sql/` – reusable Athena query templates.

This structure follows a typical production-ready data pipeline layout where ingestion, processing, and analytics layers are clearly separated.
