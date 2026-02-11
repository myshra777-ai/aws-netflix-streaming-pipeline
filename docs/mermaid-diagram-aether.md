flowchart TD
    %% Phase 1: Ingestion
    A[Netflix Raw Events<br/>s3://.../raw/] -->|Trigger| LA[Lambda_A: Registrar]
    LA -->|Register Metadata| DDB[(DynamoDB: BatchMetadataTable)]
    LA -->|SNS Alert| LB[Lambda_B: Auditor]

    %% Phase 2: Audit
    LB -->|6-Min Wait & Verify| DDB
    DDB -->|Validated| G[Glue Job: Raw -> Processed]

    %% Phase 3: Processing
    G -->|Shard Limit 100k| DQ{Data Quality Checks}
    DQ -->|Clean| P[s3://.../analytics/clean/]
    DQ -->|Anomalies| Q[s3://.../quarantine/dlq/]

    %% Phase 4: Accountability
    P --> CLI[AETHER CONTROL CONSOLE]
    CLI -->|CONFIRM| W[Warehouse / Athena / Redshift]
    CLI -->|SKIP| IDLE[IDLE_PENDING_REVIEW]
    CLI -->|REJECT| AL[Critical Alert]

    import json
import boto3
import uuid
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Aether_Batch_Registry')

def lambda_handler(event, context):
    # 1. Generate Unique Aether Batch ID
    batch_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # 2. Extract Metadata (Non-Sensitive)
    # Assuming S3 Trigger, but can be adapted for API
    try:
        source_info = event['Records'][0]['s3']
        bucket_name = source_info['bucket']['name']
        file_key = source_info['object']['key']
        file_size = source_info['object'].get('size', 0)
        
        # 3. IAM Identity Capture (Accountability)
        user_identity = event['Records'][0].get('userIdentity', {}).get('principalId', 'UNKNOWN_ENTITY')
        
        # 4. Create the "Digital Birth Certificate" in DynamoDB
        registry_item = {
            'batch_id': batch_id,
            'timestamp': timestamp,
            'source_path': f"s3://{bucket_name}/{file_key}",
            'file_size_bytes': file_size,
            'owner_iam_arn': user_identity,
            'status': 'REGISTERED_PENDING_AUDIT',
            'confidence_score': 0.0, # Will be updated in Phase 2/3
            'cloud_provider': 'AWS',
            'hive_mind_sync': False
        }
        
        table.put_item(Item=registry_item)
        
        # 5. Hive-Mind Trigger (CloudWatch Logging)
        # We use a structured log format that Aether Backend can scrape
        print(f"AETHER_LOG | ACTION: REGISTRATION | BATCH_ID: {batch_id} | STATUS: SUCCESS | BY: {user_identity}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'aether_batch_id': batch_id, 'message': 'Batch Registered Successfully'})
        }
        
    except Exception as e:
        error_msg = f"AETHER_LOG | ACTION: REGISTRATION | STATUS: FAILED | REASON: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Registration Failed'})
        }