```mermaid
flowchart TD
    A[Netflix Raw Events<br/>s3://.../raw/] --> B[Glue Job<br/>Raw → Processed]
    B --> C[Data Quality Checks<br/>Glue DQ]
    C --> D[Processed Zone<br/>s3://.../processed/]
    D --> E[Warehouse / Athena / Redshift]
