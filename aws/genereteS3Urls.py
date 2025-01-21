import json
import boto3
import uuid
import os

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        if not file_name or not file_type:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'fileName and fileType are mandatory.'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        summary_id = str(uuid.uuid4())
        
        object_key = f"uploads/{summary_id}/{file_name}"
        
        s3_client = boto3.client('s3')
        bucket_name = os.environ['BUCKET_NAME']  
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': file_type,
                'ACL': 'private'
            },
            ExpiresIn=300  
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'uploadURL': presigned_url,
                'summaryId': summary_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error.'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
