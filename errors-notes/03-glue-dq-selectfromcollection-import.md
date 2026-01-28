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
Use the recommended pattern:

python
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
Verification
After adding the import, the job no longer failed on the SelectFromCollection line.

dq_results_dyf was created successfully and could be written to S3 or inspected further.

Learning
When working with Glue Data Quality and DynamicFrameCollection, ensure all required helper classes (like SelectFromCollection) are imported.

Copying examples from docs without imports is a common source of runtime errors; always double-check imports.

text


