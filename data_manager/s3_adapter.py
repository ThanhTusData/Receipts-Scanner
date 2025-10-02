# data_manager/s3_adapter.py
import os
import boto3
from botocore.client import Config

S3_ENDPOINT = os.getenv("S3_ENDPOINT", None)
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "receipts")

class S3Adapter:
    def __init__(self):
        if S3_ENDPOINT:
            self.s3 = boto3.client(
                "s3",
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                config=Config(signature_version="s3v4"),
            )
        else:
            # default real AWS (no endpoint)
            self.s3 = boto3.client("s3")
        # ensure bucket exists (best-effort)
        try:
            self.s3.head_bucket(Bucket=S3_BUCKET)
        except Exception:
            try:
                self.s3.create_bucket(Bucket=S3_BUCKET)
            except Exception:
                pass

    def upload_file(self, local_path: str, key: str):
        self.s3.upload_file(local_path, S3_BUCKET, key)

    def download_file(self, key: str, target_path: str):
        self.s3.download_file(S3_BUCKET, key, target_path)

    def presigned_url(self, key: str, expires_in=3600):
        return self.s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires_in)
