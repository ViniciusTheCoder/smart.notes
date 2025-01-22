import json
import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)  

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_table_name = os.getenv('DYNAMODB_TABLE_NAME')
if not dynamodb_table_name:
    logger.error("Environment variable 'DYNAMODB_TABLE_NAME' is not set.")
    raise ValueError("DynamoDB table name not set in environment variables.")
table = dynamodb.Table(dynamodb_table_name)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    try:
        body = json.loads(event.get('body', '{}'))
        summary_id = body.get('summaryId')
        
        if not summary_id:
            logger.warning("Missing summaryId.")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'summaryId is required'})
            }
        
        logger.info(f"Fetching summary with ID: {summary_id}")
        
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = os.getenv('AWS_BUCKET_NAME')
        key = f"results/{summary_id}.md"
        
        logger.debug(f"S3 key: {key}") 
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        logger.info("Summary obtained.")
        
        document_name = f"audio/{summary_id}.mp3"
        created_at = datetime.utcnow().isoformat()
        
        table.put_item(
            Item={
                'summaryId': summary_id,
                'created_at': created_at,
                'documentName': document_name
            }
        )
        logger.info(f"Record created in DynamoDB: summaryId={summary_id}, created_at={created_at}, documentName={document_name}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'content': content})
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch summary or record in DynamoDB: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to fetch summary or record data'})
        }
