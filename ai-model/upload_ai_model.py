import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS boto3 clients
s3_client = boto3.client("s3")

# Get AWS Account ID
try:
    account = boto3.client("sts").get_caller_identity()["Account"]
    print(f"[INFO] Retrieved AWS Account ID: {account}")
except ClientError as e:
    print(f"[ERROR] Failed to retrieve AWS Account ID: {e}")
    raise

# Use env-var for bucket or dynamically create the bucket name
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", f"bedrock-custom-models-{account}")
print(f"[INFO] Using S3 bucket: {BUCKET_NAME}")

# Local path where the model will be downloaded
PATH_TO_MODEL = os.path.join(os.path.dirname(__file__), "model")
print(f"[INFO] Uploading files from local path: {PATH_TO_MODEL}")

if not os.path.exists(PATH_TO_MODEL):
    print(f"[ERROR] Path to model does not exist: {PATH_TO_MODEL}")
    raise FileNotFoundError(f"Path to model does not exist: {PATH_TO_MODEL}")

# Multipart upload threshold (in bytes)
MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100 MB
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB

# S3 key prefix
PREFIX = "custom-model"


def upload_file(local_path, bucket_name, s3_key):
    file_size = os.path.getsize(local_path)

    if file_size > MULTIPART_THRESHOLD:
        print(
            f"[INFO] File {s3_key} exceeds {MULTIPART_THRESHOLD} bytes, using multipart upload."
        )
        multipart_upload(local_path, bucket_name, s3_key)
    else:
        try:
            s3_client.upload_file(local_path, bucket_name, s3_key)
            print(f"[SUCCESS] Uploaded: {s3_key}")
        except ClientError as e:
            print(f"[ERROR] Failed to upload {s3_key}: {e}")


def multipart_upload(local_path, bucket_name, s3_key):
    try:
        # Initiate multipart upload
        multipart_upload = s3_client.create_multipart_upload(
            Bucket=bucket_name, Key=s3_key
        )
        upload_id = multipart_upload["UploadId"]
        parts = []
        with open(local_path, "rb") as file:
            part_number = 1
            while True:
                data = file.read(CHUNK_SIZE)
                if not data:
                    break
                print(f"[INFO] Uploading part {part_number} of file {s3_key}...")
                part = s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=data,
                )
                parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                part_number += 1

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            MultipartUpload={"Parts": parts},
            UploadId=upload_id,
        )
        print(f"[SUCCESS] Multipart upload completed for: {s3_key}")
    except ClientError as e:
        print(f"[ERROR] Multipart upload failed for {s3_key}: {e}")
        s3_client.abort_multipart_upload(
            Bucket=bucket_name, Key=s3_key, UploadId=upload_id
        )
        raise


# Iterate through files and upload to S3
for root, dirs, files in os.walk(PATH_TO_MODEL):
    for file in files:
        local_path = os.path.join(root, file)
        s3_key = os.path.join(PREFIX, os.path.relpath(local_path, PATH_TO_MODEL))

        try:
            print(
                f"[INFO] Uploading file: {local_path} to S3 bucket: {BUCKET_NAME} with key: {s3_key}"
            )
            upload_file(local_path, BUCKET_NAME, s3_key)
        except ClientError as e:
            print(f"[ERROR] Failed to upload {s3_key}: {e}")

print("[INFO] Upload process completed.")
