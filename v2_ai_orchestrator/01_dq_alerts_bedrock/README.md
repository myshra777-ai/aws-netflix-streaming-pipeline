Glue DQ job runs → emits results.

EventBridge/SNS triggers lambdas/netflix_bedrock_dq_handler.py.

Lambda calls Bedrock → generates human summary → sends alert (SNS/Slack).