# Test Plan – Netflix Streaming Pipeline

## Overview

This document captures the key test cases and edge scenarios for the Netflix-style batch pipeline:

- Ingestion → Raw (S3)
- Raw → Processed (Glue: `netflix-raw-to-processed`)
- Processed → Warehouse (Glue: `netflix-processed-to-redshift`)
- Orchestration (Step Functions: `netflix-orchestrator-dev-ai-recovery`)
- Failure handling (HandleFailure Lambda + DLQ S3 records)

Each test case records setup, execution steps, and expected vs actual outcomes.

---

## Legend

- **Result**: `PASS` / `FAIL` / `TODO`
- **Stage**:
  - `validation`
  - `raw-to-processed`
  - `processed-to-redshift`
  - `orchestrator`
- **Category**:
  - `HAPPY_PATH`
  - `DQ_GUARDRAIL`
  - `SCHEMA_MISMATCH`
  - `INFRA_ERROR`
  - `DATA_QUALITY`
  - `AI_INTEGRATION` (future)

---

## Summary Table

| ID  | Name                              | Stage                  | Category        | Result | Notes                |
|-----|-----------------------------------|------------------------|-----------------|--------|----------------------|
| TC1 | Happy path – full batch success   | end-to-end            | HAPPY_PATH      | TODO   |                      |
| TC2 | DQ guardrail – ColumnCount zero   | processed-to-redshift | DQ_GUARDRAIL    | TODO   |                      |
| TC3 | Schema drift – column removed     | raw-to-processed      | SCHEMA_MISMATCH | TODO   |                      |
| TC4 | Schema drift – extra column       | raw-to-processed      | SCHEMA_MISMATCH | TODO   |                      |
| TC5 | Data type drift                   | raw-to-processed      | SCHEMA_MISMATCH | TODO   |                      |
| TC6 | Empty dataset (no files)          | processed-to-redshift | DQ_GUARDRAIL    | TODO   |                      |
| TC7 | Corrupt JSON / bad format         | raw-to-processed      | DATA_QUALITY    | TODO   |                      |
| TC8 | Unexpected event_type             | raw-to-processed      | DATA_QUALITY    | TODO   |                      |
| TC9 | Glue infra error (bad JobName)    | orchestrator          | INFRA_ERROR     | TODO   |                      |
| TC10| Validation Lambda failure         | validation            | INFRA_ERROR     | TODO   |                      |
| TC11| HandleFailure Lambda error        | orchestrator          | INFRA_ERROR     | TODO   |                      |
| TC12| Mixed batch – some bad records    | raw-to-processed      | DATA_QUALITY    | TODO   | Decide policy        |

---

## Detailed Test Cases

### TC1 – Happy path: full batch success

**Stage**: end-to-end  
**Category**: HAPPY_PATH  

**Goal**  
Verify that a valid batch runs through the entire pipeline successfully, writing to warehouse and not touching DLQ.

**Setup**  
- Place N valid events into:  
  `s3://myshr-netflix-datalake-ap-south-1/raw/events/...`  

**Execution steps**  
1. Trigger Step Functions `netflix-orchestrator-dev-ai-recovery` with normal input.  
2. Wait for execution to complete.  
3. Check Glue job runs (both SUCCEEDED).  
4. Check S3 warehouse prefix `warehouse/netflix_events/` for new Parquet files.  
5. Run `SELECT * FROM netflix_events LIMIT 10` via Athena/Redshift.

**Expected result**  
- State machine path: `ValidateInput` → `RunRawToProcessed` → `RunProcessedToRedshift` → `SuccessState`.  
- No DLQ objects created for this time window.  
- Schema and sample records correct.

**Actual result**  
- Result:  
- Notes:

---

### TC2 – DQ guardrail: ColumnCount == 0 (current test)

**Stage**: processed-to-redshift  
**Category**: DQ_GUARDRAIL  

**Goal**  
Confirm that when processed dataset is effectively empty / ColumnCount zero, warehouse job fails and DLQ record is written.

**Setup**  
- Configure `netflix-processed-to-redshift` such that it reads from an empty/invalid processed path OR manipulates logic to force ColumnCount==0.

**Execution steps**  
1. Trigger state machine.  
2. Observe `RunProcessedToRedshift` fails with custom DQ exception.  
3. Confirm `HandleFailure` invoked and returns `status: dlq_written`.  
4. Inspect DLQ record at the key returned in `dlq_s3_key`.

**Expected result**  
- Glue job state: `FAILED` with `DQ_FAILURE: ColumnCount == 0...`.  
- Step Functions path: Catch → HandleFailure → End.  
- DLQ JSON contains:
  - `pipeline_stage: "processed-to-redshift"`  
  - `failure_category: "DQ_GUARDRAIL"`  
  - `dq_failure_type: "COLUMN_COUNT_ZERO"`  
  - `error_message` with DQ_FAILURE text.  
  - `bedrock_analysis.request` populated; `response` null (until AI added).

**Actual result**  
- Result: `PASS` (from latest run).  
- Notes: JobRunId currently null; can enrich later.

---

### TC3 – Schema drift: required column removed

**Stage**: raw-to-processed  
**Category**: SCHEMA_MISMATCH  

**Goal**  
Verify pipeline behaviour when a mandatory column (e.g. `user_id`) is missing from input.

**Setup**  
- Generate sample events missing `user_id`.  
- Place into raw/events path for a test partition.

**Execution steps**  
1. Trigger state machine.  
2. Observe `netflix-raw-to-processed` behaviour (Spark/Glue error or DQ failure).  
3. Follow downstream effects (second job should not corrupt warehouse).  
4. Inspect DLQ entry.

