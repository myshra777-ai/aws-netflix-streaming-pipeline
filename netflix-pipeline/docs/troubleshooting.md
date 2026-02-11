

```markdown
# Troubleshooting Guide

This guide summarizes common operational issues for the Netflix streaming pipeline and where to look first when something goes wrong.[web:69][web:72]

For deeper root-cause analysis and step-by-step recovery, see the top-level `docs/runbook_failures.md` and `errors-notes/` files.

---

## 1. No Data Appearing in Raw S3 Location

**Symptoms**

- Firehose delivery stream is active, but S3 `netflix/ingest_year=2026/` remains empty.

**Checks**

1. Verify that the event producer is actually sending data to the Firehose endpoint.
2. Check Firehose monitoring metrics (delivery success/failure) in CloudWatch.[web:81]
3. Confirm the Firehose destination bucket and prefix are correct.
4. Inspect Firehose error logs for permission or format errors.

---

## 2. Raw Table Missing or Out of Date

**Symptoms**

- Glue Catalog does not show `raw_netflix_events_rootevents`, or schema is stale.

**Checks**

1. Make sure Glue database `netflix-streams-aws` exists.
2. Rerun the Glue crawler over the raw S3 path.
3. Confirm the crawler IAM role has read access to the S3 bucket and write access to the Glue Catalog.[web:73]

---

## 3. Processed Table Exists but Partitions Are Missing

**Symptoms**

- `processed_netflix_events` table exists, but `SHOW PARTITIONS` returns no or fewer partitions than expected.

**Checks**

1. Confirm the Glue job `netflix-raw-to-processed` completed successfully.
2. Verify that the job output path and partitionKeys configuration match the expected S3 layout.
3. Check S3 for partition folders `event_date=YYYY-MM-DD/`.
4. If required, run `MSCK REPAIR TABLE processed_netflix_events;` for Hive-style partition discovery.

---

## 4. Athena Queries Return `TABLE_NOT_FOUND`

**Symptoms**

- Athena returns `TABLE_NOT_FOUND` for `raw_netflix_events_rootevents` or `processed_netflix_events`.

**Checks**

1. In Athena, ensure the selected database is `netflix-streams-aws`.
2. Use fully qualified table names when in doubt:

   ```sql
   SELECT * 
   FROM "netflix-streams-aws"."processed_netflix_events"
   LIMIT 10;

Confirm via:

sql

SHOW TABLES IN "netflix-streams-aws";

5. Glue Job Fails with Data Quality Errors
Symptoms

Glue job fails or logs errors related to Data Quality processing.

Checks

Confirm that EvaluateDataQuality is configured with valid rulesets.

Make sure SelectFromCollection and other helper classes are imported correctly.

Check CloudWatch logs for details about which column/rule failed.[web:59]

6. Performance or Cost Issues
Symptoms

Glue jobs take longer than expected or Athena queries scan large amounts of data.

Checks

Verify that output is stored as Parquet with Snappy compression.

Ensure queries filter on event_date to take advantage of partition pruning.

Avoid SELECT * on large tables without filters.

Consider increasing Glue job DPUs only when necessary.[web:76][web:80]

When in Doubt
Use this general checklist:

Is data arriving in S3?

Are the Glue tables and partitions up to date?

Is the Glue job configuration (paths, partitions, compression) correct?

Is the correct database selected in Athena?

Are errors documented in errors-notes/ and reflected in runbook_failures.md?

Keeping this guide updated with real incidents over time will make the pipeline much easier to operate in a production-like environment.