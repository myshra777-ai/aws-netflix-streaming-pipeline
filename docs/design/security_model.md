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

Add a short summary and fix to errors-notes/ and keep runbook_failures.md updated for future reference.[web:69][web:71]

text

***

## 4) `docs/security_model.md`

```markdown
# Security Model

This document describes the security and access control model for the AWS Netflix Streaming Data Pipeline.

## Identity and Access Management (IAM)

### Principals

- **Glue job role**
  - IAM role assumed by the AWS Glue job `netflix-raw-to-processed`.
- **Firehose delivery role**
  - IAM role used by Kinesis Data Firehose to write to S3 and, if required, interact with the Glue Data Catalog.[web:54][web:60]
- **Analytics users**
  - IAM users/roles running Athena queries (e.g., analysts, engineers).

### Permissions

At a high level:

- Glue job role:
  - `s3:GetObject`, `s3:PutObject` on the relevant raw and processed S3 prefixes.
  - `glue:GetTable`, `glue:GetDatabase`, `glue:UpdateTable` on `netflix-streams-aws`.
  - CloudWatch Logs permissions for logging job output.[web:54][web:73]

- Firehose role:
  - `s3:PutObject` on the raw ingest bucket prefix.
  - Optional: `kms:Encrypt` / `kms:Decrypt` if using SSE-KMS.

- Athena / Query role:
  - `athena:*` as needed for querying (or more restricted).
  - `s3:GetObject` and `s3:ListBucket` on processed prefixes and query result bucket.
  - `glue:GetDatabase`, `glue:GetTable` for catalog access.[web:54][web:60]

## Data Protection

- **At rest**
  - S3 buckets can be configured with server-side encryption (SSE-S3 or SSE-KMS).
  - Glue and Athena read/write encrypted data transparently when configured correctly.[web:54]

- **In transit**
  - All communication between services uses TLS by default when accessing AWS APIs and S3.

## Network and Access

- Pipeline components can run in a public or VPC-integrated configuration:
  - Glue jobs can be configured to run inside a VPC for private access to data stores.
  - Athena queries data in S3 over AWS’s internal network when VPC endpoints and appropriate routing are set up.[web:54][web:60]

## Governance and Auditing

- **CloudWatch Logs**
  - Glue job logs, Firehose delivery logs, and CloudWatch metrics are used to monitor success/failure rates and performance.

- **CloudTrail**
  - API activity for Glue, Athena, S3, and IAM is recorded in AWS CloudTrail for auditing and incident investigation.

- **Least privilege**
  - IAM policies are scoped to the specific buckets, prefixes, and databases used by this project (no wide `*` access wherever possible).[web:71][web:74]

This model gives a baseline for secure operation of the pipeline and can be extended with more granular controls (e.g., row/column-level security at the query layer) as needed.
