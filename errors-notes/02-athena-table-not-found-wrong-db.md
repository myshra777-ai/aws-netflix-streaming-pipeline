In Athena:

sql
SHOW PARTITIONS processed_netflix_events;
-- Output: event_date=2026-01-27, __HIVE_DEFAULT_PARTITION__
Sanity check:

sql
SELECT event_date, COUNT(*) 
FROM processed_netflix_events
GROUP BY event_date
ORDER BY event_date;
Learning
For epoch-based timestamps, always use from_unixtime (or equivalent) before to_date / to_timestamp.

__HIVE_DEFAULT_PARTITION__ is a strong signal of NULL/invalid partition-key values and should be investigated.

text

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
Verification
Confirmed tables with:

sql
SHOW TABLES IN "netflix-streams-aws";
Ran a basic count:

sql
SELECT COUNT(*) 
FROM "netflix-streams-aws"."processed_netflix_events";
Queries executed successfully without TABLE_NOT_FOUND.

Learning
Always verify the active database in Athena before running queries.

When in doubt, use "database"."table" notation to avoid ambiguity.

text

***
