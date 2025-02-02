import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def milliseconds_to_timecode(milliseconds):
    """Convert milliseconds to timecode format HH:MM:SS:FF"""
    seconds = milliseconds // 1000
    frames = (milliseconds % 1000) // 40  # Assuming 25fps, each frame is 40ms
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

def get_mediaconvert_endpoint(region):
    mediaconvert_client = boto3.client('mediaconvert', region)
    response = mediaconvert_client.describe_endpoints()
    return response['Endpoints'][0]['Url']

def list_images_in_s3(s3_client, bucket, prefix):
    try:
        logger.info(f"Searching for images in s3://{bucket}/{prefix}")
        
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            logger.error(f"No objects found in s3://{bucket}/{prefix}")
            return []
        
        images = []
        for obj in response['Contents']:
            if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(obj['Key'])
                logger.info(f"Added image: {obj['Key']}")
        
        return sorted(images)
        
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        raise

def create_video(bucket_name, output_key, media_convert_role):
    region_name='us-east-1'
    try:
        endpoint_url = get_mediaconvert_endpoint(region_name)
        mediaconvert = boto3.client('mediaconvert', endpoint_url=endpoint_url, region_name= region_name)
        s3_client = boto3.client('s3')
        
        # List images
        images_prefix = f"images/"
        
        images = list_images_in_s3(s3_client, bucket_name, images_prefix)
        if not images:
            raise ValueError(f"No images found in s3://{bucket_name}/{images_prefix}")
        
        # Video dimensions
        video_width = 1920
        video_height = 1080

        # Create insertable images array
        insertable_images = []
        current_time = 0
        duration = 5000  # 5 seconds per image in milliseconds
        
        for image_key in images:
            logger.info(f"Adding image {image_key} to job")
            insertable_images.append({
                "ImageX": 0,
                "ImageY": 0,
                "Layer": 1,
                "ImageInserterInput": f"s3://{bucket_name}/{image_key}",
                "StartTime": milliseconds_to_timecode(current_time),  # Convert to timecode
                "Duration": duration,
                "Opacity": 100,  # Add opacity (0-100)
                "Width": video_width,
                "Height": video_height 
            })
            current_time += duration
            logger.info(f"Added image to job: {image_key} at time {milliseconds_to_timecode(current_time)}")
        
        # Job settings
        job_settings = {
            "TimecodeConfig": {"Source": "ZEROBASED"},
            "Inputs": [{
                "ImageInserter": {
                    "InsertableImages": insertable_images,
                    "SdrReferenceWhiteLevel": 100  # Add SDR white level
                },
                "AudioSelectors": {
                    "Audio Selector 1": {
                        "DefaultSelection": "DEFAULT"
                    }
                },
                "FileInput": f"s3://{bucket_name}/audios/audio.mp3",
                "VideoSelector": {  # Add video selector settings
                    "ColorSpace": "FOLLOW",
                    "Rotate": "AUTO"
                }
            }],
            "OutputGroups": [{
                "Name": "File Group",
                "OutputGroupSettings": {
                    "Type": "FILE_GROUP_SETTINGS",
                    "FileGroupSettings": {
                        "Destination": f"s3://{bucket_name}/{output_key}/final_video"
                    }
                },
                "Outputs": [{
                    "VideoDescription": {
                        "ScalingBehavior": "DEFAULT",  # Add scaling behavior
                        "TimecodeInsertion": "DISABLED",
                        "AntiAlias": "ENABLED",
                        "Sharpness": 50,
                        "CodecSettings": {
                            "Codec": "H_264",
                            "H264Settings": {
                                "MaxBitrate": 5000000,
                                "RateControlMode": "QVBR",
                                "QvbrSettings": {
                                    "QvbrQualityLevel": 7
                                },
                                "FramerateControl": "SPECIFIED",
                                "FramerateNumerator": 30,
                                "FramerateDenominator": 1,
                                "GopSize": 60,  # Add GOP size
                                "GopSizeUnits": "FRAMES",
                                "ParControl": "SPECIFIED",  # Add PAR control
                                "ParNumerator": 1,
                                "ParDenominator": 1
                            }
                        },
                        "Width": video_width,
                        "Height": video_height,
                    },
                    "AudioDescriptions": [{
                        "CodecSettings": {
                            "Codec": "AAC",
                            "AacSettings": {
                                "Bitrate": 96000,
                                "CodingMode": "CODING_MODE_2_0",
                                "SampleRate": 48000
                            }
                        }
                    }],
                    "ContainerSettings": {
                        "Container": "MP4",
                        "Mp4Settings": {
                            "CslgAtom": "INCLUDE",
                            "FreeSpaceBox": "EXCLUDE",
                            "MoovPlacement": "PROGRESSIVE_DOWNLOAD"
                        }
                    }
                }]
            }]
        }

        # Create the job
        logger.info("Creating MediaConvert job")
        response = mediaconvert.create_job(
            Role=media_convert_role,
            Settings=job_settings
        )
        
        job_id = response['Job']['Id']
        logger.info(f"MediaConvert job created with ID: {job_id}")
        return job_id

    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise

def lambda_handler(event, context):
    try:
        logger.info(f"Input event: {json.dumps(event)}")
        
        bucket_name = os.environ['bucket_name']
        media_convert_role = os.environ['MEDIA_CONVERT_ROLE']
        output_key = os.environ['s3_key']
        
        if not all([bucket_name]):
            raise ValueError("Missing required parameters")
            
        logger.info(f"Processing request for input: s3://{bucket_name}/images")
        logger.info(f"Output will be saved to: s3://{bucket_name}/{output_key}")

        job_id = create_video(
            bucket_name,
            output_key,
            media_convert_role
        )
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'Video processing started',
                'jobId': job_id,
                'inputLocation': f"s3://{bucket_name}/images",
                'outputLocation': f"s3://{bucket_name}/{output_key}/final_video.mp4"
            }
        }
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return {
            'statusCode': 400,
            'body': {
                'error': str(ve)
            }
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
