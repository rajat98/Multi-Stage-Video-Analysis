# __copyright__   = "Copyright 2024, VISA Lab"
# __license__     = "MIT"
import os

import boto3

AWS_REGION_NAME = "us-east-1"
AWS_ACCESS_KEY_ID =  os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_IN_BUCKET_NAME = "1229565443-input"
S3_STAGE_1_BUCKET_NAME = "1229565443-stage-1"
S3_STAGE_2_BUCKET_NAME = "1229565443-stage-2"
S3_STAGE_3_BUCKET_NAME = "1229565443-stage-3"
S3_OUTPUT_BUCKET_NAME = "1229565443-output"

s3 = boto3.client('s3', region_name=AWS_REGION_NAME,
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def upload_to_s3(s3_bucket, s3_key, local_file_path):
    try:
        s3.upload_file(local_file_path, s3_bucket, s3_key)
        object_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
        print(f"File uploaded to S3: {object_url}")
    except Exception as e:
        object_url = ""
        print(f"Error uploading file: {e}")
    return object_url


def download_from_s3(bucket_name, object_key, destination_path):
    try:
        # Download the video file from S3
        s3.download_file(bucket_name, object_key, destination_path)
        print(f"Video downloaded successfully to {destination_path}")
    except Exception as e:
        print(f"Error downloading video: {e}")


def download_folder_from_s3(bucket_name, folder_name, local_directory):
    try:
        # Download the video file from S3
        # List objects in the folder
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

        # Check if the folder exists in S3
        if 'Contents' not in response:
            print(f"No objects found in folder '{folder_name}'")
            return

        # Create the local directory if it doesn't exist
        if not os.path.exists(local_directory):
            os.makedirs(local_directory)

        # Iterate over the objects in the folder and download each one
        for obj in response['Contents']:
            key = obj['Key']
            local_file_path = os.path.join(local_directory, os.path.basename(key))
            s3.download_file(bucket_name, key, local_file_path)
            print(f"Downloaded '{key}' to '{local_file_path}'")
    except Exception as e:
        print(f"Error downloading folder: {e}")


def save_prediction_to_s3(s3_bucket, s3_key, text):
    s3.put_object(Body=text, Bucket=s3_bucket, Key=s3_key)
    object_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
    print(f"Text saved to S3: {object_url}")


def upload_frames(folder_path, bucket):
    parent_dir = "/".join(folder_path.rsplit('/')[:-1])
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Construct the full path to the file
            file_path = os.path.join(root, file)
            # Remove the common prefix (folder_path) to get the relative key in S3
            s3_key = os.path.relpath(file_path, parent_dir)
            s3_key = s3_key.replace("-", "_")
            upload_to_s3(bucket, s3_key, file_path)


def is_folder_uploded_completeley(s3_input_key):
    return s3_input_key.split("/")[-1] == "output_09.jpg"
