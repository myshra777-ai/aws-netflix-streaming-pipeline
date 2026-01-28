### 1) `errors-notes/01-hive-default-partition-null-date.md`

```markdown
# Error 01 – __HIVE_DEFAULT_PARTITION__ with NULL event_date

## Context
- Job: `netflix-raw-to-processed`
- Source: `raw_netflix_events_rootevents` (Kinesis → S3 raw)
- Target: `processed_netflix_events` (S3 `processed_partitioned/`, partitioned by `event_date`)
- Symptom: In Athena, `SHOW PARTITIONS processed_netflix_events;` showed:
  - `event_date=2026-01-27`
  - `__HIVE_DEFAULT_PARTITION__` (around 5 rows with NULL `event_date`)

## Root Cause
- The raw timestamp column `event_ts` was stored in epoch seconds.
- In the first version of the job, `event_date` was derived using `to_date(col("event_ts"))` directly.
- Glue/Athena expect a proper timestamp or date string; feeding epoch seconds directly to `to_date` produced NULL.
- Rows with NULL partition key values are automatically grouped under `__HIVE_DEFAULT_PARTITION__`.

## Fix
Convert epoch seconds to a proper timestamp string first, then extract the date:

```python
from pyspark.sql.functions import col, from_unixtime, to_date

df = df.withColumn(
    "event_date",
    to_date(from_unixtime(col("event_ts")))
)
```

## Verification
- Reran the Glue job.
- In S3 processed path:
  - `.../processed_partitioned/event_date=2026-01-27/` contained ~3000 rows.
  - `__HIVE_DEFAULT_PARTITION__` contained only a few bad rows.
- In Athena:

```sql
SHOW PARTITIONS processed_netflix_events;
-- Output: event_date=2026-01-27, __HIVE_DEFAULT_PARTITION__
```

- Sanity check:

```sql
SELECT event_date, COUNT(*) 
FROM processed_netflix_events
GROUP BY event_date
ORDER BY event_date;
```

## Learning
- For epoch-based timestamps, always use `from_unixtime` (or equivalent) before `to_date` / `to_timestamp`.
- `__HIVE_DEFAULT_PARTITION__` is a strong signal of NULL/invalid partition-key values and should be investigated.
```

***

### 2) `errors-notes/02-athena-table-not-found-wrong-db.md`

```markdown
# Error 02 – TABLE_NOT_FOUND in Athena (wrong database)

## Context
- Glue database: `netflix-streams-aws`
- Tables:
  - `raw_netflix_events_rootevents`
  - `processed_netflix_events`
- Symptom:
  - Athena returned `TABLE_NOT_FOUND` when running queries on these tables.

## Root Cause
- In the Athena console, the selected database was `default`.
- The Glue tables were created under the `netflix-streams-aws` database.
- Queries were executed either:
  - With the wrong active database selected, or
  - Without fully qualifying the table name.

## Fix
1. In Athena, change the active database from `default` to `netflix-streams-aws`.
2. Optionally, use fully qualified table names:

```sql
SELECT * 
FROM "netflix-streams-aws"."raw_netflix_events_rootevents"
LIMIT 10;
```

## Verification
- Confirmed tables with:

```sql
SHOW TABLES IN "netflix-streams-aws";
```

- Ran a basic count:

```sql
SELECT COUNT(*) 
FROM "netflix-streams-aws"."processed_netflix_events";
```

- Queries executed successfully without `TABLE_NOT_FOUND`.

## Learning
- Always verify the active database in Athena before running queries.
- When in doubt, use `"database"."table"` notation to avoid ambiguity.
```

***

### 3) `errors-notes/03-glue-dq-selectfromcollection-import.md`

```markdown
# Error 03 – Glue Data Quality: SelectFromCollection import issue

## Context
- AWS Glue 5.0 job using Data Quality on a DynamicFrame.
- Goal: Run data quality rules and capture row-level outcomes.
- Symptom:
  - Code used `SelectFromCollection.apply(dfc=dq_collection, key="rowLevelOutcomes")`,
  - The job failed with an import/reference error for `SelectFromCollection`.

## Root Cause
- The `SelectFromCollection` class was not imported.
- `EvaluateDataQuality().process(...)` returns a `DynamicFrameCollection`.
- To extract a specific DynamicFrame from that collection (for example, `rowLevelOutcomes`), `SelectFromCollection` must be imported and used.

## Fix
- Add the correct import:

```python
from awsglue.dynamicframe import SelectFromCollection
```

- Use the recommended pattern:

```python
from awsglue.data_quality import EvaluateDataQuality, DataQualityRuleset
from awsglue.dynamicframe import SelectFromCollection

dq_ruleset = DataQualityRuleset(
    ruleset="your_rules_here"
)

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
```

## Verification
- After adding the import, the job no longer failed on the `SelectFromCollection` line.
- `dq_results_dyf` was created successfully and could be written to S3 or inspected further.

## Learning
- When working with Glue Data Quality and `DynamicFrameCollection`, ensure all required helper classes (like `SelectFromCollection`) are imported.
- Copying examples from docs without imports is a common source of runtime errors; always double-check imports.
```

