import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event)

    s3_client = boto3.client('s3')
    polly = boto3.client('polly')
    
    text_content = event['text_content']
    bucket_name = os.environ['bucket_name']
    s3_key = os.environ['s3_key']
    response = polly.synthesize_speech(
        Text=text_content,
        OutputFormat='mp3',
        VoiceId='Joanna'
    )
    
    upload_audio_to_s3(s3_client, s3_key, bucket_name, response)
        
    return {
        'statusCode': 200,
        'body': json.dumps('Voiceover has been successfully generated.')
    }

def upload_audio_to_s3(s3_client, s3_key, bucket_name, response):
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key + "/audio_file",
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        logger.info(f"Audio file successfully uploaded to S3 at s3://{bucket_name}/{s3_key}/")
    except Exception as e:
        logger.error(f"Failed to upload audio to S3: {e}")
