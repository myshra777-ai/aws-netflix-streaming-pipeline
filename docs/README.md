

```markdown
# AWS Netflix Streaming Data Pipeline (Serverless, Near Real‑Time)

This project is an end‑to‑end, Netflix‑style clickstream data pipeline built on AWS using Kinesis Data Firehose, S3, AWS Glue 5.0, and Amazon Athena.[web:113][web:109]  
It ingests streaming playback events, lands them in an S3 data lake, performs ETL and basic data quality checks with Glue, and exposes a partitioned analytics layer for interactive SQL queries in Athena.

---

## 1. High‑Level Architecture

**Flow:** Client events → Kinesis Data Firehose → S3 raw zone → Glue ETL job → S3 processed zone (Parquet, partitioned) → Glue Catalog → Athena.

- Ingestion: Netflix‑style playback events (play, pause, stop, seek, etc.) are sent to an Amazon Kinesis Data Firehose delivery stream.  
- Storage: Firehose writes batched JSON/CSV data to an S3 “raw” prefix in a data lake bucket.  
- ETL: An AWS Glue 5.0 Spark job (`netflix-raw-to-processed`) reads the raw table, cleans and enriches the data, and writes optimized Parquet files to a “processed” prefix partitioned by `event_date`.  
- Metadata: AWS Glue Data Catalog stores table definitions for both raw and processed datasets.  
- Analytics: Amazon Athena queries the processed table using SQL for per‑title views, event‑type distributions, and date‑wise metrics.[web:70][web:122]

> You can find a deeper description of the architecture and data model under `docs/architecture.md` and `docs/data_model.md`.

---

## 2. Screenshots – Pipeline in Action

These screenshots show the pipeline running end to end on AWS (Glue job, S3 data lake, Athena queries, and CloudWatch monitoring).[web:114]

### 2.1 AWS Glue – ETL Job Runs

- Glue job run details (job succeeded, execution time, DPUs, Spark UI enabled)  
- Spark UI showing stages and executor timeline for the `netflix-raw-to-processed` job

![Glue job run details](screenshots/netflix-pipeline/glue-jobs/glue-job-run-details.png)
![Glue Spark UI stages](screenshots/netflix-pipeline/glue-jobs/glue-spark-ui-stages.png)

### 2.2 Amazon S3 – Raw and Processed Layers

- Processed data path with:
  - `event_date=2026-01-27/` partition
  - `event_date=__HIVE_DEFAULT_PARTITION__/` for rows where partition key was initially null  
- Processed Parquet files inside each partition, compressed with Snappy

![S3 processed partitions](screenshots/netflix-pipeline/s3-processed/s3-processed-event-date-partitions.png)
![S3 default partition](screenshots/netflix-pipeline/s3-processed/s3-processed-hive-default-partition.png)

### 2.3 Amazon Athena – Analytics Queries

- Query showing per‑`event_date` row counts (~3010 rows per day)  
- Event‑type distribution (e.g., `PLAY_START`, `PLAY_STOP`, etc.)  
- Top titles by views, country‑wise distribution

![Athena per-date counts](screenshots/netflix-pipeline/athena-queries/athena-rows-per-date.png)
![Athena event-type distribution](screenshots/netflix-pipeline/athena-queries/athena-event-type-distribution.png)
![Athena top titles](screenshots/netflix-pipeline/athena-queries/athena-top-titles.png)
![Athena country-wise events](screenshots/netflix-pipeline/athena-queries/athena-country-events.png)

### 2.4 CloudWatch – Monitoring

- CloudWatch alarm monitoring Glue job resource usage for the Netflix ETL job

![CloudWatch Glue alarm](screenshots/netflix-pipeline/cloudwatch/glue-job-resource-usage-alarm.png)

---

## 3. Use Case and Goals

**Use case:**  
Simulate Netflix‑like streaming analytics where product teams need to answer questions such as:

- How many play events did we receive per day?  
- Which titles are being watched the most?  
- How does usage vary by device type or country?  

**Goals:**

- Design a fully serverless data pipeline using AWS managed services.  
- Separate raw and processed zones in an S3 data lake and use schema‑on‑read.  
- Implement a reusable Glue ETL job with partitioned Parquet output.  
- Provide documentation (architecture, setup, troubleshooting, runbook) like a production system.

---

## 4. Architecture Details

### 4.1 AWS Services Used

- **Amazon Kinesis Data Firehose** – Ingests streaming events and delivers them to S3 in near real time. 
- **Amazon S3** – Data lake storage with separate raw and processed prefixes.  
- **AWS Glue 5.0** – Spark ETL job (`netflix-raw-to-processed`), Data Catalog tables, optional Data Quality checks.  
- **Amazon Athena** – Serverless interactive SQL engine querying Glue Catalog tables over S3.  
- **Amazon CloudWatch** – Logs for Glue jobs and alarms on Glue resource usage.

### 4.2 Data Lake Layout

Example bucket and prefixes:

- Bucket: `myshr-netflix-datalake-ap-south-1`  
- Raw zone: `s3://myshr-netflix-datalake-ap-south-1/netflix/ingest_year=2026/`  
- Processed zone: `s3://myshr-netflix-datalake-ap-south-1/netflix/processed_partitioned/`

