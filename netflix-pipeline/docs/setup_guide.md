Go to Crawlers and create a new crawler:

Data source: S3

Path: s3://myshr-netflix-datalake-ap-south-1/netflix/ingest_year=2026/

IAM role: Select or create a role with S3 read and Glue catalog permissions.

Target database: netflix-streams-aws

Table name prefix (optional): e.g., raw_

Run the crawler and verify that the table raw_netflix_events_rootevents is created.[web:73][web:81]

5. Glue ETL Job – netflix-raw-to-processed
In the AWS console, go to AWS Glue → ETL jobs.

Create a new job:

Name: netflix-raw-to-processed

IAM role: Glue role with access to:

Raw and processed S3 prefixes

Glue Data Catalog

CloudWatch Logs

Glue version: 4.0 or 5.0 (Spark)[web:62]

Type: Spark job.

Attach the script from this repository:

Local path: glue-scripts/netflix-raw-to-processed.py

Upload to S3 or copy-paste into the Glue script editor.

Set job parameters:

Choose the same region as your S3 buckets and Firehose.

(Optional) Add job arguments if required.

Configure the job output:

Output path: s3://myshr-netflix-datalake-ap-south-1/netflix/processed_partitioned/

Format: Parquet

Compression: Snappy

Partition keys: event_date

Enable updating the Glue Data Catalog table processed_netflix_events.

Save the job.

You can run the job on demand (no schedule is required; the default state can remain “Active” without any triggers).[web:44][web:48]

6. Athena Setup
Open the Amazon Athena console.

Set up a query result location:

For example: s3://myshr-netflix-datalake-ap-south-1/athena-results/

In the database dropdown, select:

text
netflix-streams-aws
Verify tables:

sql
SHOW TABLES IN "netflix-streams-aws";
You should see:

raw_netflix_events_rootevents

processed_netflix_events

List partitions of the processed table:

sql
SHOW PARTITIONS processed_netflix_events;
Run sample queries:

sql
-- Daily volume
SELECT event_date, COUNT(*) AS total_events
FROM processed_netflix_events
GROUP BY event_date
ORDER BY event_date;

-- Sample events
SELECT *
FROM processed_netflix_events
WHERE event_date = DATE '2026-01-27'
LIMIT 20;
7. Local Repository Structure
From the root of this repository:

text
aws-netflix-streaming-pipeline/
  glue-scripts/
    netflix-raw-to-processed.py
  errors-notes/
  sql/
  docs/
  netflix-pipeline/
    docs/
      setup_guide.md
      architecture.md
      data_dictionary.md
      troubleshooting.md
Core ETL logic lives in glue-scripts/.

Documentation lives under docs/ and netflix-pipeline/docs/.

8. Validation Checklist
After setup, verify:

 Firehose successfully delivers events to the raw S3 prefix.

 Glue crawler creates/updates raw_netflix_events_rootevents.

 Glue job netflix-raw-to-processed runs successfully.

 Processed S3 path contains event_date=... partitions.

 Athena can run daily counts and sample queries on processed_netflix_events.

 There are no unexpected failures described in runbook_failures.md.

If issues occur, consult troubleshooting.md and runbook_failures.md.

