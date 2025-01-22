import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')

TARGET_LAMBDA_FUNCTION_NAME = os.getenv('TARGET_LAMBDA_FUNCTION_NAME')

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        if not TARGET_LAMBDA_FUNCTION_NAME:
            raise ValueError("TARGET_LAMBDA_FUNCTION_NAME is not defined.")

        
        if 'body' in event:
            try:
                payload = json.loads(event['body'])
                logger.info(f"Extracted payload from body: {json.dumps(payload)}")
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from 'body' field.")
                raise ValueError("Invalid JSON in 'body' field.")
        else:
            payload = event
            logger.info(f"Using event as payload: {json.dumps(payload)}")

        if 'summaryId' not in payload:
            raise ValueError("The 'summaryId' field is missing in the payload.")

        response = lambda_client.invoke(
            FunctionName=TARGET_LAMBDA_FUNCTION_NAME,
            InvocationType='Event',  
            Payload=json.dumps(payload).encode('utf-8')
        )
        logger.info(f"Successfully invoked Lambda function '{TARGET_LAMBDA_FUNCTION_NAME}'.")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processing started successfully.'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  
            }
        }
    except Exception as e:
        logger.error(f"Error invoking Lambda function '{TARGET_LAMBDA_FUNCTION_NAME}': {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error.', 'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  
            }
        }
