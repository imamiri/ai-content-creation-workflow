import json
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event)
    
    s3 = boto3.client('s3')
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    bucket = event['bucket_name']
    key = event['key']

    s3.download_file(bucket, key, '/tmp/blog_doc.txt')
    
    text_content = extract_text_from_txt('/tmp/blog_doc.txt')

    logger.info(text_content)
    model_id = 'amazon.titan-text-premier-v1:0'

    try:
        request_body = {
            "inputText": f"Summarize the following text: {text_content}",
            "textGenerationConfig": {
                "maxTokenCount": 150,
                "temperature": 0.7,
                "topP": 0.9,
                "stopSequences": []
            }
        }

        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        summarized_text = response_body['results'][0]['outputText']
        logger.info("Summary: " + summarized_text)

        return {
            'statusCode': 200,
            'text_content': summarized_text
        }
    except Exception as e:
        logger.error(f"Error while invoking Bedrock model: {e}")
        raise e
    

def extract_text_from_txt(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text