Processed layout (Hive‑style partitions):

```text
netflix/processed_partitioned/
  event_date=2026-01-27/
  event_date=__HIVE_DEFAULT_PARTITION__/
```

More details are documented in `docs/architecture.md`.

---

## 5. Data Model

### 5.1 Raw Events Table

- Database: `netflix-streams-aws`  
- Table: `raw_netflix_events_rootevents`  
- Location: S3 raw prefix

Key columns (logical):

- `user_id` – User/account identifier  
- `profile_id` – Profile within the account  
- `content_id` or `title_id` – Movie/show identifier  
- `event_type` – `PLAY_START`, `PLAY_STOP`, `PAUSE`, `SEEK`, etc.  
- `event_ts` – Event timestamp in epoch seconds  
- `device_type` – Mobile, web, TV, etc.  
- `country` – Country code  
- `raw_payload` – Original JSON string (optional)

### 5.2 Processed Events Table

- Database: `netflix-streams-aws`  
- Table: `processed_netflix_events`  
- Location: S3 processed prefix  
- Partition key: `event_date`

Columns:

- `user_id`  
- `profile_id`  
- `content_id` / `title_id`  
- `event_type`  
- `event_ts`  
- `event_timestamp` – Converted from epoch  
- `event_date` – Date derived from `event_ts` (partition)  
- `device_type`  
- `country`  

See `netflix-pipeline/docs/design/data_dictionary.md` for the full data dictionary.

---

## 6. Repository Structure

```text
aws-netflix-streaming-pipeline/
  glue-scripts/
    netflix-raw-to-processed.py          # Glue ETL job script
  docs/
    architecture.md                      # Platform-level architecture
    data_model.md                        # Global data model
    runbook_failures.md                  # Detailed failure analysis and recovery
  netflix-pipeline/
    docs/
      architecture/
        architecture.md                  # App-level architecture overview
      design/
        data_dictionary.md               # Processed table dictionary
      operations/
        setup_guide.md                   # Step-by-step AWS setup guide
        troubleshooting.md               # Common issues and quick checks
  screenshots/
    netflix-pipeline/
      s3-raw/
      s3-processed/
      glue-jobs/
      athena-queries/
      cloudwatch/
```

This layout mirrors how production data platforms separate code, documentation, and operations runbooks.

---

## 7. How to Run This Project

### 7.1 Prerequisites

- AWS account with access to:
  - S3, Kinesis Data Firehose, Glue, Athena, CloudWatch  
- AWS CLI or console access.  
- Python environment (for local utilities, if used).  
- This repository cloned locally.

### 7.2 Step 1 – Create S3 Bucket

1. Create an S3 bucket, for example:  
   `myshr-netflix-datalake-ap-south-1`.  
2. Create (or just rely on) the following prefixes:
   - `netflix/ingest_year=2026/` for raw data  
   - `netflix/processed_partitioned/` for processed data  

### 7.3 Step 2 – Configure Kinesis Data Firehose

1. Create a Firehose delivery stream with:
   - Source: Direct PUT (or your streaming producer)  
   - Destination: S3  
   - S3 prefix: `netflix/ingest_year=2026/`  
