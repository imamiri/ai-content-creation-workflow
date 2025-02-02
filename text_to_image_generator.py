import json
import os
import boto3
import base64
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event)

    s3_client = boto3.client('s3')
    text_content = event['text_content']
    
    bucket_name = os.environ['bucket_name']
    s3_key = os.environ['s3_key']
    try:
        bedrock_client = boto3.client('bedrock-runtime')

        request_body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": text_content,
            },
            "imageGenerationConfig": {
                "numberOfImages": 5,
                "quality": "standard",  # Options: "standard" or "premium"
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,  # Range: 1.0 (exclusive) to 10.0
            }
        }
        
        response = bedrock_client.invoke_model(
            modelId='amazon.titan-image-generator-v2:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        images = response_body['images']
        
        index = 0
        for image in images:
            image_binary = base64.b64decode(image)
            write_image_to_s3(s3_client, bucket_name, s3_key + '/image_' + str(index) + '.png', image_binary) 
            index += 1 
        
        return {
            'statusCode': 200,
            'text_content': text_content
        }
      
    except Exception as e:
        logger.error(f"Error while invoking Bedrock model: {e}")
        raise e

def write_image_to_s3(s3_client, bucket_name, s3_key, image_binary):
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=image_binary,
            ContentType='image/png'
        )
        logger.info(f"Image successfully uploaded to S3 at s3://{bucket_name}/{s3_key}/")
    except Exception as e:
        logger.error(f"Failed to upload image to S3: {e}")
