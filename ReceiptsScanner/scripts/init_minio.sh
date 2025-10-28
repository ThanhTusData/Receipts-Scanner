#!/bin/bash
# MinIO initialization script

set -e

echo "Initializing MinIO for Receipt Scanner..."

# Configuration
MINIO_ENDPOINT="${MINIO_ENDPOINT:-localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
BUCKET_NAME="${MINIO_BUCKET_NAME:-receipts}"

# Check if mc (MinIO client) is installed
if ! command -v mc &> /dev/null; then
    echo "MinIO client (mc) not found. Installing..."
    
    # Detect OS
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     
            wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /tmp/mc
            ;;
        Darwin*)    
            wget https://dl.min.io/client/mc/release/darwin-amd64/mc -O /tmp/mc
            ;;
        *)          
            echo "Unsupported OS: ${OS}"
            exit 1
            ;;
    esac
    
    chmod +x /tmp/mc
    sudo mv /tmp/mc /usr/local/bin/
    echo "MinIO client installed successfully"
fi

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
for i in {1..30}; do
    if curl -f http://${MINIO_ENDPOINT}/minio/health/live &> /dev/null; then
        echo "MinIO is ready!"
        break
    fi
    echo "Attempt $i/30: MinIO not ready yet..."
    sleep 2
done

# Configure MinIO client
echo "Configuring MinIO client..."
mc alias set myminio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

# Create bucket if it doesn't exist
echo "Creating bucket: ${BUCKET_NAME}"
mc mb myminio/${BUCKET_NAME} --ignore-existing

# Set bucket policy (download only)
echo "Setting bucket policy..."
cat > /tmp/policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["*"]
      },
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}/*"]
    }
  ]
}
EOF

mc anonymous set-json /tmp/policy.json myminio/${BUCKET_NAME}
rm /tmp/policy.json

# Create folder structure
echo "Creating folder structure..."
mc cp /dev/null myminio/${BUCKET_NAME}/images/.keep
mc cp /dev/null myminio/${BUCKET_NAME}/data/.keep
mc cp /dev/null myminio/${BUCKET_NAME}/backups/.keep

echo "✅ MinIO initialization completed successfully!"
echo ""
echo "MinIO Console: http://${MINIO_ENDPOINT%:*}:9001"
echo "Access Key: ${MINIO_ACCESS_KEY}"
echo "Secret Key: ${MINIO_SECRET_KEY}"
echo "Bucket: ${BUCKET_NAME}"