2. Set buffering interval and size based on desired latency.  
3. Attach an IAM role that allows Firehose to write to the bucket.

### 7.4 Step 3 – Glue Data Catalog and Crawler

1. Create Glue database `netflix-streams-aws`.  
2. Create a Glue Crawler:
   - Data source: S3 raw prefix  
   - Target database: `netflix-streams-aws`  
   - Table prefix: `raw_` (optional)  
3. Run crawler to create `raw_netflix_events_rootevents`.

### 7.5 Step 4 – Glue ETL Job (`netflix-raw-to-processed`)

1. In Glue → Jobs, create a Spark job:  

   - Name: `netflix-raw-to-processed`  
   - Glue version: 5.0 (Spark)  
   - Worker type: `G.1X`, 2 workers (example)  
   - Script: upload `glue-scripts/netflix-raw-to-processed.py`  

2. Configure:
   - Input: raw table from Glue Catalog  
   - Output: `s3://.../netflix/processed_partitioned/` as Parquet, Snappy  
   - Partition key: `event_date`  

3. Run the job on demand and verify:
   - S3 processed prefix contains per‑date partitions  
   - Glue Catalog has `processed_netflix_events` table  

Screenshots in `screenshots/netflix-pipeline/glue-jobs/` show a successful job run with Spark UI and metrics.

### 7.6 Step 5 – Query with Athena

1. In Athena, set query results location to a path in your S3 bucket.  
2. Select database `netflix-streams-aws`.  
3. Confirm tables:

   ```sql
   SHOW TABLES IN "netflix-streams-aws";
   ```

4. Discover partitions (if needed):

   ```sql
   MSCK REPAIR TABLE processed_netflix_events;
   ```

5. Run example queries:

   ```sql
   -- Rows per date
   SELECT event_date, COUNT(*) AS rows_per_date
   FROM processed_netflix_events
   GROUP BY event_date
   ORDER BY event_date;

   -- Event-type distribution
   SELECT event_type, COUNT(*) AS events
   FROM processed_netflix_events
   GROUP BY event_type
   ORDER BY events DESC;

   -- Top titles by views
   SELECT title_id, COUNT(*) AS views
   FROM raw_netflix_events_rootevents
   WHERE event_type = 'PLAY_START'
   GROUP BY title_id
   ORDER BY views DESC
   LIMIT 10;
   ```

Screenshots in `screenshots/netflix-pipeline/athena-queries/` correspond to these queries.

---

## 8. Operations and Troubleshooting

### 8.1 Quick Health Checklist

- Raw S3 prefix receiving new objects from Firehose.  
- Glue crawler successfully updating raw table schema.  
- Glue job runs succeed without data quality failures.  
- Processed S3 prefix has fresh `event_date=YYYY-MM-DD/` folders.  
- Athena queries return results for latest dates.

### 8.2 Common Issues

Common failures and their fixes are documented in:

- `docs/runbook_failures.md` – Detailed runbook with root causes and recovery steps.  
- `netflix-pipeline/docs/operations/troubleshooting.md` – Quick troubleshooting guide.

Typical problems include:

- `__HIVE_DEFAULT_PARTITION__` folders due to null `event_date`.  
- Missing partitions in Athena until `MSCK REPAIR TABLE` is run.  
- Glue job failures due to schema drift or DQ rule violations.

---

## 9. What I Learned

From this project I practiced:

- Designing a serverless data pipeline on AWS (Kinesis → S3 → Glue → Athena).  
- Working with partitioned Parquet datasets and Glue Catalog metadata.  
- Debugging Glue Spark jobs using the Spark UI, logs, and CloudWatch alarms.  
- Writing production‑style documentation (architecture, setup, runbook) for a data engineering project.

---

## 10. Future Improvements

Planned enhancements:

- Add a streaming ingestion component (Kinesis Data Streams or Kafka) with a small producer app.  
- Introduce more advanced data quality checks and alerts (e.g., volume anomalies per day).  
- Move orchestration to Step Functions or Apache Airflow.  
- Add a simple dashboard (QuickSight or Streamlit) on top of Athena queries.
```
