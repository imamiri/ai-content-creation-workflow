import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    logger.info(event)
    
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    
    key = event['Records'][0]['s3']['object']['key']
    
    step_function_input = {
        "bucket_name": bucket_name,
        "key": key
    }
    
    # Start the Step Function execution
    response = stepfunctions.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:730335386019:stateMachine:Text-To-Video-Workflow',
        input=json.dumps(step_function_input)
    )
    
    logger.info(response)

    return {
        "statusCode": 200,
        "body": json.dumps('Workflow has been successfully started.')
    }
