```markdown
# AWS Netflix Streaming Data Pipeline

This project is an end-to-end **AWS-native** data platform inspired by Netflix’s streaming architecture. It simulates user streaming events (play, pause, search, etc.) and builds a scalable pipeline for real-time and batch analytics using AWS services.

---

## 🎯 Goals

- Build a production-style, portfolio-ready streaming + batch data pipeline on AWS  
- Use fully managed AWS services instead of heavy local infra (no Airflow, minimal Docker)  
- Showcase data lake, warehouse, orchestration, and monitoring patterns in one project  

---

## 🏗️ High-Level Architecture (Planned)

**Ingestion & Streaming**

- Simulated user events (Netflix-style playback & interaction logs)
- Amazon Kinesis Data Streams (or Firehose) for real-time ingestion
- Producer scripts running from local / EC2 to push events

**Data Lake & Metadata**

- Amazon S3 with separate zones:
  - `raw` – direct ingested events
  - `processed` – cleaned & enriched data
  - `curated` – analytics-ready tables
- AWS Glue Crawlers + Glue Data Catalog for schema management

**Processing**

- Streaming:
  - AWS Glue Streaming jobs (PySpark) or Kinesis Data Analytics
  - Real-time transformations, partitioned data written to S3
- Batch:
  - AWS Glue batch jobs for hourly/daily aggregations
  - Dimension/fact-style tables for analytics

**Warehouse & Analytics**

- Amazon Redshift for warehouse-style analytics and dashboards
- Amazon Athena for ad-hoc SQL directly on S3
- (Optional later) Amazon QuickSight for BI dashboards

**Orchestration & Monitoring**

- AWS Step Functions to orchestrate Glue jobs, Redshift loads, and Lambdas
- Amazon EventBridge for scheduling and event-driven triggers
- AWS Lambda for small utility tasks (quality checks, housekeeping)
- Amazon SNS for alerts (job failures, SLA breaches)
- Amazon CloudWatch for logs, metrics, and alarms

---

## 📂 Repository Structure

> Current state: skeleton created, implementation will be filled in phase by phase.

```text
ingestion/
  kinesis_producer/
    README.md                # How we generate and send streaming events
    sample_events_generator.py

streaming/
  glue_streaming_jobs/
    README.md                # Design of streaming jobs
    netflix_stream_ingest_job.py

batch_etl/
  glue_jobs/
    daily_aggregations_job.py

warehouse/
  redshift/
    ddl/
      create_tables.sql      # Redshift table schemas
    etl_sql/
      load_from_s3.sql       # COPY / MERGE style scripts

orchestration/
  step_functions/
    netflix_pipeline_state_machine.json
  eventbridge_rules/
    schedules.md

infra/
  terraform/
    main.tf                  # IaC for core AWS resources (to be implemented)

monitoring/
  cloudwatch_alarms/
    alarms.md                # Planned alarms & metrics

docs/
  architecture-diagram.md    # Text / diagram of full architecture
  data_model.md              # Explanation of logical & physical data model
```

---

## 🚦 Roadmap & Phases

**Phase 1 – Basic Streaming Path**

- [ ] Implement local/EC2 event producer → Kinesis → S3 (raw zone)  
- [ ] Configure Glue Crawler + Catalog for raw data  
- [ ] Query raw events via Athena  

**Phase 2 – Streaming Transformations**

- [ ] Implement Glue Streaming job (or KDA) to process Kinesis events  
- [ ] Write processed data to S3 (processed zone) with partitions  

**Phase 3 – Batch ETL & Warehouse**

- [ ] Glue batch job for aggregations (view time, top shows, etc.)  
- [ ] Create Redshift schemas and load data from S3  
- [ ] Build a few core analytics queries / views  

**Phase 4 – Orchestration & Monitoring**

- [ ] Step Functions state machine for end-to-end workflows  
- [ ] EventBridge schedules for daily/hourly runs  
- [ ] Lambda + SNS alerts on failures / anomalies  
- [ ] CloudWatch metrics & alarms documentation  

**Phase 5 – Polish for Portfolio**

- [ ] Finalize docs (`docs/architecture-diagram.md`, `data_model.md`)  
- [ ] Add diagrams and example queries  
- [ ] Optional dashboards (QuickSight / any BI tool)

---

## 🧩 Tech Stack

- Language: Python (PySpark for Glue jobs)
- AWS: Kinesis, S3, Glue, Redshift, Athena, Step Functions, EventBridge, Lambda, SNS, CloudWatch
- Infra as Code: Terraform / CloudFormation (planned)

---

## ✅ Status

- [x] Repository structure bootstrapped  
- [ ] Phase 1 streaming path implementation  
- [ ] Further phases in progress
```

