# Data Model

## Raw Events: raw_netflix_events_rootevents

**Location**

- Database: `netflix-streams-aws`
- Table: `raw_netflix_events_rootevents`
- S3 prefix: `s3://myshr-netflix-datalake-ap-south-1/netflix/ingest_year=2026/`

**Logical schema**

- `user_id` (string)  
  Unique identifier for the user or account.
- `profile_id` (string, nullable)  
  Profile within a multi-profile account.
- `content_id` (string)  
  Identifier of the content (movie/show/episode).
- `event_type` (string)  
  Type of player event, e.g. `play`, `pause`, `stop`, `seek`.
- `event_ts` (bigint)  
  Event timestamp in epoch seconds (source for `event_date`).
- `device_type` (string)  
  Device or platform generating the event.
- `country` (string, nullable)  
  User or session country code.
- `raw_payload` (string / JSON, optional)  
  Full raw event payload for debugging or reprocessing.

The raw table is designed to be close to the producer schema and primarily serves as a landing zone.[web:71]

## Processed Events: processed_netflix_events

**Location**

- Database: `netflix-streams-aws`
- Table: `processed_netflix_events`
- S3 prefix: `s3://myshr-netflix-datalake-ap-south-1/netflix/processed_partitioned/`
- Partition column: `event_date`

**Logical schema**

- `user_id` (string)  
- `profile_id` (string)  
- `content_id` (string)  
- `event_type` (string)  
- `event_ts` (bigint) – original epoch value  
- `event_timestamp` (timestamp, optional) – converted from `event_ts`  
- `event_date` (date) – partition key  
- `device_type` (string)  
- `country` (string)  
- Additional derived fields if needed (session identifiers, playback position, etc.).

**Partitioning**

`event_date` is derived from `event_ts` using:

```python
from pyspark.sql.functions import col, from_unixtime, to_date

df = df.withColumn(
    "event_date",
    to_date(from_unixtime(col("event_ts")))
)

Resulting S3 layout:

text
.../processed_partitioned/
  event_date=2026-01-27/
    part-0000-...snappy.parquet
  event_date=2026-01-28/
    part-0000-...snappy.parquet
  __HIVE_DEFAULT_PARTITION__/
    part-0000-...snappy.parquet
Querying Patterns
Partition discovery

sql
SHOW PARTITIONS processed_netflix_events;
Daily volume

sql
SELECT
    event_date,
    COUNT(*) AS total_events
FROM processed_netflix_events
GROUP BY event_date
ORDER BY event_date;
Sample events by date

sql
SELECT *
FROM processed_netflix_events
WHERE event_date = DATE '2026-01-27'
LIMIT 50;
These patterns align with common clickstream analytics use cases where date is the primary filter.