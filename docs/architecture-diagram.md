# Streaming Pipeline Architecture (AWS Netflix-style)

## High-level flow

1. Synthetic Event Generator  
   - Component: `ingestion/kinesis_producer/sample_events_generator.py`  
   - Generates Netflix-style playback/search events (play, pause, seek, stop, search).  
   - Uses a user-based `partition_key` to group all events of a user together.

2. Streaming Ingestion (Amazon Kinesis Data Streams)  
   - Managed streaming service for real-time event ingestion.  
   - Producers send JSON events with `PartitionKey = user_id`.  
   - Streams can be scaled by increasing shard count.

3. Real-time Processing (AWS Glue Streaming Job)  
   - Consumes events from Kinesis in mini-batches.  
   - Applies basic cleaning, type casting, and enrichment.  
   - Writes results to the S3 data lake.

4. Data Lake Storage (Amazon S3)  
   - Raw zone: `s3://<bucket-name>/raw/events/` (as-ingested JSON).  
   - Processed zone: `s3://<bucket-name>/processed/events/` (cleaned/partitioned).  
   - Curated zone: `s3://<bucket-name>/curated/aggregates/` (aggregations, user/title level).

5. Metadata & Catalog (AWS Glue Data Catalog + Crawlers)  
   - Crawlers scan S3 locations and infer table schemas.  
   - Tables registered in Glue Data Catalog for Athena/Redshift.

6. Query & Analytics (Athena / Redshift)  
   - Athena: ad-hoc SQL directly on S3 data.  
   - Redshift: modeled tables (e.g. fact_events, dim_user, dim_title) for BI dashboards.

7. Orchestration & Monitoring (later phases)  
   - AWS Step Functions / Amazon EventBridge: coordinate batch jobs and triggers.  
   - Amazon CloudWatch + Amazon SNS: monitor job failures, lag, and send alerts.

## Text diagram

```text
[ Synthetic Event Generator (Python) ]
                |
                v
[ Amazon Kinesis Data Streams ]
                |
                v
[ AWS Glue Streaming Job ]
                |
                v
[ Amazon S3 Data Lake ]
   - raw/events/
   - processed/events/
   - curated/aggregates/
                |
                v
[ Glue Crawler + Data Catalog ]
                |
                v
[ Athena / Redshift ]
                |
                v
[ Dashboards / Analytics / Consumers ]
