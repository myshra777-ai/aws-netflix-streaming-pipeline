import json

def lambda_handler(event, context):
    # SNS event has Records list, pick first record
    record = event["Records"][0]
    msg = json.loads(record["Sns"]["Message"])

    job_name = msg.get("job_name")
    run_id = msg.get("run_id")
    invalid_ratio = msg.get("invalid_ratio")
    dlq_path = msg.get("dlq_path")

    print(f"[DQ-ALERT] job={job_name}, run_id={run_id}, ratio={invalid_ratio}, dlq={dlq_path}")

    # TODO: yahan Bedrock call + S3 me suggestions likhenge
    return {"status": "ok"}
