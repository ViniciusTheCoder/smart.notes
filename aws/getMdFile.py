import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)  

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
        
        logger.info(f"Buscando resumo com ID: {summary_id}")
        
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = os.getenv('AWS_BUCKET_NAME')
        key = f"results/{summary_id}.md"
        
        logger.debug(f"S3 key: {key}") 
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        logger.info("Summary obtained.")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'content': content})
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch summary: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to fetch summary'})
        }