**Expected result**  
- Either raw job fails, or second job fails due to DQ/schema mismatch.  
- DLQ record:
  - `failure_category: "SCHEMA_MISMATCH"`  
  - `dq_failure_type` like `"REQUIRED_COLUMN_MISSING"` (if implemented)  
  - Clear error_message with context.

**Actual result**  
- Result:  
- Notes:

---

### TC4 – Schema drift: extra column added

**Stage**: raw-to-processed  
**Category**: SCHEMA_MISMATCH  

**Goal**  
Check whether adding an extra non-breaking column is tolerated or flagged, and ensure it does not silently break downstream.

**Setup**  
- Add extra column e.g. `"client_version": "1.0.0"` to raw events.  

**Execution steps**  
1. Trigger state machine.  
2. Monitor Glue jobs and DLQ.

**Expected result**  
- Ideally pipeline continues (backward compatible) and column can be ignored or passed through.  
- If failure occurs, DLQ clearly indicates schema drift.

**Actual result**  
- Result:  
- Notes:

---

### TC5 – Data type drift

**Stage**: raw-to-processed  
**Category**: SCHEMA_MISMATCH  

**Goal**  
When a numeric field receives non-numeric values, verify job failure and DLQ logging.

**Setup**  
- Set `duration = "abc"` for some records.

**Execution steps**  
1. Trigger pipeline.  
2. Observe Glue cast/type error.  
3. Inspect DLQ.

**Expected result**  
- Glue job fails with type cast error.  
- DLQ `failure_category: "SCHEMA_MISMATCH"` and clear error_message.

**Actual result**  
- Result:  
- Notes:

---

### TC6 – Empty dataset (no files)

**Stage**: processed-to-redshift  
**Category**: DQ_GUARDRAIL  

**Goal**  
Confirm behaviour when there are no processed files for the given run.

**Setup**  
- Point warehouse job to a path with no files for the current batch.

**Execution steps**  
1. Trigger pipeline.  
2. See DQ or job failure.  
3. Inspect DLQ.

**Expected result**  
- Warehouse job fails; no Parquet written.  
- DLQ indicates empty dataset / ColumnCount zero.

**Actual result**  
- Result:  
- Notes:

---

### TC7 – Corrupt JSON / bad format

**Stage**: raw-to-processed  
**Category**: DATA_QUALITY  

**Goal**  
Ensure corrupt files cause controlled failure and generate DLQ entry.

**Setup**  
- Add one deliberately corrupted JSON file under raw/events.

**Execution steps**  
1. Trigger pipeline.  
2. Observe Glue read error.  
3. Inspect DLQ for parse error.

**Expected result**  
- Job fails with parse exception.  
- DLQ `failure_category: "DATA_QUALITY"` and specific error.

**Actual result**  
- Result:  
- Notes:

---

### TC8 – Unexpected event_type

**Stage**: raw-to-processed  
**Category**: DATA_QUALITY  

**Goal**  
Test handling for unknown event_type values.

**Setup**  
- Create events with `event_type = "UNKNOWN_EVENT"`.

**Execution steps**  
1. Trigger pipeline.  
2. Observe if they are filtered, mapped to “other”, or cause failure.

**Expected result**  
- Behaviour documented and consistent (either safe ignore or DQ flag).  
- If failure: DLQ record with cause.

**Actual result**  
- Result:  
- Notes:

---

### TC9 – Glue infra error (bad JobName)

**Stage**: orchestrator  
**Category**: INFRA_ERROR  

**Goal**  
Validate recovery when Glue job cannot be started for infra reasons.

**Setup**  
- Temporarily misconfigure JobName in state machine for processed job (or use a test state machine).

**Execution steps**  
1. Trigger pipeline.  
2. Glue task should fail with resource not found.  
3. HandleFailure should run and write DLQ.

**Expected result**  
- `failure_category: "INFRA_ERROR"`, `failure_source: "GLUE_JOB"`.  
- No partial writes to warehouse.

**Actual result**  
- Result:  
- Notes:

---

### TC10 – Validation Lambda failure

**Stage**: validation  
**Category**: INFRA_ERROR  

**Goal**  
Confirm validation errors get routed to DLQ.

**Setup**  
- Temporarily raise an exception in `validation_lambda` for certain inputs.

**Execution steps**  
1. Trigger pipeline with that input.  
2. Catch branch should call HandleFailure.

**Expected result**  
- DLQ `pipeline_stage: "validation"` with relevant error message.  

**Actual result**  
- Result:  
- Notes:

---

### TC11 – HandleFailure Lambda failure (regression)

**Stage**: orchestrator  
**Category**: INFRA_ERROR  

**Goal**  
Ensure previous issues (ImportModuleError, AccessDenied) stay fixed.

**Setup**  
- Use current configuration, run failure scenario (DQ guardrail).

**Execution steps**  
1. Trigger DQ failure.  
2. Confirm no Lambda runtime errors; DLQ always written.

**Expected result**  
- No ImportModuleError/AccessDenied in logs.  
- DLQ record present.

**Actual result**  
- Result: `PASS` (AccessDenied fixed with S3 IAM).  
- Notes:

---

### TC12 – Mixed batch (good + bad records)

**Stage**: raw-to-processed  
**Category**: DATA_QUALITY  

**Goal**  
Decide and document policy for partially bad batches.

**Setup**  
- Some records valid, some with corrupt/missing fields.

**Execution steps**  
1. Trigger pipeline.  
2. Observe behaviour (fail whole job vs partial success).

**Expected result**  
- Chosen policy documented (e.g. fail whole batch).  
- DLQ record explains decision.

**Actual result**  
- Result:  
- Notes:
