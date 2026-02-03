# v1 Core Pipeline

v1 represents the **core, production-style data pipeline** without any AI extras.  
Iska goal hai Netflix-style events ko raw se processed tak reliably le jaana, DQ/DLQ handle karna, aur query layer expose karna.

---

## v1 Core Pipeline – Roadmap

- **01_ingestion**  
  Read raw Netflix events from Kinesis/stream or batch files and land them in the raw S3 layer.

- **02_raw_to_processed**  
  Glue job to clean, transform, and partition data into the processed S3 layer.

- **03_dq_and_dlq**  
  Run data quality checks on processed data and route bad records to a DLQ S3 path.

- **04_query_layer**  
  Expose curated tables/views via Athena or Redshift for analytics and dashboards.

---

## Folder Structure

- `01_ingestion/`  
  - Future home for ingestion Glue/Lambda code.
  - Responsibility: get data from source systems (Kinesis, batch files, etc.) into `s3://<bucket>/netflix/raw/`.

- `02_raw_to_processed/`  
  - `glue_job_raw_to_processed.py`: main ETL job that reads raw data, applies transformations, and writes partitioned data to processed layer.  
  - Writes to something like: `s3://<bucket>/netflix/processed_partitioned/`.

- `03_dq_and_dlq/`  
  - Will contain jobs/scripts to:
    - Run data quality rules on processed data.
    - Send failed/bad records to a DLQ path (e.g. `s3://<bucket>/netflix/dlq/`).

- `04_query_layer/`  
  - Will contain definitions/docs for:
    - Athena/Redshift tables or views.
    - Example analytical queries on top of the processed layer.

---

## Current Status (v1)

- Core ETL:
  - `02_raw_to_processed/glue_job_raw_to_processed.py` is the main Glue job for raw → processed.
- Ingestion:
  - Folder exists, final ingestion job still to be moved/implemented here.
- DQ & DLQ:
  - Folder exists, rules and DLQ job still to be implemented.
- Query layer:
  - Folder exists, to be wired to Athena/Redshift and linked with example SQL.

---

## Next Steps Ideas (v1)

- Define and move ingestion job into `01_ingestion/` with a clear name (e.g. `glue_job_ingestion_to_raw.py`).
- Implement minimal DQ checks + DLQ handling in `03_dq_and_dlq/`.
- Add a couple of core Athena/Redshift queries under `04_query_layer/` and link them from the top-level README.
