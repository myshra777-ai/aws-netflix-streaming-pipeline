# Architecture Diagram

This file describes the logical architecture diagram for the AWS Netflix Streaming Data Pipeline. You can use it as a reference when creating a visual diagram (e.g., draw.io, Excalidraw, Lucidchart).[web:71][web:74]

## Components

- **Producers**
  - Netflix-style clients or synthetic event generators.

- **Ingestion**
  - Amazon Kinesis Data Firehose delivery stream.

- **Storage**
  - Amazon S3 raw bucket (`netflix/ingest_year=2026/`).
  - Amazon S3 processed bucket (`netflix/processed_partitioned/`).

- **Metadata and Processing**
  - AWS Glue Crawler.
  - AWS Glue Data Catalog.
  - AWS Glue 5.0 ETL Job (`netflix-raw-to-processed`).
  - (Optional) AWS Glue Data Quality.

- **Analytics**
  - Amazon Athena querying `processed_netflix_events`.

## Diagram – Text Description

You can represent the diagram with the following flow:

1. **Left side – Producers**
   - Box: “Event Producers (Players / Synthetic Generator)”
   - Arrow to Kinesis Data Firehose.

2. **Middle – Ingestion & Storage**
   - Box: “Kinesis Data Firehose”
   - Arrow to “S3 – Raw Layer (`netflix/ingest_year=2026/`)”.

3. **Middle – Metadata**
   - From “S3 – Raw Layer” arrow to “Glue Crawler”.
   - From “Glue Crawler” arrow to “Glue Data Catalog (raw_netflix_events_rootevents)”.[web:73]

4. **Processing**
   - Box: “Glue Job – netflix-raw-to-processed (Glue 5.0)”.
   - Input from “Glue Data Catalog – raw table”.
   - Output arrows to:
     - “S3 – Processed Layer (`processed_partitioned/` – partitioned by event_date)”.
     - (Optional) “S3 – DQ Results / Logs”.

5. **Analytics**
   - From “S3 – Processed Layer” arrow to “Glue Data Catalog (processed_netflix_events)”.
   - From “Glue Data Catalog (processed)” arrow to “Amazon Athena”.
   - Users/clients icon reading queries from Athena.

## File Export Guidance

When you draw the diagram:

- Save source file (e.g., `.drawio` or `.excalidraw`) into `docs/` or `docs/overview/`.
- Export a PNG/SVG and reference it from `README.md` or `docs/architecture.md`.

Example reference in markdown:

```markdown

This ensures the architecture is easy to understand at a glance while the detailed behavior is documented in architecture.md and data_model.md.