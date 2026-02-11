```markdown
# Runbook – Common Failures and Recovery

This runbook captures the most common failures observed in the Netflix streaming pipeline and how to troubleshoot and recover from them.[web:68][web:69][web:72]

---

## 1. __HIVE_DEFAULT_PARTITION__ Appears in Processed Data

**Symptoms**

- Athena `SHOW PARTITIONS processed_netflix_events;` shows:
  - `event_date=2026-01-27`
  - `__HIVE_DEFAULT_PARTITION__`
- A small number of rows have `event_date` = NULL.

**Likely Cause**

- `event_date` derivation from `event_ts` is failing.
- `event_ts` is stored as epoch seconds, but the Glue job is calling `to_date(col("event_ts"))` directly instead of converting epoch to timestamp first.
- Any row producing NULL for the partition key is placed in `__HIVE_DEFAULT_PARTITION__`.[web:69]

**How to Fix**

1. Update the Glue ETL logic:

   ```python
   from pyspark.sql.functions import col, from_unixtime, to_date

   df = df.withColumn(
       "event_date",
       to_date(from_unixtime(col("event_ts")))
   )
Rerun the Glue job for the affected data.

Verify partitions:

sql
SHOW PARTITIONS processed_netflix_events;
Optionally inspect the default partition:

sql
SELECT *
FROM processed_netflix_events
WHERE event_date IS NULL
LIMIT 50;
Reference

Detailed write-up: errors-notes/01-hive-default-partition-null-date.md

2. TABLE_NOT_FOUND in Athena
Symptoms

Athena returns TABLE_NOT_FOUND for tables that are known to exist in the Glue Catalog.

Likely Cause

Wrong database selected in Athena (e.g., default instead of netflix-streams-aws).[web:73]

Query referencing table without a fully qualified name.

How to Fix

In the Athena console, change the active database to netflix-streams-aws.

Or use a fully qualified name:

sql
SELECT *
FROM "netflix-streams-aws"."processed_netflix_events"
LIMIT 10;
Confirm table presence:

sql
SHOW TABLES IN "netflix-streams-aws";
Reference

Detailed write-up: errors-notes/02-athena-table-not-found-wrong-db.md

3. Glue Data Quality – SelectFromCollection Import Errors
Symptoms

Glue job fails on a line similar to:

python
dq_results_dyf = SelectFromCollection.apply(
    dfc=dq_collection,
    key="rowLevelOutcomes"
)
Error message indicates SelectFromCollection is not defined or import is missing.

Likely Cause

Missing import for SelectFromCollection.

Working with a DynamicFrameCollection returned by EvaluateDataQuality without importing the helper class.[web:59]

How to Fix

Add the import at the top of the script:

python
from awsglue.dynamicframe import SelectFromCollection
Use the recommended pattern:

python
from awsglue.data_quality import EvaluateDataQuality, DataQualityRuleset
from awsglue.dynamicframe import SelectFromCollection

dq_ruleset = DataQualityRuleset(ruleset="your_rules_here")

dq_collection = EvaluateDataQuality().process(
    glueContext,
    frame=transformed_dyf,
    ruleset=dq_ruleset,
    publishing_options=None
)

dq_results_dyf = SelectFromCollection.apply(
    dfc=dq_collection,
    key="rowLevelOutcomes"
)
Rerun the job and confirm successful completion.

Reference

Detailed write-up: errors-notes/03-glue-dq-selectfromcollection-import.md

4. General Debugging Checklist
When any failure occurs:

Reproduce the issue

Capture logs from Glue job run / Athena query ID.

Re-run on a small subset if possible.[web:69][web:72]

Locate the failing stage

Is the problem in ingestion (Firehose/S3), ETL (Glue), or analytics (Athena)?

Check recent changes

Schema changes, partition logic, or configuration updates often introduce breakage.

Document the incident

Add a short summary and fix to errors-notes/ and keep runbook_failures.md updated for future reference